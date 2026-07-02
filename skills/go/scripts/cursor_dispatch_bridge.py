"""
File-based Cursor dispatch bridge for go Worker Contract.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DISPATCH_DIR = ".go/dispatch"
QUEUE_DIR = "queue"
RESULTS_DIR = "results"
PROMPTS_DIR = "prompts"

SENTINEL_PREFIX = "GO_WORKER_DISPATCH_REQUEST"


def is_cursor_environment() -> bool:
    markers = (
        "CURSOR_TRACE_ID",
        "CURSOR_SESSION_ID",
        "CURSOR_AGENT",
        "CURSOR_WORKSPACE",
    )
    return any(os.environ.get(k) for k in markers)


def dispatch_root(project_dir: Path) -> Path:
    return Path(project_dir) / DISPATCH_DIR


def queue_dir(project_dir: Path) -> Path:
    return dispatch_root(project_dir) / QUEUE_DIR


def results_dir(project_dir: Path) -> Path:
    return dispatch_root(project_dir) / RESULTS_DIR


def prompts_dir(project_dir: Path) -> Path:
    return dispatch_root(project_dir) / PROMPTS_DIR


def file_dispatch_enabled() -> bool:
    mode = os.environ.get("LOOPENGINE_CURSOR_DISPATCH", "auto").strip().lower()
    if mode in ("0", "false", "off", "disabled"):
        return False
    if mode in ("file", "1", "true", "on", "enabled"):
        return True
    return is_cursor_environment()


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def enqueue_dispatch(project_dir: Path, packet: dict[str, Any]) -> dict[str, str]:
    """Write packet + request metadata; return paths for host agent."""
    task_id = packet["task_id"]
    root = Path(project_dir)
    q = queue_dir(root)
    r = results_dir(root)
    p = prompts_dir(root)
    q.mkdir(parents=True, exist_ok=True)
    r.mkdir(parents=True, exist_ok=True)
    p.mkdir(parents=True, exist_ok=True)

    packet_path = q / f"{task_id}.packet.json"
    request_path = q / f"{task_id}.request.json"
    result_path = r / f"{task_id}.result.json"
    prompt_path = p / f"{task_id}.md"

    _atomic_write_json(packet_path, packet)
    prompt_path.write_text(build_task_prompt(packet), encoding="utf-8")

    request = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "packet_path": str(packet_path.resolve()),
        "result_path": str(result_path.resolve()),
        "prompt_path": str(prompt_path.resolve()),
        "workspace_root": packet["workspace"]["root"],
    }
    _atomic_write_json(request_path, request)

    return {
        "task_id": task_id,
        "packet_path": str(packet_path.resolve()),
        "request_path": str(request_path.resolve()),
        "result_path": str(result_path.resolve()),
        "prompt_path": str(prompt_path.resolve()),
    }


def build_task_prompt(packet: dict[str, Any]) -> str:
    """Human/agent-readable prompt for Cursor Task subagent."""
    ws = packet["workspace"]["root"]
    lines = [
        "# go Worker Dispatch",
        "",
        f"**Task ID:** `{packet['task_id']}`",
        f"**Type:** `{packet['task_type']}`",
        f"**Goal:** {packet['goal']}",
        "",
        f"## Workspace (mandatory cwd)",
        f"All file operations MUST occur under:",
        f"```",
        f"{ws}",
        f"```",
        "",
    ]
    allowed = packet["workspace"].get("allowed_paths") or []
    if allowed:
        lines.extend([
            "## Allowed paths",
            ", ".join(f"`{p}`" for p in allowed),
            "",
        ])
    handoffs = (packet.get("context") or {}).get("handoffs") or []
    if handoffs:
        lines.append("## Prior handoffs")
        lines.append("```json")
        lines.append(json.dumps(handoffs, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    lines.extend([
        "## Instructions",
        packet["prompt"],
        "",
        "## Output contract",
        "When done, write a WorkerResult JSON file to the path given in the dispatch request.",
        "Minimum fields: contract_version, task_id, status, runtime_meta.profile=cursor.",
        "Include handoff JSON in a ```json block in your summary AND in WorkerResult.handoff.",
        "",
        "Status must be one of: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED, FAILED.",
    ])
    return "\n".join(lines)


def format_sentinel(paths: dict[str, str]) -> str:
    payload = json.dumps(paths, ensure_ascii=False)
    return f"{SENTINEL_PREFIX} {payload}"


def wait_for_result(
    project_dir: Path,
    task_id: str,
    *,
    timeout_sec: float = 600,
    poll_interval_sec: float = 0.5,
) -> dict[str, Any] | None:
    """Poll results file until available or timeout."""
    result_path = results_dir(Path(project_dir)) / f"{task_id}.result.json"
    deadline = time.perf_counter() + timeout_sec
    while time.perf_counter() < deadline:
        if result_path.exists():
            try:
                with open(result_path, encoding="utf-8") as handle:
                    data = json.load(handle)
                if data.get("task_id") == task_id:
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        time.sleep(poll_interval_sec)
    return None


def write_result(project_dir: Path, result: dict[str, Any]) -> Path:
    """Called by hosting Cursor agent after Task subagent completes."""
    task_id = result["task_id"]
    path = results_dir(Path(project_dir)) / f"{task_id}.result.json"
    _atomic_write_json(path, result)

    request_path = queue_dir(Path(project_dir)) / f"{task_id}.request.json"
    if request_path.exists():
        try:
            with open(request_path, encoding="utf-8") as handle:
                req = json.load(handle)
        except (json.JSONDecodeError, OSError):
            req = {"task_id": task_id}
        req["status"] = "completed"
        req["completed_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_write_json(request_path, req)

    return path


def resolve_project_root(packet: dict[str, Any]) -> Path | None:
    ctx = packet.get("context") or {}
    if ctx.get("project_root"):
        return Path(ctx["project_root"])
    ws = packet.get("workspace", {}).get("root")
    if not ws:
        return None
    wt = Path(ws)
    # .go/worktrees/<id> -> project root
    if wt.name and wt.parent.name == "worktrees" and wt.parent.parent.name == ".go":
        return wt.parent.parent.parent
    return wt


def cleanup_dispatch(project_dir: Path, task_id: str) -> None:
    root = Path(project_dir)
    for directory, suffix in (
        (queue_dir(root), ".packet.json"),
        (queue_dir(root), ".request.json"),
        (results_dir(root), ".result.json"),
        (prompts_dir(root), ".md"),
    ):
        path = directory / f"{task_id}{suffix}"
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="go Cursor dispatch bridge CLI")
    sub = parser.add_subparsers(dest="command")

    wr = sub.add_parser("write-result", help="Write WorkerResult JSON to dispatch queue")
    wr.add_argument("--project", required=True, help="Project root directory")
    wr.add_argument("--result-file", required=True, help="Path to WorkerResult JSON file")

    args = parser.parse_args()
    if args.command == "write-result":
        with open(args.result_file, encoding="utf-8") as handle:
            result = json.load(handle)
        out = write_result(Path(args.project), result)
        print(out)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

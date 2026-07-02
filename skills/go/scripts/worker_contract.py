"""
go Worker Contract v1 — packet validation, result builders, handoff parsing.

Single source of truth aligned with:
  - skills/go/references/worker-task-packet.schema.json
  - skills/go/references/worker-result.schema.json
  - skills/go/references/runtime-capabilities.schema.json
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "1.0"

REQUIRED_PACKET_KEYS = frozenset({
    "contract_version",
    "task_id",
    "task_type",
    "goal",
    "prompt",
    "workspace",
    "constraints",
    "runtime",
})

REQUIRED_WORKSPACE_KEYS = frozenset({
    "root",
    "branch",
    "base_branch",
    "allowed_paths",
})

REQUIRED_CONSTRAINT_KEYS = frozenset({
    "must_commit",
    "timeout_sec",
})

REQUIRED_RUNTIME_KEYS = frozenset({"profile"})

VALID_TASK_TYPES = frozenset({"implement", "merge_resolve", "review"})
VALID_PROFILES = frozenset({"cursor", "zcode"})
VALID_STATUSES = frozenset({
    "DONE",
    "DONE_WITH_CONCERNS",
    "NEEDS_CONTEXT",
    "BLOCKED",
    "FAILED",
})

REFERENCES_DIR = Path(__file__).resolve().parents[1] / "references"


class PacketValidationError(ValueError):
    """Raised when WorkerTaskPacket fails contract validation."""


def validate_packet(packet: dict[str, Any]) -> None:
    """Validate packet shape. Raises PacketValidationError on failure."""
    if not isinstance(packet, dict):
        raise PacketValidationError("packet must be a dict")

    missing = REQUIRED_PACKET_KEYS - set(packet.keys())
    if missing:
        raise PacketValidationError(f"missing required fields: {sorted(missing)}")

    if packet.get("contract_version") != CONTRACT_VERSION:
        raise PacketValidationError(
            f"unsupported contract_version: {packet.get('contract_version')}"
        )

    if packet.get("task_type") not in VALID_TASK_TYPES:
        raise PacketValidationError(f"invalid task_type: {packet.get('task_type')}")

    workspace = packet.get("workspace")
    if not isinstance(workspace, dict):
        raise PacketValidationError("workspace must be a dict")
    ws_missing = REQUIRED_WORKSPACE_KEYS - set(workspace.keys())
    if ws_missing:
        raise PacketValidationError(f"workspace missing: {sorted(ws_missing)}")
    if not workspace.get("root"):
        raise PacketValidationError("workspace.root is required")

    constraints = packet.get("constraints")
    if not isinstance(constraints, dict):
        raise PacketValidationError("constraints must be a dict")
    c_missing = REQUIRED_CONSTRAINT_KEYS - set(constraints.keys())
    if c_missing:
        raise PacketValidationError(f"constraints missing: {sorted(c_missing)}")

    runtime = packet.get("runtime")
    if not isinstance(runtime, dict):
        raise PacketValidationError("runtime must be a dict")
    if "profile" not in runtime:
        raise PacketValidationError("runtime.profile is required")
    if runtime.get("profile") not in VALID_PROFILES:
        raise PacketValidationError(f"invalid runtime.profile: {runtime.get('profile')}")


def make_result(
    task_id: str,
    status: str,
    profile: str,
    *,
    commit_sha: str | None = None,
    handoff: dict | None = None,
    verification: dict | None = None,
    execution_mode: str = "sequential",
    duration_ms: int | None = None,
    degraded: bool = False,
    degraded_reason: str | None = None,
    error: str | None = None,
    concerns: list[str] | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")

    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "task_id": task_id,
        "status": status,
        "runtime_meta": {
            "profile": profile,
            "execution_mode": execution_mode,
            "degraded": degraded,
            "degraded_reason": degraded_reason,
        },
    }
    if duration_ms is not None:
        result["runtime_meta"]["duration_ms"] = duration_ms
    if commit_sha is not None:
        result["commit_sha"] = commit_sha
    if handoff is not None:
        result["handoff"] = handoff
    if verification is not None:
        result["verification"] = verification
    if error:
        result["error"] = error
    if concerns:
        result["concerns"] = concerns
    return result


def failed_result(task_id: str, profile: str, error: str, **kwargs) -> dict[str, Any]:
    return make_result(task_id, "FAILED", profile, error=error, **kwargs)


def blocked_result(task_id: str, profile: str, error: str, **kwargs) -> dict[str, Any]:
    return make_result(task_id, "BLOCKED", profile, error=error, **kwargs)


def parse_handoff(stdout: str) -> dict[str, Any]:
    """Parse handoff JSON from worker stdout (multi-strategy)."""
    if not stdout:
        return _empty_handoff("no stdout")

    match = re.search(r"```json\s*(\{.*?\})\s*```", stdout, re.DOTALL)
    if not match:
        match = re.search(r'\{"files_changed".*?\}', stdout, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return _empty_handoff("handoff parse failed")


def _empty_handoff(reason: str) -> dict[str, Any]:
    return {
        "files_changed": [],
        "new_interfaces": [],
        "artifacts": reason,
        "next_task_hint": None,
    }


def normalize_assigned_runtime(task: dict[str, Any], default_profile: str = "zcode") -> dict[str, Any]:
    """Map v4 assigned_tool or v5 assigned_runtime to unified runtime dict."""
    if task.get("assigned_runtime"):
        return dict(task["assigned_runtime"])

    tool = task.get("assigned_tool", default_profile)
    profile = "cursor" if tool == "cursor" else "zcode"
    return {
        "profile": profile,
        "adapter": "subagent",
    }


def build_packet_from_task(
    task: dict[str, Any],
    project_dir: Path,
    worktree_dir: Path,
    prompt: str,
    *,
    runtime_profile: str | None = None,
    handoffs: list[dict] | None = None,
    feature_branch: str | None = None,
    task_type: str = "implement",
) -> dict[str, Any]:
    """Build WorkerTaskPacket from orchestrator task dict."""
    assigned = normalize_assigned_runtime(task, default_profile=runtime_profile or "zcode")
    profile = runtime_profile or assigned.get("profile", "zcode")
    task_id = task["id"]
    branch = f"go-{task_id.lower()}"

    if feature_branch is None:
        try:
            import git_ops
            feature_branch = git_ops.get_current_branch(project_dir)
        except Exception:
            feature_branch = "main"

    return {
        "contract_version": CONTRACT_VERSION,
        "task_id": task_id,
        "task_type": task_type,
        "goal": task.get("name", task_id),
        "prompt": prompt,
        "workspace": {
            "root": str(worktree_dir.resolve()),
            "branch": branch,
            "base_branch": feature_branch,
            "allowed_paths": list(task.get("files") or []),
        },
        "context": {
            "handoffs": handoffs or [],
            "skills": list(task.get("skills") or []),
            "acceptance_criteria": [],
            "project_root": str(Path(project_dir).resolve()),
        },
        "constraints": {
            "must_commit": task_type != "merge_resolve",
            "commit_message_template": f"go-{task_id}: {{name}}",
            "timeout_sec": 600,
            "max_retries": 2,
        },
        "runtime": {
            "profile": profile,
            "subagent_role": assigned.get("subagent_role", "general-purpose"),
            "model_hint": task.get("model_hint", "standard"),
        },
    }


def result_keys_for_parity(result: dict[str, Any]) -> set[str]:
    """Top-level keys used for cross-runtime parity checks (C6)."""
    keys = set(result.keys())
    if "runtime_meta" in result and isinstance(result["runtime_meta"], dict):
        keys.add("runtime_meta")
    return keys


def load_golden_packet(name: str) -> dict[str, Any]:
    path = REFERENCES_DIR / "golden-packets" / name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Timer:
    def __init__(self):
        self._start = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)

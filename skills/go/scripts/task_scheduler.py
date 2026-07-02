"""
go task scheduler v5.0 — Worker Contract execution + DAG concurrency.

Replaces direct zcode_runner.execute_* calls with adapter-based dispatch.
"""
from __future__ import annotations

import concurrent.futures
import os
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import git_ops
import state_manager
import zcode_runner
from worker_adapter import ensure_adapters_loaded, get_adapter
from worker_contract import (
    build_packet_from_task,
    make_result,
    normalize_assigned_runtime,
)

ROUTING_RULES_PATH = Path(__file__).resolve().parents[1] / "routing-rules.yaml"

DONE_STATUSES = frozenset({"DONE", "DONE_WITH_CONCERNS"})


def detect_runtime_profile() -> str:
    """Resolve runtime profile from env or host detection."""
    explicit = os.environ.get("LOOPENGINE_GO_RUNTIME", "").strip().lower()
    if explicit in ("cursor", "zcode"):
        return explicit
    from cursor_dispatch_bridge import is_cursor_environment
    return "cursor" if is_cursor_environment() else "zcode"


def load_routing_config() -> dict[str, Any]:
    if not ROUTING_RULES_PATH.exists():
        return {"worktree": {"max_concurrent": 4}}
    with open(ROUTING_RULES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def max_workers_for(profile: str) -> int:
    config = load_routing_config()
    wt_max = config.get("worktree", {}).get("max_concurrent", 4)
    ensure_adapters_loaded()
    try:
        caps = get_adapter(profile).capabilities()
        return min(wt_max, caps.get("max_parallel_workers", wt_max))
    except KeyError:
        return wt_max


def paths_overlap(tasks: list[dict]) -> bool:
    """Return True if any two tasks share allowed_paths entries."""
    seen: set[str] = set()
    for task in tasks:
        for path in task.get("files") or []:
            if path in seen:
                return True
            seen.add(path)
    return False


def _collect_handoffs(project_dir, task: dict) -> list[dict]:
    summaries = []
    for dep_id in task.get("depends_on", []):
        try:
            dep = state_manager.get_task(project_dir, dep_id)
            if dep.get("handoff"):
                hs = dict(dep["handoff"])
                hs["task_id"] = dep_id
                summaries.append(hs)
        except KeyError:
            pass
    return summaries


def _apply_worker_result(
    project_dir,
    task: dict,
    packet: dict,
    worker_result: dict,
    worktree_dir: Path,
) -> dict[str, Any]:
    """Post-process WorkerResult: commit, verify, update state."""
    task_id = task["id"]
    status = worker_result.get("status")
    profile = worker_result.get("runtime_meta", {}).get("profile", "zcode")

    if status == "FAILED":
        state_manager.update_task(
            project_dir, task_id,
            status=state_manager.TASK_FAILED,
            error=(worker_result.get("error") or "worker failed")[:200],
        )
        return {"status": "failed", "error": worker_result.get("error")}

    if status == "BLOCKED":
        state_manager.update_task(
            project_dir, task_id,
            status=state_manager.TASK_FAILED,
            error=(worker_result.get("error") or "blocked")[:200],
        )
        return {"status": "failed", "error": worker_result.get("error")}

    if status == "NEEDS_CONTEXT":
        state_manager.update_task(
            project_dir, task_id,
            status=state_manager.TASK_PENDING,
            error=(worker_result.get("error") or "needs context")[:200],
        )
        return {"status": "failed", "error": worker_result.get("error")}

    if status not in DONE_STATUSES:
        state_manager.update_task(
            project_dir, task_id,
            status=state_manager.TASK_FAILED,
            error=f"unexpected worker status: {status}",
        )
        return {"status": "failed", "error": f"unexpected status: {status}"}

    must_commit = packet["constraints"].get("must_commit", True)
    commit_sha = worker_result.get("commit_sha")

    if must_commit:
        commit_sha = git_ops.force_commit(
            worktree_dir,
            f"go-{task_id}: {task.get('name', task_id)[:50]}",
        )
    elif packet["task_type"] == "merge_resolve":
        # merge_resolve: worker should have git add'd; complete merge commit at project root
        pass

    unexpected: list[str] = []
    allowed = packet["workspace"].get("allowed_paths") or []
    if allowed and must_commit:
        actual = git_ops.capture_change_snapshot(worktree_dir)
        verification = git_ops.verify_expected_changes(allowed, actual)
        if not verification["passed"]:
            state_manager.update_task(project_dir, task_id, status=state_manager.TASK_FAILED)
            return {
                "status": "failed",
                "error": f"非预期文件被修改: {verification['unexpected']}",
            }
        unexpected = verification.get("unexpected", [])

    handoff = worker_result.get("handoff") or {}
    if commit_sha:
        handoff["git_commit"] = commit_sha

    runtime = normalize_assigned_runtime(task)
    runtime["capabilities_snapshot"] = get_adapter(profile).capabilities()

    state_manager.update_task(
        project_dir, task_id,
        status=state_manager.TASK_COMPLETED,
        handoff=handoff,
        commit_sha=commit_sha,
        assigned_runtime=runtime,
        degraded=worker_result.get("runtime_meta", {}).get("degraded", False),
        degraded_reason=worker_result.get("runtime_meta", {}).get("degraded_reason"),
    )

    return {
        "status": "completed",
        "handoff": handoff,
        "commit_sha": commit_sha,
        "worker_status": status,
        "unexpected_files": unexpected,
    }


def execute_packet_in_worktree(
    project_dir,
    task: dict,
    *,
    tier: str = "L2",
    runtime_profile: str | None = None,
    adapter=None,
    task_type: str = "implement",
    prompt: str | None = None,
) -> dict[str, Any]:
    """Execute one task via Worker Contract in an isolated worktree."""
    ensure_adapters_loaded()
    profile = runtime_profile or detect_runtime_profile()
    assigned = normalize_assigned_runtime(task, default_profile=profile)
    profile = assigned.get("profile", profile)

    if adapter is None:
        adapter = get_adapter(profile)

    handoffs = _collect_handoffs(project_dir, task)
    head_before = git_ops.get_head(project_dir)
    state_manager.update_task(
        project_dir, task["id"],
        status=state_manager.TASK_IN_PROGRESS,
        git_head_before=head_before,
        model=task.get("model"),
        assigned_runtime=assigned,
    )

    try:
        worktree_dir = git_ops.create_worktree(project_dir, task["id"])
    except RuntimeError as exc:
        return {"status": "failed", "error": f"创建 worktree 失败: {exc}"}

    if prompt is None:
        prompt = zcode_runner.build_prompt(task, str(worktree_dir), handoffs)

    try:
        state = state_manager.read_state(project_dir)
        feature_branch = state.get("feature_branch") or git_ops.get_current_branch(project_dir)
    except Exception:
        feature_branch = git_ops.get_current_branch(project_dir)

    packet = build_packet_from_task(
        task,
        Path(project_dir),
        worktree_dir,
        prompt,
        runtime_profile=profile,
        handoffs=handoffs,
        feature_branch=feature_branch,
        task_type=task_type,
    )

    worker_result = adapter.execute(packet)
    return _apply_worker_result(project_dir, task, packet, worker_result, worktree_dir)


def execute_task_in_worktree(project_dir, task, tier="L2", runtime_profile=None, adapter=None):
    """Backward-compatible entry point."""
    return execute_packet_in_worktree(
        project_dir, task, tier=tier, runtime_profile=runtime_profile, adapter=adapter,
    )


def execute_tasks_concurrent(
    project_dir,
    tasks,
    tier="L2",
    max_workers=None,
    runtime_profile=None,
    adapters: dict[str, Any] | None = None,
):
    """
    Concurrent DAG execution via Worker Contract adapters.

    adapters: optional profile -> adapter instance (for tests)
    """
    ensure_adapters_loaded()
    profile = runtime_profile or detect_runtime_profile()
    if max_workers is None:
        max_workers = max_workers_for(profile)

    completed_ids: set[str] = set()
    failed: list[str] = []
    all_results: dict[str, Any] = {}

    while True:
        ready = [
            t for t in tasks
            if t.get("status") == state_manager.TASK_PENDING
            and all(dep in completed_ids for dep in t.get("depends_on", []))
        ]

        if not ready:
            pending = [t for t in tasks if t.get("status") == state_manager.TASK_PENDING]
            if pending:
                print(f"⚠️ 依赖无法满足: {[t['id'] for t in pending]}")
                failed.extend(t["id"] for t in pending)
            break

        # Cap batch by max_workers; split if path overlap would break isolation
        batch = ready[:max_workers]
        if len(batch) > 1 and paths_overlap(batch):
            batch = [ready[0]]

        if len(batch) == 1:
            task = batch[0]
            print(f"  ▶️ {task['id']}: {task.get('name', '')[:40]}")
            task_profile = normalize_assigned_runtime(task, profile).get("profile", profile)
            adapter = (adapters or {}).get(task_profile) or get_adapter(task_profile)
            result = execute_packet_in_worktree(
                project_dir, task, tier=tier, runtime_profile=task_profile, adapter=adapter,
            )
            all_results[task["id"]] = result
            if result.get("status") == "completed":
                completed_ids.add(task["id"])
            else:
                failed.append(task["id"])
        else:
            worker_count = min(len(batch), max_workers)
            print(f"  🚀 并发执行 {len(batch)} 个任务 ({worker_count} workers)")

            def _run_one(t):
                tp = normalize_assigned_runtime(t, profile).get("profile", profile)
                ad = (adapters or {}).get(tp) or get_adapter(tp)
                return execute_packet_in_worktree(
                    project_dir, t, tier=tier, runtime_profile=tp, adapter=ad,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = {executor.submit(_run_one, t): t["id"] for t in batch}
                for future in concurrent.futures.as_completed(futures):
                    task_id = futures[future]
                    try:
                        result = future.result(timeout=900)
                        all_results[task_id] = result
                        if result.get("status") == "completed":
                            completed_ids.add(task_id)
                            print(f"  ✅ {task_id} 完成")
                        else:
                            failed.append(task_id)
                            print(f"  ❌ {task_id} 失败: {str(result.get('error', ''))[:60]}")
                    except Exception as exc:
                        failed.append(task_id)
                        print(f"  ❌ {task_id} 异常: {str(exc)[:60]}")

    for task in tasks:
        if task["id"] in completed_ids:
            merge_result = _merge_worktree(project_dir, task["id"], runtime_profile=profile, adapters=adapters)
            if not merge_result["ok"] and task["id"] not in failed:
                failed.append(task["id"])

    all_done = len(completed_ids) + len(failed) == len(tasks)
    return {
        "all_completed": all_done and not failed,
        "failed_tasks": failed,
        "completed_count": len(completed_ids),
        "results": all_results,
    }


def _merge_worktree(project_dir, task_id, runtime_profile=None, adapters=None):
    merge_result = git_ops.merge_worktree_to_feature(project_dir, task_id)
    if not merge_result["conflict"]:
        return {"ok": True}

    resolved = _auto_resolve_conflicts(
        project_dir,
        merge_result["conflict_files"],
        runtime_profile=runtime_profile,
        adapters=adapters,
    )
    if not resolved:
        print(f"  ⚠️ {task_id} 合并冲突未解决,需人工处理")
        return {"ok": False}
    return {"ok": True}


def _auto_resolve_conflicts(project_dir, conflict_files, runtime_profile=None, adapters=None):
    if not conflict_files:
        return True

    ensure_adapters_loaded()
    profile = runtime_profile or detect_runtime_profile()
    adapter = (adapters or {}).get(profile) or get_adapter(profile)

    files_info = []
    for f in conflict_files:
        filepath = Path(project_dir) / f
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            files_info.append(f"### {f}\n```\n{content[:3000]}\n```")

    prompt = (
        "当前在 git merge 中,以下文件有冲突:\n\n"
        + "\n\n".join(files_info)
        + "\n\n请解决所有冲突:\n"
        "1. 移除冲突标记\n"
        "2. 整合双方改动\n"
        "3. git add 标记已解决 (不要 commit)"
    )

    packet = {
        "contract_version": "1.0",
        "task_id": f"merge-{Path(project_dir).name}",
        "task_type": "merge_resolve",
        "goal": "Resolve merge conflicts",
        "prompt": prompt,
        "workspace": {
            "root": str(Path(project_dir).resolve()),
            "branch": git_ops.get_current_branch(project_dir),
            "base_branch": git_ops.get_current_branch(project_dir),
            "allowed_paths": list(conflict_files),
        },
        "context": {"handoffs": [], "skills": [], "acceptance_criteria": []},
        "constraints": {"must_commit": False, "timeout_sec": 300, "max_retries": 1},
        "runtime": {"profile": profile, "subagent_role": "general-purpose"},
    }

    result = adapter.execute(packet)
    if result.get("status") not in DONE_STATUSES:
        # Fallback: legacy zcode direct call
        zcode_runner.call_zcode(prompt, project_dir, mode="yolo", timeout=300)

    remaining = git_ops.resolve_conflicts_with_agent(project_dir)
    return len(remaining) == 0


def assigned_runtime_for_task(task: dict | None = None, profile: str | None = None) -> dict[str, Any]:
    """Build assigned_runtime block for new tasks."""
    ensure_adapters_loaded()
    p = profile or detect_runtime_profile()
    if task:
        p = normalize_assigned_runtime(task, p).get("profile", p)
    return {
        "profile": p,
        "adapter": "subagent",
        "capabilities_snapshot": get_adapter(p).capabilities(),
    }

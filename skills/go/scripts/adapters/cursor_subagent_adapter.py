"""Cursor subagent adapter — contract surface; file bridge + BLOCKED outside Cursor."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cursor_dispatch_bridge import (
    enqueue_dispatch,
    file_dispatch_enabled,
    format_sentinel,
    is_cursor_environment,
    resolve_project_root,
    wait_for_result,
)
from worker_adapter import BaseWorkerAdapter, register_adapter
from worker_contract import Timer, blocked_result, make_result


class CursorSubagentAdapter(BaseWorkerAdapter):
    profile = "cursor"

    def __init__(
        self,
        *,
        dispatch_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        force_blocked: bool = False,
        use_file_bridge: bool | None = None,
    ):
        self.dispatch_fn = dispatch_fn
        self.force_blocked = force_blocked
        self.use_file_bridge = use_file_bridge

    def capabilities(self) -> dict[str, Any]:
        return {
            "profile": "cursor",
            "supports_subagent": True,
            "supports_foreground_parallel": True,
            "supports_background_parallel": True,
            "supports_worktree_cwd_binding": True,
            "supports_structured_handoff": True,
            "max_parallel_workers": 4,
        }

    def _file_bridge_enabled(self) -> bool:
        if self.use_file_bridge is not None:
            return self.use_file_bridge
        return file_dispatch_enabled()

    def execute(self, packet: dict[str, Any]) -> dict[str, Any]:
        failed = self._validate_or_fail(packet)
        if failed:
            return failed

        timer = Timer()

        if self.force_blocked or not is_cursor_environment():
            return blocked_result(
                packet["task_id"],
                self.profile,
                "Cursor subagent adapter requires Cursor runtime (CURSOR_* env). "
                "Run go orchestrator from Cursor agent session or use profile=zcode.",
                duration_ms=timer.elapsed_ms(),
            )

        if self.dispatch_fn:
            result = self.dispatch_fn(packet)
            if "runtime_meta" not in result:
                result.setdefault("runtime_meta", {})
            result["runtime_meta"].setdefault("profile", self.profile)
            result["runtime_meta"].setdefault("duration_ms", timer.elapsed_ms())
            return result

        if self._file_bridge_enabled():
            project_root = resolve_project_root(packet)
            if project_root is not None:
                paths = enqueue_dispatch(project_root, packet)
                print(format_sentinel(paths), flush=True)
                default_timeout = float(packet.get("constraints", {}).get("timeout_sec", 600))
                poll_timeout = float(
                    os.environ.get("LOOPENGINE_CURSOR_DISPATCH_POLL_SEC", default_timeout)
                )
                result = wait_for_result(
                    project_root,
                    packet["task_id"],
                    timeout_sec=poll_timeout,
                )
                if result is not None:
                    if "runtime_meta" not in result:
                        result["runtime_meta"] = {}
                    result["runtime_meta"].setdefault("profile", self.profile)
                    result["runtime_meta"]["duration_ms"] = timer.elapsed_ms()
                    return result

                return make_result(
                    packet["task_id"],
                    "NEEDS_CONTEXT",
                    self.profile,
                    error=(
                        "Cursor file dispatch timed out. Host agent: read "
                        f"{paths['prompt_path']}, run Task subagent, write "
                        f"{paths['result_path']}"
                    ),
                    execution_mode="background_parallel",
                    duration_ms=timer.elapsed_ms(),
                )

        return make_result(
            packet["task_id"],
            "NEEDS_CONTEXT",
            self.profile,
            error="Dispatch via Cursor Task tool required; packet validated and ready.",
            execution_mode="background_parallel",
            duration_ms=timer.elapsed_ms(),
        )


register_adapter("cursor", CursorSubagentAdapter)

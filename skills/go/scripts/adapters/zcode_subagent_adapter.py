"""ZCode subagent adapter — contract surface; CLI fallback with degraded flag."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from worker_adapter import BaseWorkerAdapter, register_adapter
from worker_contract import Timer, make_result


class ZCodeSubagentAdapter(BaseWorkerAdapter):
    profile = "zcode"

    def __init__(self, *, use_cli_fallback: bool = True):
        self.use_cli_fallback = use_cli_fallback

    def capabilities(self) -> dict[str, Any]:
        return {
            "profile": "zcode",
            "supports_subagent": True,
            "supports_foreground_parallel": True,
            "supports_background_parallel": False,
            "supports_worktree_cwd_binding": True,
            "supports_structured_handoff": True,
            "max_parallel_workers": 4,
        }

    def execute(self, packet: dict[str, Any]) -> dict[str, Any]:
        import zcode_runner  # lazy: avoid pulling state_manager at import time

        failed = self._validate_or_fail(packet)
        if failed:
            return failed

        timer = Timer()
        workspace = packet["workspace"]["root"]
        timeout = packet["constraints"].get("timeout_sec", 600)
        model = packet.get("runtime", {}).get("model_id")

        degraded = False
        degraded_reason = None

        if self.use_cli_fallback:
            degraded = True
            degraded_reason = "zcode_cli_fallback"

        result = zcode_runner.call_zcode_with_retry(
            packet["prompt"],
            workspace,
            mode="yolo",
            timeout=timeout,
            model=model,
        )

        if not result.get("success"):
            return make_result(
                packet["task_id"],
                "FAILED",
                self.profile,
                error=(result.get("stderr") or "ZCode execution failed")[:200],
                execution_mode="foreground_parallel",
                duration_ms=timer.elapsed_ms(),
                degraded=degraded,
                degraded_reason=degraded_reason,
            )

        stdout = result.get("stdout", "")
        handoff = self._handoff_from_stdout(stdout, None)
        if handoff.get("artifacts") == "handoff parse failed":
            status = "DONE_WITH_CONCERNS"
            concerns = ["handoff JSON not found in worker output"]
        else:
            status = "DONE"
            concerns = None

        return make_result(
            packet["task_id"],
            status,
            self.profile,
            handoff=handoff,
            execution_mode="foreground_parallel",
            duration_ms=timer.elapsed_ms(),
            degraded=degraded,
            degraded_reason=degraded_reason,
            concerns=concerns,
        )


register_adapter("zcode", ZCodeSubagentAdapter)

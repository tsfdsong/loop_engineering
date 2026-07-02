"""Stub adapter for conformance tests and local simulation."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from worker_adapter import BaseWorkerAdapter, register_adapter
from worker_contract import Timer, make_result


class StubWorkerAdapter(BaseWorkerAdapter):
    profile = "stub"

    def __init__(
        self,
        *,
        sleep_sec: float = 0.0,
        simulate_profile: str = "zcode",
        on_execute: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
    ):
        self.sleep_sec = sleep_sec
        self.simulate_profile = simulate_profile
        self.on_execute = on_execute

    def capabilities(self) -> dict[str, Any]:
        return {
            "profile": self.simulate_profile,
            "supports_subagent": True,
            "supports_foreground_parallel": True,
            "supports_background_parallel": self.simulate_profile == "cursor",
            "supports_worktree_cwd_binding": True,
            "supports_structured_handoff": True,
            "max_parallel_workers": 4,
        }

    def execute(self, packet: dict[str, Any]) -> dict[str, Any]:
        failed = self._validate_or_fail(packet)
        if failed:
            return failed

        if self.on_execute:
            custom = self.on_execute(packet)
            if custom is not None:
                return custom

        timer = Timer()
        if self.sleep_sec:
            time.sleep(self.sleep_sec)

        workspace = Path(packet["workspace"]["root"])
        workspace.mkdir(parents=True, exist_ok=True)
        task_type = packet["task_type"]

        if task_type == "merge_resolve":
            for rel in packet["workspace"]["allowed_paths"]:
                path = workspace / rel
                if path.exists():
                    text = path.read_text(encoding="utf-8")
                    text = text.replace("<<<<<<<", "").replace("=======", "").replace(">>>>>>>", "")
                    path.write_text(text, encoding="utf-8")
            return make_result(
                packet["task_id"],
                "DONE",
                self.simulate_profile,
                handoff={"files_changed": packet["workspace"]["allowed_paths"], "artifacts": "conflicts resolved"},
                execution_mode="foreground_parallel",
                duration_ms=timer.elapsed_ms(),
            )

        changed: list[str] = []
        for rel in packet["workspace"]["allowed_paths"] or ["stub-output.txt"]:
            path = workspace / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# stub output for {packet['task_id']}\n", encoding="utf-8")
            changed.append(rel)

        handoff = {
            "files_changed": changed,
            "new_interfaces": [{"type": "table", "name": "points", "columns": ["user_id", "amount"]}],
            "artifacts": f"stub completed {packet['task_id']}",
            "next_task_hint": "T2 can use points table",
        }
        stdout = f"done\n```json\n{__import__('json').dumps(handoff)}\n```"
        handoff = self._handoff_from_stdout(stdout, None)

        return make_result(
            packet["task_id"],
            "DONE",
            self.simulate_profile,
            handoff=handoff,
            execution_mode="foreground_parallel",
            duration_ms=timer.elapsed_ms(),
        )


register_adapter("stub", StubWorkerAdapter)

"""Worker adapter registry and base protocol."""
from __future__ import annotations

from typing import Any, Protocol

from worker_contract import (
    PacketValidationError,
    Timer,
    blocked_result,
    failed_result,
    make_result,
    parse_handoff,
    validate_packet,
)


class WorkerAdapter(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def execute(self, packet: dict[str, Any]) -> dict[str, Any]: ...


_REGISTRY: dict[str, type] = {}


def register_adapter(profile: str, cls: type) -> None:
    _REGISTRY[profile] = cls


def get_adapter(profile: str, **kwargs) -> WorkerAdapter:
    if profile not in _REGISTRY:
        raise KeyError(f"no adapter registered for profile: {profile}")
    return _REGISTRY[profile](**kwargs)


def list_profiles() -> list[str]:
    return sorted(_REGISTRY.keys())


class BaseWorkerAdapter:
    """Shared validation and result helpers."""

    profile: str = "unknown"

    def capabilities(self) -> dict[str, Any]:
        raise NotImplementedError

    def _validate_or_fail(self, packet: dict[str, Any]) -> dict[str, Any] | None:
        try:
            validate_packet(packet)
        except PacketValidationError as exc:
            task_id = packet.get("task_id", "unknown")
            return failed_result(task_id, self.profile, str(exc))
        return None

    def _handoff_from_stdout(self, stdout: str, commit_sha: str | None) -> dict[str, Any]:
        handoff = parse_handoff(stdout)
        if commit_sha:
            handoff["git_commit"] = commit_sha
        return handoff


def ensure_adapters_loaded() -> None:
    """Import adapter modules to populate registry (idempotent)."""
    if _REGISTRY:
        return
    from adapters import cursor_subagent_adapter, stub_adapter, zcode_subagent_adapter  # noqa: F401

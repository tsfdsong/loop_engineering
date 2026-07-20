"""Adapter base types for LoopEngine install."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from loopengine_install.ops import Operation


@dataclass
class AdapterContext:
    home: Path
    repo_root: Path
    central: Path
    version: str
    skill_names: list[str]
    dry_run: bool = False
    mcp_bins: dict[str, str | None] = field(default_factory=dict)


class Adapter(ABC):
    name: str

    @abstractmethod
    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        ...

    @abstractmethod
    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
        ...

    @abstractmethod
    def merge_mcp(self, ctx: AdapterContext) -> list[Operation]:
        ...

    @abstractmethod
    def inject_agents(self, ctx: AdapterContext) -> list[Operation]:
        ...

    def install(self, ctx: AdapterContext) -> list[Operation]:
        ops: list[Operation] = []
        ops.extend(self.sync_plugin(ctx))
        ops.extend(self.activate_registry(ctx))
        ops.extend(self.merge_mcp(ctx))
        ops.extend(self.inject_agents(ctx))
        return ops

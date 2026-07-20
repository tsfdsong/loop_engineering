"""Shared semi-plugin / inject-only adapter helpers."""

from __future__ import annotations

from pathlib import Path

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    copy_tree_op,
    extract_redline_blocks,
    inject_agents_file,
)
from loopengine_install.ops import Operation


class SyncInjectAdapter(Adapter):
    """Tier-2/3: sync central package to plugin_root + optional AGENTS inject."""

    name: str = "base"
    relative_plugin_root: tuple[str, ...] = ()
    agents_relative: tuple[str, ...] | None = None

    def plugin_root(self, ctx: AdapterContext) -> Path:
        return ctx.home.joinpath(*self.relative_plugin_root)

    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        return [
            copy_tree_op(
                f"{self.name}-sync-plugin",
                ctx.central,
                self.plugin_root(ctx),
                ctx.dry_run,
            )
        ]

    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
        return []

    def merge_mcp(self, ctx: AdapterContext) -> list[Operation]:
        return []

    def inject_agents(self, ctx: AdapterContext) -> list[Operation]:
        if not self.agents_relative:
            return []
        agents = ctx.central / "AGENTS.md"
        if not agents.is_file():
            agents = ctx.repo_root / "AGENTS.md"
        markers = ctx.repo_root / "scripts" / "_lib" / "redline_markers.txt"
        blocks = extract_redline_blocks(agents, markers)
        target = ctx.home.joinpath(*self.agents_relative)
        op = inject_agents_file(f"{self.name}-agents", target, blocks, ctx.dry_run)
        return [op] if op else []

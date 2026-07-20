"""Cursor Tier-1 adapter: plugins/local + MCP + rules inject."""

from __future__ import annotations

from pathlib import Path

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    cleanup_flat_skills,
    extract_redline_blocks,
    inject_agents_file,
    link_or_copy_op,
)
from loopengine_install.ops import Operation


class CursorAdapter(Adapter):
    name = "cursor"

    def plugin_root(self, ctx: AdapterContext) -> Path:
        return ctx.home / ".cursor" / "plugins" / "local" / "loopengine"

    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        cleanup_flat_skills(
            ctx.home / ".cursor" / "skills",
            ctx.skill_names,
            ctx.dry_run,
            "cursor",
        )
        dest = self.plugin_root(ctx)
        op = link_or_copy_op(
            "cursor-sync-plugin",
            ctx.central,
            dest,
            ctx.dry_run,
        )
        return [op]

    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
        # local/ discovery — no separate registry file required
        return []

    def merge_mcp(self, ctx: AdapterContext) -> list[Operation]:
        jcode = ctx.mcp_bins.get("jcodemunch") or ""
        repo = ctx.mcp_bins.get("repomix") or ""
        hdrm = ctx.mcp_bins.get("headroom") or ""
        if not jcode and not repo and not hdrm:
            return []
        cfg = ctx.home / ".cursor" / "mcp.json"
        keys: list[str] = []
        if jcode:
            keys.append("jcodemunch")
        if repo:
            keys.append("repomix")
        if hdrm:
            keys.append("headroom")
        if not keys:
            return []

        if not ctx.dry_run:
            cfg.parent.mkdir(parents=True, exist_ok=True)
            if not cfg.exists():
                cfg.write_text("{}\n", encoding="utf-8")
            # merge_cursor requires jcode+repo args; call inline when partial
            from _lib.json_io import atomic_write_json, read_json

            data = read_json(str(cfg))
            servers = data.setdefault("mcpServers", {})
            if jcode:
                servers["jcodemunch"] = {"command": jcode, "args": ["serve"]}
            if repo:
                servers["repomix"] = {"command": repo, "args": ["--mcp"]}
            if hdrm:
                servers["headroom"] = {"command": hdrm, "args": ["mcp", "serve"]}
            else:
                servers.pop("headroom", None)
            atomic_write_json(str(cfg), data)
        return [
            Operation(
                id="cursor-mcp",
                kind="merge-json",
                ownership="managed",
                destination=str(cfg),
                merge_keys=keys,
            )
        ]

    def inject_agents(self, ctx: AdapterContext) -> list[Operation]:
        agents = ctx.central / "AGENTS.md"
        if not agents.is_file():
            agents = ctx.repo_root / "AGENTS.md"
        markers = ctx.repo_root / "scripts" / "_lib" / "redline_markers.txt"
        blocks = extract_redline_blocks(agents, markers)
        target = ctx.home / ".cursor" / "rules" / "loopengine-interaction.mdc"
        op = inject_agents_file("cursor-agents", target, blocks, ctx.dry_run)
        return [op] if op else []

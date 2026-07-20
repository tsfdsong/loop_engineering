"""Cursor Tier-1 adapter: plugins/local + MCP + rules inject."""

from __future__ import annotations

from pathlib import Path

from merge_mcp_config import merge_cursor

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    cleanup_flat_skills,
    extract_redline_blocks,
    inject_agents_file,
    link_or_copy_op,
    merge_json_keys,
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
        if not jcode and not repo:
            return []
        cfg = ctx.home / ".cursor" / "mcp.json"
        keys = ["jcodemunch", "repomix"]
        if hdrm:
            keys.append("headroom")

        def mutator(data):
            # merge_cursor expects path then mutates via read — adapt:
            tmp = dict(data)
            # replicate merge_cursor logic on in-memory dict
            from copy import deepcopy

            # write temp then call merge_cursor by mocking — simpler inline:
            servers = tmp.setdefault("mcpServers", {})
            if jcode:
                servers["jcodemunch"] = {"command": jcode, "args": ["serve"]}
            if repo:
                servers["repomix"] = {"command": repo, "args": ["--mcp"]}
            if hdrm:
                servers["headroom"] = {"command": hdrm, "args": ["mcp", "serve"]}
            else:
                servers.pop("headroom", None)
            return tmp

        # Prefer calling merge_cursor for fidelity when not dry_run
        if not ctx.dry_run and jcode and repo:
            cfg.parent.mkdir(parents=True, exist_ok=True)
            if not cfg.exists():
                cfg.write_text("{}\n", encoding="utf-8")
            data = merge_cursor(str(cfg), jcode, repo, hdrm)
            from _lib.json_io import atomic_write_json

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
        return [
            merge_json_keys("cursor-mcp", cfg, keys, mutator, ctx.dry_run)
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

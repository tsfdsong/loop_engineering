"""ZCode Tier-1 adapter: skills/loopengine + marketplace + enabledPlugins + MCP."""

from __future__ import annotations

from pathlib import Path

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    copy_tree_op,
    extract_redline_blocks,
    inject_agents_file,
    write_registry_json,
)
from loopengine_install.ops import Operation


class ZCodeAdapter(Adapter):
    name = "zcode"

    def plugin_root(self, ctx: AdapterContext) -> Path:
        return ctx.home / ".zcode" / "skills" / "loopengine"

    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        return [
            copy_tree_op(
                "zcode-sync-plugin",
                ctx.central,
                self.plugin_root(ctx),
                ctx.dry_run,
            )
        ]

    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
        cfg = ctx.home / ".zcode" / "cli" / "config.json"
        km = ctx.home / ".zcode" / "cli" / "plugins" / "known_marketplaces.json"
        key = "loopengine@zcode-plugins-official"
        ops: list[Operation] = []

        def mut_enabled(data):
            data = dict(data or {})
            plugins = data.setdefault("plugins", {})
            enabled = plugins.setdefault("enabledPlugins", {})
            enabled[key] = True
            return data

        if cfg.exists() or not ctx.dry_run:
            ops.append(
                write_registry_json(
                    "zcode-enabled-plugins",
                    cfg,
                    key,
                    "zcode.enabledPlugins",
                    mut_enabled,
                    ctx.dry_run,
                )
            )

        def mut_km(data):
            data = dict(data or {})
            mps = data.setdefault("marketplaces", [])
            mid = "zcode-plugins-official"
            if not any(isinstance(x, dict) and x.get("id") == mid for x in mps):
                mps.append(
                    {
                        "id": mid,
                        "source": {
                            "type": "local",
                            "path": str(
                                ctx.home
                                / ".zcode"
                                / "cli"
                                / "plugins"
                                / "cache"
                                / mid
                            ),
                        },
                    }
                )
            return data

        if km.parent.exists() or not ctx.dry_run:
            km.parent.mkdir(parents=True, exist_ok=True)
            ops.append(
                write_registry_json(
                    "zcode-known-marketplaces",
                    km,
                    "zcode-plugins-official",
                    "zcode.known_marketplaces",
                    mut_km,
                    ctx.dry_run,
                )
            )
        return ops

    def merge_mcp(self, ctx: AdapterContext) -> list[Operation]:
        jcode = ctx.mcp_bins.get("jcodemunch") or ""
        repo = ctx.mcp_bins.get("repomix") or ""
        if not jcode and not repo:
            return []
        cfg = ctx.home / ".zcode" / "cli" / "config.json"
        keys: list[str] = []
        if jcode:
            keys.append("jcodemunch")
        if repo:
            keys.append("repomix")
        if not ctx.dry_run:
            cfg.parent.mkdir(parents=True, exist_ok=True)
            if not cfg.exists():
                cfg.write_text("{}\n", encoding="utf-8")
            from _lib.json_io import atomic_write_json, read_json

            data = read_json(str(cfg))
            # ZCode schema: mcp.servers may be dict (preferred) or list
            mcp = data.setdefault("mcp", {})
            servers = mcp.get("servers")
            if not isinstance(servers, dict):
                servers = {}
                mcp["servers"] = servers
            if jcode:
                servers["jcodemunch"] = {
                    "type": "stdio",
                    "command": jcode,
                    "args": ["serve"],
                }
            if repo:
                servers["repomix"] = {
                    "type": "stdio",
                    "command": repo,
                    "args": ["--mcp"],
                }
            atomic_write_json(str(cfg), data)
        return [
            Operation(
                id="zcode-mcp",
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
        target = ctx.home / ".zcode" / "AGENTS.md"
        op = inject_agents_file("zcode-agents", target, blocks, ctx.dry_run)
        return [op] if op else []

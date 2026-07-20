"""Claude Tier-1 adapter: local marketplace + installed_plugins."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    extract_redline_blocks,
    inject_agents_file,
    write_registry_json,
)
from loopengine_install.ops import Operation


class ClaudeAdapter(Adapter):
    name = "claude"

    def _cache_root(self, ctx: AdapterContext) -> Path:
        return (
            ctx.home
            / ".claude"
            / "plugins"
            / "cache"
            / "loopengine-local"
            / "loopengine"
            / ctx.version
        )

    def _marketplace_root(self, ctx: AdapterContext) -> Path:
        return ctx.home / ".claude" / "plugins" / "marketplaces" / "loopengine-local"

    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        cache = self._cache_root(ctx)
        ops: list[Operation] = []
        if not ctx.dry_run:
            if cache.exists():
                shutil.rmtree(cache)
            shutil.copytree(ctx.central, cache)
        ops.append(
            Operation(
                id="claude-sync-cache",
                kind="copy-tree",
                ownership="managed",
                source=str(ctx.central),
                destination=str(cache),
            )
        )
        mp = self._marketplace_root(ctx)
        plugin_dir = mp / "plugins" / "loopengine"
        if not ctx.dry_run:
            if mp.exists():
                shutil.rmtree(mp)
            plugin_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(ctx.central, plugin_dir)
            meta = mp / ".claude-plugin"
            meta.mkdir(parents=True, exist_ok=True)
            (meta / "marketplace.json").write_text(
                "{\n"
                '  "name": "loopengine-local",\n'
                '  "owner": {"name": "LoopEngine"},\n'
                '  "metadata": {"description": "LoopEngine local marketplace", '
                f'"version": "{ctx.version}"}},\n'
                '  "plugins": [{\n'
                '    "name": "loopengine",\n'
                '    "description": "LoopEngine",\n'
                '    "source": "./plugins/loopengine",\n'
                '    "strict": false\n'
                "  }]\n}\n",
                encoding="utf-8",
            )
        ops.append(
            Operation(
                id="claude-sync-marketplace",
                kind="copy-tree",
                ownership="managed",
                source=str(ctx.central),
                destination=str(plugin_dir),
            )
        )
        return ops

    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        install_path = str(self._cache_root(ctx))
        key = "loopengine@loopengine-local"
        km_path = ctx.home / ".claude" / "plugins" / "known_marketplaces.json"
        ip_path = ctx.home / ".claude" / "plugins" / "installed_plugins.json"
        mp_root = str(self._marketplace_root(ctx))

        def mut_km(data):
            data = dict(data or {})
            data["loopengine-local"] = {
                "source": {"source": "directory", "path": mp_root},
                "installLocation": mp_root,
                "lastUpdated": now,
            }
            return data

        def mut_ip(data):
            data = dict(data or {})
            if "version" not in data:
                data["version"] = 2
            plugins = data.setdefault("plugins", {})
            plugins[key] = [
                {
                    "scope": "user",
                    "installPath": install_path,
                    "version": ctx.version,
                    "installedAt": now,
                    "lastUpdated": now,
                }
            ]
            return data

        return [
            write_registry_json(
                "claude-known-marketplaces",
                km_path,
                "loopengine-local",
                "claude.known_marketplaces",
                mut_km,
                ctx.dry_run,
            ),
            write_registry_json(
                "claude-installed-plugins",
                ip_path,
                key,
                "claude.installed_plugins",
                mut_ip,
                ctx.dry_run,
            ),
        ]

    def merge_mcp(self, ctx: AdapterContext) -> list[Operation]:
        return []

    def inject_agents(self, ctx: AdapterContext) -> list[Operation]:
        agents = ctx.central / "AGENTS.md"
        if not agents.is_file():
            agents = ctx.repo_root / "AGENTS.md"
        markers = ctx.repo_root / "scripts" / "_lib" / "redline_markers.txt"
        blocks = extract_redline_blocks(agents, markers)
        target = ctx.home / ".claude" / "CLAUDE.md"
        op = inject_agents_file("claude-agents", target, blocks, ctx.dry_run)
        return [op] if op else []

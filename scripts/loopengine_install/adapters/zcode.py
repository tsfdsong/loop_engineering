"""ZCode Tier-1 adapter: official plugin cache + marketplace + enabledPlugins.

Root cause (2026-07-20): copying only to ~/.zcode/skills/loopengine + flipping
enabledPlugins does NOT make ZCode manage LoopEngine as a plugin. zcode.cjs
scanOfficialCache/loadPlugin requires:
  1) ~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/<ver>/
  2) .zcode-plugin/plugin.json (+ .zcode-plugin-seed.json)
  3) marketplaces/.../marketplace.json plugins[] entry with cachePath
See loopengine_install.adapters.zcode (verified against zcode.cjs 2026-07-14).

Root cause (2026-07-22): enabledPlugins=true alone still shows default-off in UI.
zcode.cjs resolveEnabled = enabledPlugins[id] ?? defaultEnabled, and UI
installedPlugins only lists installed_plugins.json — must register there too.

Root cause (2026-07-22 #2): enabledPlugins=true on disk still lists as disabled when
any provider.options.apiKey is "" / null. zcode.cjs Uz→QWt.parse uses
apiKey: he.string().min(1).optional(); empty string fails the *entire* user
config load, so enabledPlugins is silently discarded (defaultEnabled only).
Sanitize empty apiKey keys on activate so the config stays parseable.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    extract_redline_blocks,
    inject_agents_file,
    write_registry_json,
)
from loopengine_install.ops import Operation

MARKETPLACE_ID = "zcode-plugins-official"
PLUGIN_NAME = "loopengine"


def sanitize_empty_provider_api_keys(data: dict) -> int:
    """Drop empty/null provider options.apiKey so ZCode config parse succeeds.

    Returns the number of apiKey fields removed.
    """
    provider = data.get("provider")
    if not isinstance(provider, dict):
        return 0
    removed = 0
    for entry in provider.values():
        if not isinstance(entry, dict):
            continue
        options = entry.get("options")
        if not isinstance(options, dict) or "apiKey" not in options:
            continue
        api_key = options["apiKey"]
        if api_key is None or (isinstance(api_key, str) and api_key.strip() == ""):
            del options["apiKey"]
            removed += 1
    return removed


class ZCodeAdapter(Adapter):
    name = "zcode"

    def plugin_root(self, ctx: AdapterContext) -> Path:
        return (
            ctx.home
            / ".zcode"
            / "cli"
            / "plugins"
            / "cache"
            / MARKETPLACE_ID
            / PLUGIN_NAME
            / ctx.version
        )

    def _marketplace_json(self, ctx: AdapterContext) -> Path:
        return (
            ctx.home
            / ".zcode"
            / "cli"
            / "plugins"
            / "marketplaces"
            / MARKETPLACE_ID
            / "marketplace.json"
        )

    def _legacy_skills_root(self, ctx: AdapterContext) -> Path:
        return ctx.home / ".zcode" / "skills" / "loopengine"

    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        dest = self.plugin_root(ctx)
        ops: list[Operation] = []

        if not ctx.dry_run:
            self._deploy_cache_payload(ctx.central, dest)
            self._write_seed(dest, ctx.version)
            legacy = self._legacy_skills_root(ctx)
            if legacy.exists():
                if legacy.is_symlink() or legacy.is_file():
                    legacy.unlink()
                else:
                    shutil.rmtree(legacy)

        ops.append(
            Operation(
                id="zcode-sync-cache",
                kind="copy-tree",
                ownership="managed",
                source=str(ctx.central),
                destination=str(dest),
            )
        )

        mp = self._marketplace_json(ctx)
        cache_path = str(dest)

        def mut_mp(data):
            data = dict(data or {})
            if "name" not in data:
                data["name"] = MARKETPLACE_ID
            plugins = data.setdefault("plugins", [])
            entry = {
                "cachePath": cache_path,
                "name": PLUGIN_NAME,
                "source": "filesystem",
                "version": ctx.version,
            }
            existing = next(
                (p for p in plugins if isinstance(p, dict) and p.get("name") == PLUGIN_NAME),
                None,
            )
            if existing is None:
                plugins.append(entry)
            else:
                existing.update(entry)
            return data

        if not ctx.dry_run:
            mp.parent.mkdir(parents=True, exist_ok=True)
            if not mp.is_file():
                mp.write_text(
                    json.dumps({"name": MARKETPLACE_ID, "plugins": []}, indent=2)
                    + "\n",
                    encoding="utf-8",
                )
        ops.append(
            write_registry_json(
                "zcode-marketplace-plugin",
                mp,
                PLUGIN_NAME,
                "zcode.marketplace.plugins",
                mut_mp,
                ctx.dry_run,
            )
        )
        return ops

    def _deploy_cache_payload(self, central: Path, dest: Path) -> None:
        """Full central copy-tree (D13; aligned with Cursor adapter)."""
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(central, dest, symlinks=False)

    def _write_seed(self, dest: Path, version: str) -> None:
        from loopengine_install.zcode_seed import compute_seed_hash

        hash_val, _status = compute_seed_hash(dest)
        seed = {
            "hash": hash_val,
            "marketplace": MARKETPLACE_ID,
            "plugin": PLUGIN_NAME,
            "pluginVersion": version,
            "source": "filesystem",
            "version": 1,
        }
        (dest / ".zcode-plugin-seed.json").write_text(
            json.dumps(seed, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
        from datetime import datetime, timezone

        cfg = ctx.home / ".zcode" / "cli" / "config.json"
        plugins_root = ctx.home / ".zcode" / "cli" / "plugins"
        km = plugins_root / "known_marketplaces.json"
        ip = plugins_root / "installed_plugins.json"
        key = f"{PLUGIN_NAME}@{MARKETPLACE_ID}"
        install_path = str(self.plugin_root(ctx))
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        ops: list[Operation] = []

        def mut_enabled(data):
            data = dict(data or {})
            # Keep config Zod-parseable; otherwise enabledPlugins never loads.
            sanitize_empty_provider_api_keys(data)
            plugins = data.setdefault("plugins", {})
            enabled = plugins.setdefault("enabledPlugins", {})
            enabled[key] = True
            # ZCode may list a plugin in suppressedBuiltins even when
            # enabledPlugins=true; that blocks UI load (observed 2026-07-21).
            suppressed = plugins.get("suppressedBuiltins")
            if isinstance(suppressed, list) and key in suppressed:
                plugins["suppressedBuiltins"] = [x for x in suppressed if x != key]
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

        def mut_installed(data):
            # zcode.cjs: installedPlugins UI uses
            #   enabledPlugins[id] ?? false
            # and only lists records from installed_plugins.json. Cache-only
            # deploy without this file → plugin appears default-off.
            data = dict(data or {})
            data.setdefault("version", 1)
            entry = {
                "id": key,
                "name": PLUGIN_NAME,
                "marketplace": MARKETPLACE_ID,
                "version": ctx.version,
                "installPath": install_path,
                "installedAt": now,
                "updatedAt": now,
                "scope": "user",
                "source": "filesystem",
            }
            plugins = data.get("plugins")
            if isinstance(plugins, dict):
                # dict form also accepted by zcode fEo / Claude-style
                plugins[key] = [
                    {
                        "scope": "user",
                        "installPath": install_path,
                        "version": ctx.version,
                        "installedAt": now,
                        "lastUpdated": now,
                    }
                ]
                data["plugins"] = plugins
                return data
            if not isinstance(plugins, list):
                plugins = []
            idx = next(
                (
                    i
                    for i, p in enumerate(plugins)
                    if isinstance(p, dict) and p.get("id") == key
                ),
                None,
            )
            if idx is None:
                plugins.append(entry)
            else:
                prev = plugins[idx]
                entry["installedAt"] = prev.get("installedAt") or now
                plugins[idx] = {**prev, **entry}
            data["plugins"] = plugins
            return data

        if ip.parent.exists() or not ctx.dry_run:
            ip.parent.mkdir(parents=True, exist_ok=True)
            ops.append(
                write_registry_json(
                    "zcode-installed-plugins",
                    ip,
                    key,
                    "zcode.installed_plugins",
                    mut_installed,
                    ctx.dry_run,
                )
            )

        def mut_km(data):
            data = dict(data or {})
            mps = data.setdefault("marketplaces", [])
            mid = MARKETPLACE_ID
            cache_path = str(
                ctx.home / ".zcode" / "cli" / "plugins" / "cache" / mid
            )
            # Drop stale Claude-style marketplace id under ZCode home — it
            # surfaces a second loopengine@loopengine-local that stays off.
            mps[:] = [
                x
                for x in mps
                if not (isinstance(x, dict) and x.get("id") == "loopengine-local")
            ]
            if not any(isinstance(x, dict) and x.get("id") == mid for x in mps):
                mps.append(
                    {
                        "id": mid,
                        "source": {"source": "local", "path": cache_path},
                        "name": mid,
                    }
                )
            return data

        if km.parent.exists() or not ctx.dry_run:
            km.parent.mkdir(parents=True, exist_ok=True)
            ops.append(
                write_registry_json(
                    "zcode-known-marketplaces",
                    km,
                    MARKETPLACE_ID,
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

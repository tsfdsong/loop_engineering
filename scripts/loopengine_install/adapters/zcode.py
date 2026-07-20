"""ZCode Tier-1 adapter: official plugin cache + marketplace + enabledPlugins.

Root cause (2026-07-20): copying only to ~/.zcode/skills/loopengine + flipping
enabledPlugins does NOT make ZCode manage LoopEngine as a plugin. zcode.cjs
scanOfficialCache/loadPlugin requires:
  1) ~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/<ver>/
  2) .zcode-plugin/plugin.json (+ .zcode-plugin-seed.json)
  3) marketplaces/.../marketplace.json plugins[] entry with cachePath
See scripts/install_zcode_plugin.py (verified against zcode.cjs 2026-07-14).
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

# Match official ZCode plugin payload (install_zcode_plugin.WHITELIST_TOP_LEVEL)
_PAYLOAD_TOP = frozenset(
    {
        ".mcp.json",
        ".zcode-plugin",
        "README.md",
        "commands",
        "dist",
        "hooks",
        "output-styles",
        "package.json",
        "skills",
        "templates",
    }
)


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
            # Remove legacy skills-tree deploy so UI is plugin-managed, not flat
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
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for name in sorted(_PAYLOAD_TOP):
            src = central / name
            if not src.exists():
                continue
            dst = dest / name
            if src.is_dir():
                shutil.copytree(src, dst, symlinks=False)
            else:
                shutil.copy2(src, dst)
        # Ensure .zcode-plugin/plugin.json exists (from central overlay)
        plugin_json = dest / ".zcode-plugin" / "plugin.json"
        if not plugin_json.is_file():
            plugin_json.parent.mkdir(parents=True, exist_ok=True)
            plugin_json.write_text(
                json.dumps(
                    {"name": PLUGIN_NAME, "version": dest.name, "skills": "skills"},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

    def _write_seed(self, dest: Path, version: str) -> None:
        # Prefer install_zcode_plugin hash helper when available
        hash_val = "0" * 64
        try:
            from install_zcode_plugin import compute_seed_hash

            hash_val, _status = compute_seed_hash(dest)
        except Exception:  # noqa: BLE001
            pass
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
        cfg = ctx.home / ".zcode" / "cli" / "config.json"
        km = ctx.home / ".zcode" / "cli" / "plugins" / "known_marketplaces.json"
        key = f"{PLUGIN_NAME}@{MARKETPLACE_ID}"
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
            mid = MARKETPLACE_ID
            cache_path = str(
                ctx.home / ".zcode" / "cli" / "plugins" / "cache" / mid
            )
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

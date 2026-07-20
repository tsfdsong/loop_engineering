"""Cursor Tier-1 adapter: real plugin copy + flat skills for Agent discovery."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    extract_redline_blocks,
    inject_agents_file,
    list_skill_names,
)
from loopengine_install.ops import Operation


class CursorAdapter(Adapter):
    name = "cursor"

    def plugin_root(self, ctx: AdapterContext) -> Path:
        return ctx.home / ".cursor" / "plugins" / "local" / "loopengine"

    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        """Deploy a real directory under plugins/local (never symlink).

        Cursor may refuse to load skill bodies that resolve outside
        ~/.cursor/plugins/ via symlink. Also dual-deploy each skill to
        ~/.cursor/skills/<name>/ so Agent Skills discovery keeps working
        (same path Cursor historically scanned).
        """
        ops: list[Operation] = []
        dest = self.plugin_root(ctx)
        local_root = ctx.home / ".cursor" / "plugins" / "local"

        if not ctx.dry_run:
            local_root.mkdir(parents=True, exist_ok=True)
            # Remove P0 spike and any previous install (symlink or dir)
            spike = local_root / "loopengine-spike"
            if spike.exists():
                if spike.is_symlink() or spike.is_file():
                    spike.unlink()
                else:
                    shutil.rmtree(spike)
            if dest.exists() or dest.is_symlink():
                if dest.is_symlink() or dest.is_file():
                    dest.unlink()
                else:
                    shutil.rmtree(dest)
            shutil.copytree(ctx.central, dest, symlinks=False)
            self._normalize_cursor_plugin(dest, ctx)

        ops.append(
            Operation(
                id="cursor-sync-plugin",
                kind="copy-tree",
                ownership="managed",
                source=str(ctx.central),
                destination=str(dest),
            )
        )

        # Dual-deploy: flat skills for Agent Skills scanner
        flat_root = ctx.home / ".cursor" / "skills"
        skill_names = ctx.skill_names or list_skill_names(ctx.central)
        for i, name in enumerate(skill_names):
            src = ctx.central / "skills" / name
            dst = flat_root / name
            if not src.is_dir():
                continue
            if not ctx.dry_run:
                flat_root.mkdir(parents=True, exist_ok=True)
                if dst.exists() or dst.is_symlink():
                    if dst.is_symlink() or dst.is_file():
                        dst.unlink()
                    else:
                        shutil.rmtree(dst)
                shutil.copytree(src, dst, symlinks=False)
            ops.append(
                Operation(
                    id=f"cursor-flat-skill-{i:03d}-{name}",
                    kind="copy-tree",
                    ownership="managed",
                    source=str(src),
                    destination=str(dst),
                )
            )
        return ops

    def _normalize_cursor_plugin(self, dest: Path, ctx: AdapterContext) -> None:
        """Align with Cursor default discovery: hooks/hooks.json + mcp.json."""
        hooks_dir = dest / "hooks"
        cursor_hooks = hooks_dir / "hooks-cursor.json"
        default_hooks = hooks_dir / "hooks.json"
        if cursor_hooks.is_file():
            shutil.copy2(cursor_hooks, default_hooks)

        # Prefer mcp.json at plugin root (Cursor default discovery)
        plugin_json = dest / ".cursor-plugin" / "plugin.json"
        mcp_path = dest / "mcp.json"
        if plugin_json.is_file():
            data = json.loads(plugin_json.read_text(encoding="utf-8"))
            mcp_servers = data.get("mcpServers")
            if isinstance(mcp_servers, dict):
                mcp_path.write_text(
                    json.dumps({"mcpServers": mcp_servers}, indent=2, ensure_ascii=False)
                    + "\n",
                    encoding="utf-8",
                )
            # Use default folder discovery for skills/commands/hooks
            # (explicit paths are optional; defaults are more reliable)
            for key in ("skills", "commands", "hooks", "mcpServers"):
                data.pop(key, None)
            # Point hooks explicitly to default file if present
            if default_hooks.is_file():
                data["hooks"] = "./hooks/hooks.json"
            if mcp_path.is_file():
                data["mcpServers"] = "./mcp.json"
            plugin_json.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        # Also place rules inside the plugin for plugin-scoped alwaysApply
        rules_src = ctx.home / ".cursor" / "rules" / "loopengine-interaction.mdc"
        # Will be filled after inject_agents; copy from central AGENTS extract later if exists
        rules_dir = dest / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
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

            # Keep plugin mcp.json in sync if plugin dir is a real copy
            plugin_mcp = self.plugin_root(ctx) / "mcp.json"
            if self.plugin_root(ctx).is_dir() and not self.plugin_root(ctx).is_symlink():
                plugin_mcp.write_text(
                    json.dumps({"mcpServers": dict(servers)}, indent=2, ensure_ascii=False)
                    + "\n",
                    encoding="utf-8",
                )
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
        ops = [op] if op else []

        # Mirror rules into the plugin package for plugin-scoped discovery
        if not ctx.dry_run and target.is_file():
            plugin_rules = self.plugin_root(ctx) / "rules" / "loopengine-interaction.mdc"
            plugin_rules.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, plugin_rules)
            # Ensure plugin.json discovers rules/
            plugin_json = self.plugin_root(ctx) / ".cursor-plugin" / "plugin.json"
            if plugin_json.is_file():
                data = json.loads(plugin_json.read_text(encoding="utf-8"))
                data["rules"] = "./rules/"
                plugin_json.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        return ops

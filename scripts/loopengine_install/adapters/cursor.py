"""Cursor Tier-1 adapter: real plugin copy only (no flat LE skills; D3 + D13)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from loopengine_install.adapters.base import Adapter, AdapterContext
from loopengine_install.adapters.helpers import (
    cleanup_flat_skills,
    extract_redline_blocks,
    inject_agents_file,
    list_skill_names,
)
from loopengine_install.ops import Operation

CURSOR_ASK_NOTE_BEGIN = "<!-- BEGIN LOOPENGINE-CURSOR-ASK-NOTE -->"
CURSOR_ASK_NOTE_END = "<!-- END LOOPENGINE-CURSOR-ASK-NOTE -->"
CURSOR_ASK_NOTE = f"""{CURSOR_ASK_NOTE_BEGIN}
## Cursor C2 兑现说明（本平台专用 · 非共享 AGENTS 正文）

本平台通过 MCP `loopengine-ask` 提供工具 **AskUserQuestion**（本地网页点选）。
决策点必须调用该工具。若工具返回 `validation_error` / `browser_error` / `timeout` / `busy`：
**重试工具或上报阻塞**，禁止改用 markdown 列表呈现决策选项继续执行。
{CURSOR_ASK_NOTE_END}
"""


def append_cursor_ask_note(path: Path) -> None:
    """Append Cursor-only C2 note outside managed AGENTS markers (idempotent)."""
    content = path.read_text(encoding="utf-8")
    if CURSOR_ASK_NOTE_BEGIN in content:
        return
    if content and not content.endswith("\n"):
        content += "\n"
    content += "\n" + CURSOR_ASK_NOTE + "\n"
    path.write_text(content, encoding="utf-8")


class CursorAdapter(Adapter):
    name = "cursor"

    def plugin_root(self, ctx: AdapterContext) -> Path:
        return ctx.home / ".cursor" / "plugins" / "local" / "loopengine"

    def sync_plugin(self, ctx: AdapterContext) -> list[Operation]:
        """Deploy a real directory under plugins/local (never symlink).

        D3: skills live only in the plugin package — remove LE flat skills
        under ~/.cursor/skills/. D13: never symlink to the central package.
        """
        ops: list[Operation] = []
        dest = self.plugin_root(ctx)
        local_root = ctx.home / ".cursor" / "plugins" / "local"
        skill_names = ctx.skill_names or list_skill_names(ctx.central)

        # One-way migration: clear LE flat skills (not recorded as reversible ops)
        cleanup_flat_skills(
            ctx.home / ".cursor" / "skills",
            skill_names,
            ctx.dry_run,
            "cursor",
        )

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
        return ops

    def _normalize_cursor_plugin(self, dest: Path, ctx: AdapterContext) -> None:
        """Align with Cursor default discovery: hooks/hooks.json + mcp.json."""
        hooks_dir = dest / "hooks"
        cursor_hooks = hooks_dir / "hooks-cursor.json"
        default_hooks = hooks_dir / "hooks.json"
        if cursor_hooks.is_file():
            shutil.copy2(cursor_hooks, default_hooks)

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
            for key in ("skills", "commands", "hooks", "mcpServers"):
                data.pop(key, None)
            if default_hooks.is_file():
                data["hooks"] = "./hooks/hooks.json"
            if mcp_path.is_file():
                data["mcpServers"] = "./mcp.json"
            plugin_json.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        rules_dir = dest / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

    def activate_registry(self, ctx: AdapterContext) -> list[Operation]:
        return []

    def merge_mcp(self, ctx: AdapterContext) -> list[Operation]:
        jcode = ctx.mcp_bins.get("jcodemunch") or ""
        repo = ctx.mcp_bins.get("repomix") or ""
        hdrm = ctx.mcp_bins.get("headroom") or ""
        cfg = ctx.home / ".cursor" / "mcp.json"
        keys = ["loopengine-ask"]
        if jcode:
            keys.append("jcodemunch")
        if repo:
            keys.append("repomix")
        if hdrm:
            keys.append("headroom")
        central_mcp = ctx.central / "mcp"
        ask_mcp_root = (
            central_mcp
            if (central_mcp / "loopengine_ask").is_dir()
            else self.plugin_root(ctx) / "mcp"
        )

        if not ctx.dry_run:
            cfg.parent.mkdir(parents=True, exist_ok=True)
            if not cfg.exists():
                cfg.write_text("{}\n", encoding="utf-8")
            from _lib.json_io import atomic_write_json, read_json

            data = read_json(str(cfg))
            servers = data.setdefault("mcpServers", {})
            servers["loopengine-ask"] = {
                "command": sys.executable,
                "args": ["-m", "loopengine_ask"],
                "env": {"PYTHONPATH": str(ask_mcp_root.resolve())},
            }
            if jcode:
                servers["jcodemunch"] = {"command": jcode, "args": ["serve"]}
            if repo:
                servers["repomix"] = {"command": repo, "args": ["--mcp"]}
            if hdrm:
                servers["headroom"] = {"command": hdrm, "args": ["mcp", "serve"]}
            else:
                servers.pop("headroom", None)
            atomic_write_json(str(cfg), data)

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

        if not ctx.dry_run and target.is_file():
            append_cursor_ask_note(target)
            plugin_rules = self.plugin_root(ctx) / "rules" / "loopengine-interaction.mdc"
            plugin_rules.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, plugin_rules)
            if plugin_rules.is_file():
                append_cursor_ask_note(plugin_rules)
            plugin_json = self.plugin_root(ctx) / ".cursor-plugin" / "plugin.json"
            if plugin_json.is_file():
                data = json.loads(plugin_json.read_text(encoding="utf-8"))
                data["rules"] = "./rules/"
                plugin_json.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        return ops

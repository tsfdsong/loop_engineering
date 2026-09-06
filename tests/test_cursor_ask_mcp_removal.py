"""Ensure the retired Cursor loopengine-ask MCP is not registered and is scrubbed."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from loopengine_install.adapters.base import AdapterContext
from loopengine_install.adapters.cursor import (
    CURSOR_ASK_NOTE_BEGIN,
    CURSOR_ASK_NOTE_END,
    CursorAdapter,
)
from loopengine_install.package import build_central_package, read_repo_version


class CursorAskMcpRemovalTest(unittest.TestCase):
    def test_cursor_merge_does_not_register_loopengine_ask(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            version = read_repo_version(REPO)
            central = build_central_package(REPO, home / ".loopengine", version)
            ctx = AdapterContext(
                home=home,
                repo_root=REPO,
                central=central,
                version=version,
                skill_names=[],
                mcp_bins={},
            )

            ops = CursorAdapter().merge_mcp(ctx)

            self.assertEqual(ops, [])
            cfg = home / ".cursor" / "mcp.json"
            self.assertFalse(cfg.exists())

    def test_cursor_merge_scrubs_legacy_loopengine_ask(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            version = read_repo_version(REPO)
            central = build_central_package(REPO, home / ".loopengine", version)
            adapter = CursorAdapter()
            plugin = adapter.plugin_root(
                AdapterContext(
                    home=home,
                    repo_root=REPO,
                    central=central,
                    version=version,
                    skill_names=[],
                )
            )
            plugin.mkdir(parents=True)
            cfg = home / ".cursor" / "mcp.json"
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "jcodemunch": {"command": "jcodemunch-mcp", "args": ["serve"]},
                            "loopengine-ask": {
                                "command": "python3",
                                "args": ["-m", "loopengine_ask"],
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            (plugin / "mcp.json").write_text(cfg.read_text(encoding="utf-8"), encoding="utf-8")
            ask_pkg = plugin / "mcp" / "loopengine_ask"
            ask_pkg.mkdir(parents=True)
            (ask_pkg / "__init__.py").write_text("", encoding="utf-8")

            ctx = AdapterContext(
                home=home,
                repo_root=REPO,
                central=central,
                version=version,
                skill_names=[],
                mcp_bins={"jcodemunch": "jcodemunch-mcp"},
            )
            ops = adapter.merge_mcp(ctx)

            data = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertNotIn("loopengine-ask", data["mcpServers"])
            self.assertIn("jcodemunch", data["mcpServers"])
            plugin_data = json.loads((plugin / "mcp.json").read_text(encoding="utf-8"))
            self.assertNotIn("loopengine-ask", plugin_data["mcpServers"])
            self.assertFalse(ask_pkg.exists())
            self.assertEqual(ops[0].merge_keys, ["jcodemunch"])

    def test_plugin_template_has_no_loopengine_ask(self):
        template = json.loads((REPO / ".plugin-template.json").read_text(encoding="utf-8"))
        self.assertNotIn("loopengine-ask", template.get("mcpServers", {}))

    def test_inject_agents_strips_cursor_ask_note(self):
        agents_before = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            version = read_repo_version(REPO)
            central = build_central_package(REPO, home / ".loopengine", version)
            ctx = AdapterContext(
                home=home,
                repo_root=REPO,
                central=central,
                version=version,
                skill_names=[],
                mcp_bins={},
            )
            adapter = CursorAdapter()
            adapter.sync_plugin(ctx)

            note = (
                f"\n{CURSOR_ASK_NOTE_BEGIN}\n"
                "## Cursor C2 兑现说明\n"
                "loopengine-ask\n"
                f"{CURSOR_ASK_NOTE_END}\n"
            )
            user_rules = home / ".cursor" / "rules" / "loopengine-interaction.mdc"
            user_rules.parent.mkdir(parents=True, exist_ok=True)
            user_rules.write_text("# placeholder\n" + note, encoding="utf-8")
            plugin_rules = adapter.plugin_root(ctx) / "rules" / "loopengine-interaction.mdc"
            plugin_rules.parent.mkdir(parents=True, exist_ok=True)
            plugin_rules.write_text("# placeholder\n" + note, encoding="utf-8")

            adapter.inject_agents(ctx)

            for path in (user_rules, plugin_rules):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("LOOPENGINE-CURSOR-ASK-NOTE", text)
                self.assertNotIn("loopengine-ask", text)

            agents_after = (REPO / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(agents_before, agents_after)

    def test_central_package_has_no_loopengine_ask(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            version = read_repo_version(REPO)
            central = build_central_package(REPO, home / ".loopengine", version)
            self.assertFalse((central / "mcp" / "loopengine_ask").exists())


if __name__ == "__main__":
    unittest.main()

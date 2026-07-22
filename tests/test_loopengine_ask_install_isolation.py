"""Ensure loopengine-ask is installed only through the Cursor adapter."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from loopengine_install.adapters.base import AdapterContext
from loopengine_install.adapters.cursor import CursorAdapter
from loopengine_install.package import build_central_package, read_repo_version


class LoopengineAskInstallIsolationTest(unittest.TestCase):
    def test_cursor_merge_registers_loopengine_ask(self):
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

            data = json.loads((home / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
            ask = data["mcpServers"]["loopengine-ask"]
            self.assertEqual(ask["command"], sys.executable)
            self.assertEqual(ask["args"], ["-m", "loopengine_ask"])
            self.assertEqual(ask["env"]["PYTHONPATH"], str((central / "mcp").resolve()))
            self.assertEqual(ops[0].merge_keys, ["loopengine-ask"])

    def test_plugin_template_has_no_loopengine_ask(self):
        template = json.loads((REPO / ".plugin-template.json").read_text(encoding="utf-8"))
        self.assertNotIn("loopengine-ask", template.get("mcpServers", {}))


if __name__ == "__main__":
    unittest.main()

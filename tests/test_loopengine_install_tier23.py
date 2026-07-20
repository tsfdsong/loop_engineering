"""Tier-2/3 adapter smoke tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loopengine_install.adapters import ALL_TOOLS, get_adapters
from loopengine_install.adapters.base import AdapterContext
from loopengine_install.package import build_central_package, read_repo_version


class Tier23Test(unittest.TestCase):
    def test_all_tools_registered(self):
        self.assertEqual(
            set(ALL_TOOLS),
            {"cursor", "claude", "zcode", "codex", "gemini", "copilot", "pi"},
        )

    def test_codex_sync_in_tmp_home(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            le = home / ".loopengine"
            ver = read_repo_version(repo)
            central = build_central_package(repo, le, ver)
            ctx = AdapterContext(
                home=home,
                repo_root=repo,
                central=central,
                version=ver,
                skill_names=["go"],
                dry_run=False,
                mcp_bins={},
            )
            adapter = get_adapters(["codex"])[0]
            ops = adapter.install(ctx)
            root = home / ".codex" / "skills" / "loopengine"
            self.assertTrue((root / "skills").is_dir() or (root / "AGENTS.md").exists() or root.exists())
            self.assertTrue(any(o.kind == "link-or-copy" for o in ops))
            self.assertTrue((home / ".codex" / "AGENTS.md").is_file())


if __name__ == "__main__":
    unittest.main()

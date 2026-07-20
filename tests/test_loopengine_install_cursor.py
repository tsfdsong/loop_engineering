"""Tests for Cursor adapter D3 plugin-only + package prune."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loopengine_install.adapters.base import AdapterContext
from loopengine_install.adapters.cursor import CursorAdapter
from loopengine_install.package import build_central_package, prune_old_versions, read_repo_version


class CursorAdapterTest(unittest.TestCase):
    def test_plugin_only_clears_flat(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            le = home / ".loopengine"
            ver = read_repo_version(repo)
            central = build_central_package(repo, le, ver)
            skill = next(
                p.name
                for p in (central / "skills").iterdir()
                if (p / "SKILL.md").is_file()
            )
            flat = home / ".cursor" / "skills" / skill
            flat.mkdir(parents=True)
            (flat / "SKILL.md").write_text("# leftover\n", encoding="utf-8")

            ctx = AdapterContext(
                home=home,
                repo_root=repo,
                central=central,
                version=ver,
                skill_names=[skill],
                dry_run=False,
                mcp_bins={},
            )
            ops = CursorAdapter().sync_plugin(ctx)
            self.assertTrue(any(o.id == "cursor-sync-plugin" for o in ops))
            self.assertFalse(any("flat" in o.id for o in ops))
            plugin = home / ".cursor" / "plugins" / "local" / "loopengine"
            self.assertTrue(plugin.is_dir())
            self.assertFalse(plugin.is_symlink())
            self.assertTrue((plugin / "skills" / skill / "SKILL.md").is_file())
            self.assertFalse(flat.exists())


class PruneTest(unittest.TestCase):
    def test_prune_old_versions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "plugins" / "loopengine"
            (root / "1.0.0").mkdir(parents=True)
            (root / "1.3.2").mkdir(parents=True)
            (root / "current").write_text("x\n", encoding="utf-8")
            removed = prune_old_versions(Path(td), "1.3.2")
            self.assertEqual(removed, ["1.0.0"])
            self.assertFalse((root / "1.0.0").exists())
            self.assertTrue((root / "1.3.2").is_dir())
            self.assertTrue((root / "current").is_file())


if __name__ == "__main__":
    unittest.main()

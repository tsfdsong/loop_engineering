"""Tests for ZCode official plugin cache deploy (not skills-tree-only)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from loopengine_install.adapters.base import AdapterContext
from loopengine_install.adapters.zcode import ZCodeAdapter
from loopengine_install.package import build_central_package, read_repo_version


class ZCodeAdapterTest(unittest.TestCase):
    def test_deploys_official_cache_and_marketplace(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            le = home / ".loopengine"
            ver = read_repo_version(repo)
            central = build_central_package(repo, le, ver)

            # Simulate legacy skills-tree path that should be removed
            legacy = home / ".zcode" / "skills" / "loopengine"
            legacy.mkdir(parents=True)
            (legacy / "dummy.txt").write_text("x", encoding="utf-8")

            ctx = AdapterContext(
                home=home,
                repo_root=repo,
                central=central,
                version=ver,
                skill_names=["go"],
                dry_run=False,
                mcp_bins={},
            )
            adapter = ZCodeAdapter()
            ops = adapter.sync_plugin(ctx)
            self.assertTrue(any(o.id == "zcode-sync-cache" for o in ops))
            self.assertTrue(any(o.id == "zcode-marketplace-plugin" for o in ops))

            cache = adapter.plugin_root(ctx)
            self.assertTrue(cache.is_dir())
            self.assertFalse(cache.is_symlink())
            self.assertTrue((cache / ".zcode-plugin" / "plugin.json").is_file())
            self.assertTrue((cache / ".zcode-plugin-seed.json").is_file())
            self.assertTrue((cache / "skills" / "go" / "SKILL.md").is_file())
            self.assertFalse(legacy.exists())

            mp = adapter._marketplace_json(ctx)
            data = json.loads(mp.read_text(encoding="utf-8"))
            le_entries = [
                p for p in data.get("plugins", []) if p.get("name") == "loopengine"
            ]
            self.assertEqual(len(le_entries), 1)
            self.assertEqual(le_entries[0]["version"], ver)
            self.assertEqual(le_entries[0]["cachePath"], str(cache))

    def test_activate_clears_suppressed_builtins(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            key = "loopengine@zcode-plugins-official"
            cfg = home / ".zcode" / "cli" / "config.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text(
                json.dumps(
                    {
                        "plugins": {
                            "enabledPlugins": {key: False},
                            "suppressedBuiltins": [key, "other@zcode-plugins-official"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            km = home / ".zcode" / "cli" / "plugins" / "known_marketplaces.json"
            km.parent.mkdir(parents=True)
            km.write_text('{"marketplaces":[]}\n', encoding="utf-8")

            ctx = AdapterContext(
                home=home,
                repo_root=repo,
                central=repo,
                version="9.9.9",
                skill_names=["go"],
                dry_run=False,
                mcp_bins={},
            )
            ZCodeAdapter().activate_registry(ctx)
            data = json.loads(cfg.read_text(encoding="utf-8"))
            plugins = data["plugins"]
            self.assertTrue(plugins["enabledPlugins"][key])
            self.assertNotIn(key, plugins["suppressedBuiltins"])
            self.assertIn(
                "other@zcode-plugins-official", plugins["suppressedBuiltins"]
            )


if __name__ == "__main__":
    unittest.main()

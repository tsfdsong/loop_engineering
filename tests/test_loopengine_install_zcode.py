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

    def test_activate_registers_installed_plugins_enabled_by_default(self):
        """ZCode UI: enabled = enabledPlugins[id] ?? false, and only lists
        installed_plugins.json records as installedPlugins. Missing that
        registration leaves the plugin looking default-off.
        """
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            key = "loopengine@zcode-plugins-official"
            ver = "9.9.9"
            cfg = home / ".zcode" / "cli" / "config.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text("{}", encoding="utf-8")
            plugins_root = home / ".zcode" / "cli" / "plugins"
            plugins_root.mkdir(parents=True)
            km = plugins_root / "known_marketplaces.json"
            km.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "marketplaces": [
                            {
                                "id": "loopengine-local",
                                "name": "loopengine-local",
                                "source": {"source": "local", "path": "/tmp/x"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            ip = plugins_root / "installed_plugins.json"
            ip.write_text(
                json.dumps({"version": 1, "plugins": []}),
                encoding="utf-8",
            )

            ctx = AdapterContext(
                home=home,
                repo_root=repo,
                central=repo,
                version=ver,
                skill_names=["go"],
                dry_run=False,
                mcp_bins={},
            )
            ops = ZCodeAdapter().activate_registry(ctx)
            self.assertTrue(any(o.id == "zcode-installed-plugins" for o in ops))

            enabled = json.loads(cfg.read_text(encoding="utf-8"))["plugins"][
                "enabledPlugins"
            ]
            self.assertTrue(enabled[key])

            installed = json.loads(ip.read_text(encoding="utf-8"))
            records = installed["plugins"]
            self.assertIsInstance(records, list)
            match = [p for p in records if p.get("id") == key]
            self.assertEqual(len(match), 1)
            self.assertEqual(match[0]["name"], "loopengine")
            self.assertEqual(match[0]["marketplace"], "zcode-plugins-official")
            self.assertEqual(match[0]["version"], ver)
            self.assertEqual(match[0]["scope"], "user")
            self.assertTrue(match[0]["installPath"].endswith(f"loopengine/{ver}"))

            km_data = json.loads(km.read_text(encoding="utf-8"))
            self.assertFalse(
                any(
                    isinstance(x, dict) and x.get("id") == "loopengine-local"
                    for x in km_data.get("marketplaces", [])
                )
            )

    def test_activate_strips_empty_provider_api_keys(self):
        """Empty provider apiKey makes ZCode Uz/QWt.parse fail the whole user
        config, which silently drops enabledPlugins (plugin stays disabled).
        """
        from loopengine_install.adapters.zcode import sanitize_empty_provider_api_keys

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            key = "loopengine@zcode-plugins-official"
            cfg = home / ".zcode" / "cli" / "config.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text(
                json.dumps(
                    {
                        "provider": {
                            "builtin:broken": {
                                "name": "Broken",
                                "kind": "anthropic",
                                "options": {"apiKey": "", "baseURL": "https://x"},
                            },
                            "builtin:ok": {
                                "name": "OK",
                                "kind": "anthropic",
                                "options": {
                                    "apiKey": "sk-nonempty",
                                    "baseURL": "https://y",
                                },
                            },
                            "builtin:null-key": {
                                "name": "Null",
                                "kind": "anthropic",
                                "options": {"apiKey": None, "baseURL": "https://z"},
                            },
                        },
                        "plugins": {"enabledPlugins": {key: False}},
                    }
                ),
                encoding="utf-8",
            )
            plugins_root = home / ".zcode" / "cli" / "plugins"
            plugins_root.mkdir(parents=True)
            (plugins_root / "known_marketplaces.json").write_text(
                '{"marketplaces":[]}\n', encoding="utf-8"
            )
            (plugins_root / "installed_plugins.json").write_text(
                '{"version":1,"plugins":[]}\n', encoding="utf-8"
            )

            # Unit: sanitizer alone
            sample = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertEqual(sanitize_empty_provider_api_keys(sample), 2)
            self.assertNotIn(
                "apiKey", sample["provider"]["builtin:broken"]["options"]
            )
            self.assertEqual(
                sample["provider"]["builtin:ok"]["options"]["apiKey"], "sk-nonempty"
            )
            self.assertNotIn(
                "apiKey", sample["provider"]["builtin:null-key"]["options"]
            )

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
            self.assertTrue(data["plugins"]["enabledPlugins"][key])
            self.assertNotIn(
                "apiKey", data["provider"]["builtin:broken"]["options"]
            )
            self.assertEqual(
                data["provider"]["builtin:ok"]["options"]["apiKey"], "sk-nonempty"
            )
            self.assertNotIn(
                "apiKey", data["provider"]["builtin:null-key"]["options"]
            )


if __name__ == "__main__":
    unittest.main()

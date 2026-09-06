"""Tests for hooks/zcode-marketplace-selfheal.sh.

Background (2026-09-06): ZCode CLI periodically rewrites the official
marketplace.json from its remote registry, dropping the locally injected
loopengine entry (observed 39s after install). The SessionStart hook
self-heals it. These tests cover the four behavioral paths.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "hooks" / "zcode-marketplace-selfheal.sh"

VERSION = "1.3.2"


def _make_plugin_root(tmp: Path) -> Path:
    root = tmp / "plugin"
    root.mkdir()
    (root / ".zcode-plugin-seed.json").write_text(
        json.dumps({"pluginVersion": VERSION, "marketplace": "zcode-plugins-official"}),
        encoding="utf-8",
    )
    return root


def _write_marketplace(home: Path, plugins: list, raw: str | None = None) -> Path:
    mp = home / ".zcode" / "cli" / "plugins" / "marketplaces" / "zcode-plugins-official" / "marketplace.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        mp.write_text(raw, encoding="utf-8")
    else:
        mp.write_text(json.dumps({"name": "zcode-plugins-official", "plugins": plugins}, indent=2) + "\n", encoding="utf-8")
    return mp


def _run(plugin_root: Path, home: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin_root), HOME=str(home))
    return subprocess.run(
        ["bash", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=30
    )


class TestZcodeMarketplaceSelfheal(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.plugin_root = _make_plugin_root(self.tmp)
        self.home = self.tmp / "home"
        self.home.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_script_exists_and_executable(self) -> None:
        self.assertTrue(SCRIPT.is_file())
        mode = SCRIPT.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR, "hook script must be executable")

    def test_missing_entry_is_restored(self) -> None:
        mp = _write_marketplace(self.home, [{"name": "browser-use"}])
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(mp.read_text(encoding="utf-8"))
        names = [p["name"] for p in data["plugins"]]
        self.assertIn("loopengine", names)
        self.assertIn("browser-use", names, "official entries must be preserved")
        entry = next(p for p in data["plugins"] if p["name"] == "loopengine")
        self.assertEqual(entry["version"], VERSION)
        self.assertEqual(entry["cachePath"], str(self.plugin_root.resolve()))
        self.assertIn("restored", result.stderr)

    def test_healthy_entry_is_noop(self) -> None:
        entry = {
            "cachePath": str(self.plugin_root.resolve()),
            "name": "loopengine",
            "source": "filesystem",
            "version": VERSION,
        }
        mp = _write_marketplace(self.home, [entry])
        before = mp.read_text(encoding="utf-8")
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mp.read_text(encoding="utf-8"), before, "healthy state must not be rewritten")
        self.assertEqual(result.stderr, "", "no-op must be silent")

    def test_stale_version_is_updated(self) -> None:
        mp = _write_marketplace(
            self.home,
            [{"cachePath": "/old/path", "name": "loopengine", "source": "filesystem", "version": "1.2.0"}],
        )
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0)
        entry = json.loads(mp.read_text(encoding="utf-8"))["plugins"][0]
        self.assertEqual(entry["version"], VERSION)
        self.assertEqual(entry["cachePath"], str(self.plugin_root.resolve()))

    def test_malformed_official_file_is_protected(self) -> None:
        mp = _write_marketplace(self.home, [], raw="{not json")
        before = mp.read_text(encoding="utf-8")
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mp.read_text(encoding="utf-8"), before, "must never overwrite malformed official data")
        self.assertIn("skip", result.stderr)

    def _make_skill_creator(self, versions: list) -> Path:
        """versions 为目录名列表；hook 须选取最高版本目录。"""
        sc = self.home / ".zcode/cli/plugins/cache/zcode-plugins-official/skill-creator"
        for v in versions:
            d = sc / v
            d.mkdir(parents=True, exist_ok=True)
            (d / ".zcode-plugin").mkdir(exist_ok=True)
            (d / ".zcode-plugin" / "plugin.json").write_text(
                json.dumps({"name": "skill-creator", "version": v}), encoding="utf-8")
        return sc

    def test_skill_creator_missing_entry_healed_to_latest(self) -> None:
        self._make_skill_creator(["0.1.0", "0.2.0-anthropic.85cce0381e"])
        mp = _write_marketplace(self.home, [{"name": "github"}])
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(mp.read_text(encoding="utf-8"))
        e = next(p for p in data["plugins"] if p["name"] == "skill-creator")
        self.assertEqual(e["version"], "0.2.0-anthropic.85cce0381e")
        self.assertIn("0.2.0", e["cachePath"])
        self.assertIn("restored", result.stderr)

    def test_skill_creator_stale_entry_updated(self) -> None:
        self._make_skill_creator(["0.1.0", "0.2.0-anthropic.85cce0381e"])
        mp = _write_marketplace(self.home, [{
            "cachePath": "/old/0.1.0", "name": "skill-creator",
            "source": "filesystem", "version": "0.1.0"}])
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0)
        e = json.loads(mp.read_text(encoding="utf-8"))["plugins"][0]
        self.assertEqual(e["version"], "0.2.0-anthropic.85cce0381e")

    def test_all_healthy_is_silent_noop(self) -> None:
        sc = self._make_skill_creator(["0.2.0-anthropic.85cce0381e"])
        mp = _write_marketplace(self.home, [
            {"cachePath": str(self.plugin_root.resolve()), "name": "loopengine",
             "source": "filesystem", "version": VERSION},
            {"cachePath": str(sc / "0.2.0-anthropic.85cce0381e"), "name": "skill-creator",
             "source": "filesystem", "version": "0.2.0-anthropic.85cce0381e"},
        ])
        before = mp.read_text(encoding="utf-8")
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mp.read_text(encoding="utf-8"), before)
        self.assertEqual(result.stderr, "")

    def test_missing_seed_skips(self) -> None:
        _write_marketplace(self.home, [])
        shutil.rmtree(self.plugin_root)
        result = _run(self.plugin_root, self.home)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

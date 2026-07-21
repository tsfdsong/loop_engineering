"""Tests for install skip/repair when ZCode discovery is broken."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from loopengine_install.lifecycle import _skip_blocked_reason
from loopengine_install.ops import Manifest


class SkipRepairTest(unittest.TestCase):
    def test_missing_manifest_target_blocks_skip(self):
        m = Manifest(
            schema_version=2,
            product="loopengine",
            version="1.3.2",
            installed_at="2026-07-21T00:00:00Z",
            central_root="/tmp/c",
            skill_names=["go"],
            components={"cursor": {"ops": 1}},
            operations=[],
        )
        with tempfile.TemporaryDirectory() as td:
            reason = _skip_blocked_reason(Path(td), ["cursor", "zcode"], m)
        self.assertIn("missing targets", reason or "")

    def test_suppressed_builtins_blocks_skip(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            key = "loopengine@zcode-plugins-official"
            mp = (
                home
                / ".zcode"
                / "cli"
                / "plugins"
                / "marketplaces"
                / "zcode-plugins-official"
                / "marketplace.json"
            )
            mp.parent.mkdir(parents=True)
            cache = (
                home
                / ".zcode"
                / "cli"
                / "plugins"
                / "cache"
                / "zcode-plugins-official"
                / "loopengine"
                / "1.3.2"
            )
            (cache / ".zcode-plugin").mkdir(parents=True)
            (cache / ".zcode-plugin" / "plugin.json").write_text(
                '{"name":"loopengine"}\n', encoding="utf-8"
            )
            mp.write_text(
                json.dumps(
                    {
                        "plugins": [
                            {
                                "name": "loopengine",
                                "cachePath": str(cache),
                                "version": "1.3.2",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            cfg = home / ".zcode" / "cli" / "config.json"
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(
                json.dumps(
                    {
                        "plugins": {
                            "enabledPlugins": {key: True},
                            "suppressedBuiltins": [key],
                        }
                    }
                ),
                encoding="utf-8",
            )
            m = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.3.2",
                installed_at="2026-07-21T00:00:00Z",
                central_root="/tmp/c",
                skill_names=["go"],
                components={"zcode": {"ops": 1}},
                operations=[],
            )
            reason = _skip_blocked_reason(home, ["zcode"], m)
            self.assertIn("suppressedBuiltins", reason or "")


if __name__ == "__main__":
    unittest.main()

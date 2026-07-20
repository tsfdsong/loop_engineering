"""Tests for install --check mini-doctor."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from loopengine_install.lifecycle import do_check
from loopengine_install.ops import Manifest, Operation, save_manifest


class CheckTest(unittest.TestCase):
    def test_missing_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            report = do_check(home=home, json_out=False)
            self.assertFalse(report["ok"])

    def test_ops_ok_and_detect_missing_link(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            central = home / ".loopengine" / "plugins" / "loopengine" / "1.0.0"
            central.mkdir(parents=True)
            dest = home / ".cursor" / "plugins" / "local" / "loopengine"
            dest.parent.mkdir(parents=True)
            dest.mkdir()
            (dest / "ok.txt").write_text("x", encoding="utf-8")
            m = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.0.0",
                installed_at="2026-07-20T00:00:00Z",
                central_root=str(central),
                skill_names=["go"],
                components={},
                operations=[
                    Operation(
                        id="op1",
                        kind="link-or-copy",
                        ownership="managed",
                        source=str(central),
                        destination=str(dest),
                    )
                ],
            )
            save_manifest(home / ".loopengine" / "install-manifest.json", m)
            report = do_check(home=home, json_out=False)
            self.assertTrue(report["ok"], report)

            # break destination
            import shutil

            shutil.rmtree(dest)
            report2 = do_check(home=home, json_out=False)
            self.assertFalse(report2["ok"])
            self.assertTrue(any(i["id"] == "op1" for i in report2["issues"]))


if __name__ == "__main__":
    unittest.main()

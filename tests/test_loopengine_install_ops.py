"""Tests for loopengine_install.ops."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loopengine_install.ops import (
    Manifest,
    Operation,
    apply_operation,
    load_manifest,
    revert_operation,
    save_manifest,
    validate_manifest,
)


class OpsTest(unittest.TestCase):
    def test_link_or_copy_and_revert(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src, dst = td / "src", td / "dst"
            src.mkdir()
            (src / "a.txt").write_text("x", encoding="utf-8")
            op = Operation(
                id="op-1",
                kind="link-or-copy",
                ownership="managed",
                source=str(src),
                destination=str(dst),
            )
            apply_operation(op)
            self.assertTrue(dst.exists())
            self.assertEqual((dst / "a.txt").read_text(encoding="utf-8"), "x")
            revert_operation(op)
            self.assertFalse(dst.exists())

    def test_manifest_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "install-manifest.json"
            m = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.3.2",
                installed_at="2026-07-20T00:00:00Z",
                central_root="/tmp/central",
                skill_names=["go", "loop"],
                components={},
                operations=[],
            )
            save_manifest(path, m)
            m2 = load_manifest(path)
            self.assertEqual(m2.version, "1.3.2")
            validate_manifest(m2)


if __name__ == "__main__":
    unittest.main()

"""Tests for central package builder."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loopengine_install.package import build_central_package, read_repo_version


class PackageTest(unittest.TestCase):
    def test_build_central_package(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / ".loopengine"
            ver = read_repo_version(repo)
            dest = build_central_package(repo, home, ver)
            self.assertTrue((dest / "skills").is_dir())
            self.assertTrue(any((dest / "skills").iterdir()))
            self.assertTrue((dest / ".cursor-plugin" / "plugin.json").is_file())
            current = home / "plugins" / "loopengine" / "current"
            self.assertTrue(current.exists())


if __name__ == "__main__":
    unittest.main()

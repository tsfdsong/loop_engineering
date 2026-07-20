"""CLI parse tests."""

from __future__ import annotations

import unittest

from loopengine_install.cli import parse_args


class CliTest(unittest.TestCase):
    def test_default_install(self):
        a = parse_args([])
        self.assertEqual(a.command, "install")

    def test_uninstall(self):
        a = parse_args(["uninstall"])
        self.assertEqual(a.command, "uninstall")

    def test_uninstall_flag(self):
        a = parse_args(["--uninstall"])
        self.assertEqual(a.command, "uninstall")

    def test_upgrade_alias(self):
        a = parse_args(["upgrade"])
        self.assertEqual(a.command, "install")

    def test_flags(self):
        a = parse_args(["--dry-run", "--json", "--only=cursor,zcode"])
        self.assertTrue(a.dry_run)
        self.assertTrue(a.json_out)
        self.assertEqual(a.only, ["cursor", "zcode"])


if __name__ == "__main__":
    unittest.main()

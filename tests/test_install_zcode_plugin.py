"""Regression tests for the deprecated ZCode emergency CLI."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from install_zcode_plugin import cmd_install, cmd_uninstall


class InstallZCodePluginCliTest(unittest.TestCase):
    def test_dry_run_includes_dedicated_marketplace_write(self):
        repo = Path(__file__).resolve().parents[1]
        output = io.StringIO()

        with redirect_stdout(output):
            result = cmd_install(repo, dry_run=True)

        self.assertEqual(result, 0)
        self.assertIn("marketplace.json", output.getvalue())
        self.assertIn("loopengine-local", output.getvalue())

    def test_uninstall_dry_run_includes_marketplace_removal(self):
        output = io.StringIO()

        with redirect_stdout(output):
            result = cmd_uninstall("1.3.2", dry_run=True)

        self.assertEqual(result, 0)
        self.assertIn("marketplace.json", output.getvalue())


if __name__ == "__main__":
    unittest.main()

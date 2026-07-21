"""Tests for MCP binary capability detection."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from loopengine_install import detect  # noqa: E402


class HeadroomMcpDetectionTest(unittest.TestCase):
    @patch("loopengine_install.detect.subprocess.run")
    def test_capability_probe_accepts_mcp_help(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        self.assertTrue(detect.supports_headroom_mcp("/tools/headroom"))
        mock_run.assert_called_once_with(
            ["/tools/headroom", "mcp", "serve", "--help"],
            capture_output=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=10,
        )

    @patch("loopengine_install.detect.subprocess.run")
    def test_capability_probe_rejects_interactive_cli(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)

        self.assertFalse(detect.supports_headroom_mcp("/tools/headroom"))

    @patch("loopengine_install.detect.subprocess.run")
    def test_capability_probe_rejects_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["/tools/headroom", "mcp", "serve", "--help"],
            timeout=10,
        )

        self.assertFalse(detect.supports_headroom_mcp("/tools/headroom"))

    @patch("loopengine_install.detect.supports_headroom_mcp", return_value=False)
    @patch("loopengine_install.detect.shutil.which")
    def test_detect_filters_non_mcp_headroom(self, mock_which, mock_supports):
        paths = {
            "jcodemunch": None,
            "jcodemunch-mcp": "/tools/jcodemunch-mcp",
            "repomix": "/tools/repomix",
            "headroom": "/tools/headroom",
        }
        mock_which.side_effect = paths.get

        result = detect.detect_mcp_binaries()

        self.assertEqual(result["jcodemunch"], "/tools/jcodemunch-mcp")
        self.assertEqual(result["repomix"], "/tools/repomix")
        self.assertIsNone(result["headroom"])
        mock_supports.assert_called_once_with("/tools/headroom")


if __name__ == "__main__":
    unittest.main()

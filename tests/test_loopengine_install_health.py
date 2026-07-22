"""Tests for shared install health checks."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from loopengine_install.health import (
    check_cursor_plugin,
    run_health_checks,
)
from loopengine_install.ops import Manifest, Operation


class HealthChecksTest(unittest.TestCase):
    def test_cursor_flat_skills_detected(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            flat = home / ".cursor" / "skills" / "go"
            flat.mkdir(parents=True)
            (flat / "SKILL.md").write_text("# go", encoding="utf-8")
            manifest = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.0.0",
                installed_at="",
                central_root=str(home / "central"),
                skill_names=["go"],
                components={"cursor": {}},
                operations=[],
            )
            issues = check_cursor_plugin(home, manifest)
            self.assertTrue(any(i.id == "cursor-flat" for i in issues))

    def test_run_health_checks_merge_json(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            mcp = home / ".cursor" / "mcp.json"
            mcp.parent.mkdir(parents=True, exist_ok=True)
            mcp.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
            manifest = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.0.0",
                installed_at="",
                central_root=str(home / "central"),
                skill_names=[],
                operations=[
                    Operation(
                        id="cursor-mcp",
                        kind="merge-json",
                        ownership="managed",
                        destination=str(mcp),
                        merge_keys=["jcodemunch"],
                    )
                ],
            )
            issues = run_health_checks(manifest, home)
            self.assertTrue(any(i.id == "cursor-mcp" for i in issues))

    def test_cursor_ask_mcp_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            manifest = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.0.0",
                installed_at="",
                central_root=str(home / "central"),
                skill_names=[],
                components={"cursor": {}},
                operations=[],
            )
            issues = check_cursor_plugin(home, manifest)
            self.assertTrue(any(i.id == "cursor-ask-mcp" for i in issues))

    def test_cursor_ask_mcp_missing_key(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            mcp = home / ".cursor" / "mcp.json"
            mcp.parent.mkdir(parents=True, exist_ok=True)
            mcp.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
            manifest = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.0.0",
                installed_at="",
                central_root=str(home / "central"),
                skill_names=[],
                components={"cursor": {}},
                operations=[],
            )
            issues = check_cursor_plugin(home, manifest)
            self.assertTrue(any(i.id == "cursor-ask-mcp" for i in issues))

    def test_cursor_ask_mcp_present_no_issue(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            mcp = home / ".cursor" / "mcp.json"
            mcp.parent.mkdir(parents=True, exist_ok=True)
            mcp.write_text(
                json.dumps({"mcpServers": {"loopengine-ask": {"command": "python3"}}}),
                encoding="utf-8",
            )
            manifest = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.0.0",
                installed_at="",
                central_root=str(home / "central"),
                skill_names=[],
                components={"cursor": {}},
                operations=[],
            )
            issues = check_cursor_plugin(home, manifest)
            self.assertFalse(any(i.id == "cursor-ask-mcp" for i in issues))


if __name__ == "__main__":
    unittest.main()

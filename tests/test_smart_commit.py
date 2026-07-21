#!/usr/bin/env python3
"""Unit tests for scripts/smart_commit.py (spec §7)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import smart_commit as sc  # noqa: E402


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(td: Path) -> Path:
    _git(td, "init")
    _git(td, "config", "user.email", "test@example.com")
    _git(td, "config", "user.name", "Test")
    (td / "README.md").write_text("hi\n", encoding="utf-8")
    _git(td, "add", "README.md")
    _git(td, "commit", "-m", "init")
    return td


class FilterUnitTest(unittest.TestCase):
    def test_skip_env_and_log(self):
        self.assertIsNotNone(sc.skip_reason(".env"))
        self.assertIsNotNone(sc.skip_reason("app/.env.local"))
        self.assertIsNotNone(sc.skip_reason("debug.log"))
        self.assertIsNotNone(sc.skip_reason("certs/server.pem"))
        self.assertIsNotNone(sc.skip_reason("foo/node_modules/pkg/index.js"))
        self.assertIsNone(sc.skip_reason("src/main.go"))
        self.assertIsNone(sc.skip_reason("scripts/smart_commit.py"))

    def test_project_ignore(self):
        reason = sc.skip_reason("tmp/scratch.txt", ["tmp/", "*.bak"])
        self.assertEqual(reason, "project-ignore:tmp/")
        self.assertIsNone(sc.skip_reason("src/a.py", ["tmp/"]))

    def test_filter_changes_dedup(self):
        changes = [
            sc.Change("a.py", "modified"),
            sc.Change("a.py", "staged"),
            sc.Change(".env", "untracked"),
        ]
        r = sc.filter_changes(changes)
        self.assertEqual(r.will_add, ["a.py"])
        self.assertEqual(len(r.skipped), 1)
        self.assertEqual(r.skipped[0][0], ".env")


class SmartCommitRepoTest(unittest.TestCase):
    def test_not_a_repo(self):
        with tempfile.TemporaryDirectory() as td:
            code = sc.smart_commit(Path(td), "msg")
            self.assertEqual(code, 1)

    def test_missing_message(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            self.assertEqual(sc.smart_commit(repo, None), 2)
            self.assertEqual(sc.smart_commit(repo, "  "), 2)

    def test_modified_only_commits(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            (repo / "README.md").write_text("hi2\n", encoding="utf-8")
            code = sc.smart_commit(repo, "chore: update readme")
            self.assertEqual(code, 0)
            log = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%s"], cwd=str(repo), text=True
            ).strip()
            self.assertEqual(log, "chore: update readme")

    def test_untracked_source_skips_noise(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            (repo / "feat.py").write_text("x=1\n", encoding="utf-8")
            (repo / ".env").write_text("SECRET=1\n", encoding="utf-8")
            (repo / "noise.log").write_text("log\n", encoding="utf-8")
            code = sc.smart_commit(repo, "feat: add feat")
            self.assertEqual(code, 0)
            # .env and log must not be in the commit tree
            show = subprocess.check_output(
                ["git", "show", "--name-only", "--pretty=", "HEAD"],
                cwd=str(repo),
                text=True,
            )
            self.assertIn("feat.py", show)
            self.assertNotIn(".env", show)
            self.assertNotIn("noise.log", show)
            # still untracked locally
            st = subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=str(repo), text=True
            )
            self.assertIn(".env", st)
            self.assertIn("noise.log", st)

    def test_dry_run_no_commit(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            (repo / "new.py").write_text("y=2\n", encoding="utf-8")
            before = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(repo), text=True
            ).strip()
            code = sc.smart_commit(repo, "should not land", dry_run=True)
            self.assertEqual(code, 0)
            after = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(repo), text=True
            ).strip()
            self.assertEqual(before, after)
            st = subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=str(repo), text=True
            )
            self.assertIn("?? new.py", st)

    def test_nothing_after_filter(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            (repo / ".env").write_text("x=1\n", encoding="utf-8")
            code = sc.smart_commit(repo, "nope")
            self.assertEqual(code, 1)

    def test_cli_main_missing_m(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            (repo / "a.py").write_text("1\n", encoding="utf-8")
            code = sc.main(["--cwd", str(repo)])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/smart_commit.py — 智能 stage + commit（规则 + 启发式）
# ────────────────────────────────────────────────────────────
# Spec: docs/2026-07-21-smart-git-commit-design.md
#
# 用法:
#   python3 scripts/smart_commit.py -m "<message>" [--dry-run] [--push]
#   python3 scripts/smart_commit.py --cwd <repo> -m "..."
# ────────────────────────────────────────────────────────────

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_IGNORE_FILE = ".loopengine-commit-ignore"

# Directory path prefixes / components (normalized with /)
_DIR_BLOCKLIST = (
    "node_modules/",
    "vendor/",
    "dist/",
    "build/",
    ".next/",
    "__pycache__/",
    "coverage/",
    "htmlcov/",
    ".pytest_cache/",
    ".idea/",
    ".vscode/",
)

# Basename / path glob patterns
_GLOB_BLOCKLIST = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.log",
    "*.tmp",
    "*.pyc",
    "*.swp",
    ".DS_Store",
)

# Substring tokens in path (case-insensitive)
_TOKEN_BLOCKLIST = ("credentials", "secret")


@dataclass
class Change:
    path: str
    kind: str  # modified | deleted | untracked | staged


@dataclass
class FilterResult:
    will_add: list[str]
    skipped: list[tuple[str, str]]  # path, reason


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )


def is_git_repo(cwd: Path) -> bool:
    r = _run_git(cwd, "rev-parse", "--is-inside-work-tree", check=False)
    return r.returncode == 0 and r.stdout.strip() == "true"


def parse_porcelain(text: str) -> list[Change]:
    """Parse `git status --porcelain` (v1) into Change entries.

    Handles rename (`R  old -> new`) by using the new path.
    Untracked dirs may appear as `?? dir/` — expand via listing is not done;
    git usually lists files when not ignored; keep path as reported.
    """
    changes: list[Change] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        # porcelain: XY PATH or XY ORIG -> PATH
        xy = line[:2]
        rest = line[3:] if len(line) > 3 else ""
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        path = rest.strip().strip('"')
        if not path:
            continue
        # Prefer working-tree / untracked signals
        if xy == "??":
            changes.append(Change(path=path, kind="untracked"))
            continue
        if "D" in xy:
            changes.append(Change(path=path, kind="deleted"))
            continue
        # staged-only or modified
        if xy[0] != " " and xy[0] != "?":
            changes.append(Change(path=path, kind="staged"))
        elif xy[1] != " " and xy[1] != "?":
            changes.append(Change(path=path, kind="modified"))
        else:
            changes.append(Change(path=path, kind="modified"))
    return changes


def collect_changes(cwd: Path) -> list[Change]:
    r = _run_git(cwd, "status", "--porcelain", check=True)
    return parse_porcelain(r.stdout)


def _norm(path: str) -> str:
    n = path.replace("\\", "/")
    while n.startswith("./"):
        n = n[2:]
    return n


def _basename(path: str) -> str:
    return Path(_norm(path)).name


def load_project_ignore_patterns(cwd: Path) -> list[str]:
    path = cwd / PROJECT_IGNORE_FILE
    if not path.is_file():
        return []
    patterns: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        patterns.append(s)
    return patterns


def _match_gitignore_like(path: str, pattern: str) -> bool:
    """Minimal gitignore-like match: glob on full path and basename; **/ prefix."""
    n = _norm(path)
    p = pattern.strip()
    if not p:
        return False
    if p.endswith("/"):
        # directory rule
        d = p.rstrip("/")
        return n == d or n.startswith(d + "/") or f"/{d}/" in f"/{n}/"
    if p.startswith("/"):
        p = p[1:]
        return fnmatch.fnmatch(n, p) or n == p
    if "**" in p:
        # reduce ** to * for fnmatch across /
        alt = p.replace("**/", "*").replace("**", "*")
        return fnmatch.fnmatch(n, alt) or fnmatch.fnmatch(_basename(n), alt)
    return (
        fnmatch.fnmatch(n, p)
        or fnmatch.fnmatch(_basename(n), p)
        or fnmatch.fnmatch(n, "*/" + p)
        or any(fnmatch.fnmatch(part, p) for part in n.split("/"))
    )


def skip_reason(path: str, project_patterns: list[str] | None = None) -> str | None:
    """Return skip reason or None if the path should be staged."""
    n = _norm(path)
    low = n.lower()
    base = _basename(n)

    for token in _TOKEN_BLOCKLIST:
        if token in low:
            return f"token:{token}"

    for g in _GLOB_BLOCKLIST:
        if fnmatch.fnmatch(base, g) or fnmatch.fnmatch(n, g):
            return f"glob:{g}"

    for d in _DIR_BLOCKLIST:
        name = d.rstrip("/")
        if n == name or n.startswith(name + "/") or f"/{name}/" in f"/{n}/":
            return f"dir:{name}"

    for pat in project_patterns or []:
        if _match_gitignore_like(n, pat):
            return f"project-ignore:{pat}"

    return None


def filter_changes(
    changes: list[Change], project_patterns: list[str] | None = None
) -> FilterResult:
    will: list[str] = []
    skipped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for ch in changes:
        p = _norm(ch.path)
        if p in seen:
            continue
        seen.add(p)
        reason = skip_reason(p, project_patterns)
        if reason:
            skipped.append((p, reason))
        else:
            will.append(p)
    return FilterResult(will_add=will, skipped=skipped)


def format_report(result: FilterResult, commit_line: str) -> str:
    lines = ["WILL ADD:"]
    if result.will_add:
        lines.extend(f"  {p}" for p in result.will_add)
    else:
        lines.append("  (none)")
    lines.append("SKIPPED:")
    if result.skipped:
        lines.extend(f"  {p}  ({r})" for p, r in result.skipped)
    else:
        lines.append("  (none)")
    lines.append(f"COMMIT: {commit_line}")
    return "\n".join(lines) + "\n"


def smart_commit(
    cwd: Path,
    message: str | None,
    *,
    dry_run: bool = False,
    do_push: bool = False,
) -> int:
    if not is_git_repo(cwd):
        print("ERROR: not a git repository", file=sys.stderr)
        return 1
    if not message or not message.strip():
        print("ERROR: -m / --message is required", file=sys.stderr)
        return 2

    changes = collect_changes(cwd)
    patterns = load_project_ignore_patterns(cwd)
    result = filter_changes(changes, patterns)

    if not result.will_add:
        print(format_report(result, "failed"), end="")
        print("ERROR: nothing to commit after filters", file=sys.stderr)
        return 1

    if dry_run:
        print(format_report(result, "dry-run"), end="")
        return 0

    add = _run_git(cwd, "add", "--", *result.will_add, check=False)
    if add.returncode != 0:
        print(format_report(result, "failed"), end="")
        print(add.stderr or add.stdout, file=sys.stderr)
        return 1

    commit = _run_git(cwd, "commit", "-m", message.strip(), check=False)
    if commit.returncode != 0:
        print(format_report(result, "failed"), end="")
        print(commit.stderr or commit.stdout, file=sys.stderr)
        return 1

    sha_r = _run_git(cwd, "rev-parse", "--short", "HEAD", check=False)
    sha = sha_r.stdout.strip() if sha_r.returncode == 0 else "ok"
    print(format_report(result, sha), end="")

    if do_push:
        push = _run_git(cwd, "push", check=False)
        if push.returncode != 0:
            print("ERROR: push failed (commit kept)", file=sys.stderr)
            print(push.stderr or push.stdout, file=sys.stderr)
            return 1
        print("PUSH: ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Smart stage + commit with rule/heuristic filters (no LLM)."
    )
    p.add_argument("-m", "--message", help="Commit message (required)")
    p.add_argument("--dry-run", action="store_true", help="Print plan only")
    p.add_argument("--push", action="store_true", help="Push after successful commit")
    p.add_argument(
        "--cwd",
        default=".",
        help="Repository working directory (default: .)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cwd = Path(args.cwd).expanduser().resolve()
    return smart_commit(
        cwd,
        args.message,
        dry_run=args.dry_run,
        do_push=args.push,
    )


if __name__ == "__main__":
    sys.exit(main())

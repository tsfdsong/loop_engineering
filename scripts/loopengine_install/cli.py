"""CLI for python -m loopengine_install / install.py."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CliArgs:
    command: str
    dry_run: bool = False
    json_out: bool = False
    force: bool = False
    all_tools: bool = False
    only: list[str] | None = None
    check: bool = False
    repo_root: Path | None = None


def parse_args(argv: list[str] | None = None) -> CliArgs:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="loopengine_install")
    parser.add_argument(
        "command",
        nargs="?",
        default="install",
        choices=["install", "uninstall", "upgrade"],
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", dest="json_out", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--all", dest="all_tools", action="store_true")
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated tool ids (e.g. cursor,zcode,claude)",
    )
    parser.add_argument("--target", default="", help="Alias for --only")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--repo",
        default="",
        help="Override repo root (default: discover from install.py / cwd)",
    )
    if "--uninstall" in argv:
        argv = [a for a in argv if a != "--uninstall"]
        if not argv or argv[0] not in ("install", "uninstall", "upgrade"):
            argv = ["uninstall", *argv]

    ns = parser.parse_args(argv)
    only_raw = ns.only or ns.target
    only = [x.strip() for x in only_raw.replace(" ", ",").split(",") if x.strip()]
    cmd = ns.command
    if cmd == "upgrade":
        cmd = "install"
    repo = Path(ns.repo).resolve() if ns.repo else None
    return CliArgs(
        command=cmd,
        dry_run=ns.dry_run,
        json_out=ns.json_out,
        force=ns.force,
        all_tools=ns.all_tools,
        only=only or None,
        check=ns.check,
        repo_root=repo,
    )


def _discover_repo(explicit: Path | None) -> Path:
    if explicit and explicit.is_dir():
        return explicit
    # Prefer parent of scripts/ when imported from package
    here = Path(__file__).resolve()
    candidate = here.parents[2]  # scripts/loopengine_install/cli.py → repo root
    if (candidate / "package.json").is_file() and (candidate / "skills").is_dir():
        return candidate
    cwd = Path.cwd()
    if (cwd / "package.json").is_file():
        return cwd
    raise SystemExit("Cannot locate LoopEngine repo root (pass --repo)")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check and args.command == "install":
        path = Path.home() / ".loopengine" / "install-manifest.json"
        ok = path.is_file()
        payload = {"ok": ok, "manifest": str(path)}
        print(json.dumps(payload) if args.json_out else f"check: {'ok' if ok else 'missing manifest'}")
        return 0 if ok else 1

    from loopengine_install import lifecycle

    if args.command == "uninstall":
        lifecycle.do_uninstall(
            dry_run=args.dry_run,
            json_out=args.json_out,
        )
        return 0

    repo = _discover_repo(args.repo_root)
    lifecycle.do_install(
        repo_root=repo,
        only=args.only,
        all_tools=args.all_tools,
        dry_run=args.dry_run,
        force=args.force,
        json_out=args.json_out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

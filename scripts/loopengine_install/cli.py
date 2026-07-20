"""CLI for python -m loopengine_install / install.py."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass


@dataclass
class CliArgs:
    command: str
    dry_run: bool = False
    json_out: bool = False
    force: bool = False
    all_tools: bool = False
    only: list[str] | None = None
    check: bool = False


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
    # Compat: install.py --uninstall
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
    return CliArgs(
        command=cmd,
        dry_run=ns.dry_run,
        json_out=ns.json_out,
        force=ns.force,
        all_tools=ns.all_tools,
        only=only or None,
        check=ns.check,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check and args.command == "install":
        # P3 stub
        if args.json_out:
            print(json.dumps({"ok": True, "check": "stub"}))
        else:
            print("check: stub (ok)")
        return 0

    # Lifecycle wired in later tasks; for now report parsed plan
    payload = {
        "command": args.command,
        "dry_run": args.dry_run,
        "force": args.force,
        "all": args.all_tools,
        "only": args.only,
    }
    if args.json_out:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"loopengine_install: {args.command} (lifecycle pending)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

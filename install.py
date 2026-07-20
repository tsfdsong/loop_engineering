#!/usr/bin/env python3
"""LoopEngine one-click installer entry (macOS / Windows / Linux).

Usage:
  curl -fsSL …/install.py | python3
  python3 install.py install|uninstall|upgrade [flags]
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MIN = (3, 10)
REPO_URL = "https://github.com/tsfdsong/loop_engineering.git"
DEFAULT_SRC = Path.home() / ".loopengine" / "src"


def _ensure_python() -> int | None:
    if sys.version_info < MIN:
        print(
            f"LoopEngine requires Python >= {MIN[0]}.{MIN[1]} "
            f"(found {sys.version_info.major}.{sys.version_info.minor})",
            file=sys.stderr,
        )
        return 1
    return None


def _repo_root_from_file() -> Path | None:
    try:
        here = Path(__file__).resolve()
    except NameError:
        return None
    if here.name == "install.py" and (here.parent / "scripts" / "loopengine_install").is_dir():
        return here.parent
    return None


def _ensure_src_checkout() -> Path:
    src = DEFAULT_SRC
    if (src / "scripts" / "loopengine_install").is_dir():
        subprocess.run(["git", "-C", str(src), "pull", "--ff-only"], check=False)
        return src
    src.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        subprocess.run(["git", "-C", str(src), "pull", "--ff-only"], check=False)
    else:
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(src)],
            check=True,
        )
    return src


def main(argv: list[str] | None = None) -> int:
    err = _ensure_python()
    if err is not None:
        return err

    repo = _repo_root_from_file()
    if repo is None:
        # Piped from curl: clone then re-exec from checkout
        repo = _ensure_src_checkout()
        install_py = repo / "install.py"
        cmd = [sys.executable, str(install_py), *(argv if argv is not None else sys.argv[1:])]
        os.execv(sys.executable, cmd)  # noqa: S606 — intentional re-exec

    scripts = repo / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from loopengine_install.cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

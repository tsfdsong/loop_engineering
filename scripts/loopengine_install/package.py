"""Build and switch the LoopEngine central plugin package."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def read_repo_version(repo_root: Path) -> str:
    pkg = repo_root / "package.json"
    data = json.loads(pkg.read_text(encoding="utf-8"))
    return str(data["version"])


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _run_render_plugins(repo_root: Path, out_dir: Path) -> None:
    script = repo_root / "scripts" / "render_plugins.py"
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(script), str(repo_root), str(out_dir)],
        check=True,
        cwd=str(repo_root),
    )


def _place_overlays(rendered: Path, dest: Path) -> None:
    mapping = {
        "cursor-plugin": ".cursor-plugin",
        "claude-plugin": ".claude-plugin",
        "zcode-plugin": ".zcode-plugin",
        "codex-plugin": ".codex-plugin",
        "kimi-plugin": ".kimi-plugin",
    }
    for src_name, dst_name in mapping.items():
        src = rendered / src_name
        if src.is_dir():
            _copy_tree(src, dest / dst_name)
    gemini = rendered / "gemini-extension.json"
    if gemini.is_file():
        shutil.copy2(gemini, dest / "gemini-extension.json")


def _set_current(loopengine_home: Path, version: str, dest: Path) -> None:
    """Write current as a pointer file only (D13 — never a symlink)."""
    current = loopengine_home / "plugins" / "loopengine" / "current"
    if current.is_symlink() or current.is_file():
        current.unlink()
    elif current.is_dir():
        shutil.rmtree(current)
    current.write_text(str(dest.resolve()) + "\n", encoding="utf-8")


def build_central_package(
    repo_root: Path,
    loopengine_home: Path,
    version: str | None = None,
) -> Path:
    """Copy skills/hooks/commands + rendered manifests into versioned central package."""
    repo_root = repo_root.resolve()
    loopengine_home = loopengine_home.expanduser().resolve()
    version = version or read_repo_version(repo_root)
    dest = loopengine_home / "plugins" / "loopengine" / version
    dest.mkdir(parents=True, exist_ok=True)

    for name in ("skills", "hooks", "commands"):
        _copy_tree(repo_root / name, dest / name)

    for doc in ("AGENTS.md", "README.md"):
        src = repo_root / doc
        if src.is_file():
            shutil.copy2(src, dest / doc)

    rendered = loopengine_home / "plugins" / "loopengine" / f".render-{version}"
    try:
        _run_render_plugins(repo_root, rendered)
        _place_overlays(rendered, dest)
    finally:
        if rendered.exists():
            shutil.rmtree(rendered, ignore_errors=True)

    _set_current(loopengine_home, version, dest)
    return dest


def resolve_current(loopengine_home: Path) -> Path | None:
    current = loopengine_home.expanduser() / "plugins" / "loopengine" / "current"
    # Legacy symlink installs: resolve once; callers should rebuild to pointer.
    if current.is_symlink():
        target = current.resolve()
        return target if target.exists() else None
    if current.is_file():
        target = Path(current.read_text(encoding="utf-8").strip())
        return target if target.exists() else None
    if current.is_dir():
        return current.resolve()
    return None

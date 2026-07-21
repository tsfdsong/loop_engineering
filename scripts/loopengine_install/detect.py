"""Detect installed AI agent homes and MCP binaries."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

# id -> relative path under $HOME that indicates install
AGENT_MARKERS: dict[str, str] = {
    "zcode": ".zcode",
    "claude": ".claude",
    "cursor": ".cursor",
    "codex": ".codex",
    "gemini": ".gemini",
    "copilot": ".copilot",
    "pi": ".pi",
}


def detect_agents(home: Path | None = None) -> list[str]:
    home = Path(home or Path.home())
    found: list[str] = []
    for agent_id, rel in AGENT_MARKERS.items():
        if (home / rel).exists():
            found.append(agent_id)
    return found


def supports_headroom_mcp(executable: str) -> bool:
    """True only when ``headroom mcp serve --help`` exits 0 within timeout.

    Filters PyPI's interactive ``headroom`` CLI that blocks on stdin.
    """
    try:
        result = subprocess.run(
            [executable, "mcp", "serve", "--help"],
            capture_output=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def detect_mcp_binaries() -> dict[str, str | None]:
    def _which(*names: str) -> str | None:
        for n in names:
            path = shutil.which(n)
            if path:
                return path
        return None

    headroom = _which("headroom")
    if headroom and not supports_headroom_mcp(headroom):
        headroom = None

    return {
        "jcodemunch": _which("jcodemunch", "jcodemunch-mcp"),
        "repomix": _which("repomix"),
        "headroom": headroom,
    }

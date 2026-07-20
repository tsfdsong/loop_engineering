"""Adapter registry."""

from __future__ import annotations

from loopengine_install.adapters.base import Adapter
from loopengine_install.adapters.claude import ClaudeAdapter
from loopengine_install.adapters.codex import CodexAdapter
from loopengine_install.adapters.copilot import CopilotAdapter
from loopengine_install.adapters.cursor import CursorAdapter
from loopengine_install.adapters.gemini import GeminiAdapter
from loopengine_install.adapters.pi import PiAdapter
from loopengine_install.adapters.zcode import ZCodeAdapter

ADAPTERS: dict[str, Adapter] = {
    "cursor": CursorAdapter(),
    "claude": ClaudeAdapter(),
    "zcode": ZCodeAdapter(),
    "codex": CodexAdapter(),
    "gemini": GeminiAdapter(),
    "copilot": CopilotAdapter(),
    "pi": PiAdapter(),
}

TIER1 = ("cursor", "claude", "zcode")
TIER2 = ("codex", "gemini")
TIER3 = ("copilot", "pi")
ALL_TOOLS = TIER1 + TIER2 + TIER3


def get_adapters(names: list[str] | None) -> list[Adapter]:
    if not names:
        return list(ADAPTERS.values())
    out = []
    for n in names:
        if n not in ADAPTERS:
            raise KeyError(f"unknown adapter: {n} (known: {sorted(ADAPTERS)})")
        out.append(ADAPTERS[n])
    return out

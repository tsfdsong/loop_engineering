"""Adapter registry."""

from __future__ import annotations

from loopengine_install.adapters.base import Adapter
from loopengine_install.adapters.claude import ClaudeAdapter
from loopengine_install.adapters.cursor import CursorAdapter
from loopengine_install.adapters.zcode import ZCodeAdapter

ADAPTERS: dict[str, Adapter] = {
    "cursor": CursorAdapter(),
    "claude": ClaudeAdapter(),
    "zcode": ZCodeAdapter(),
}


def get_adapters(names: list[str] | None) -> list[Adapter]:
    if not names:
        return list(ADAPTERS.values())
    out = []
    for n in names:
        if n not in ADAPTERS:
            raise KeyError(f"unknown adapter: {n} (known: {sorted(ADAPTERS)})")
        out.append(ADAPTERS[n])
    return out

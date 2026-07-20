"""Gemini Tier-2 adapter."""

from loopengine_install.adapters._sync_inject import SyncInjectAdapter


class GeminiAdapter(SyncInjectAdapter):
    name = "gemini"
    relative_plugin_root = (".gemini", "extensions", "loopengine")
    agents_relative = (".gemini", "GEMINI.md")

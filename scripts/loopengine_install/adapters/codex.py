"""Codex Tier-2 adapter."""

from loopengine_install.adapters._sync_inject import SyncInjectAdapter


class CodexAdapter(SyncInjectAdapter):
    name = "codex"
    relative_plugin_root = (".codex", "skills", "loopengine")
    agents_relative = (".codex", "AGENTS.md")

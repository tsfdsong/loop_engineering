"""GitHub Copilot Tier-3 adapter (inject + skills tree)."""

from loopengine_install.adapters._sync_inject import SyncInjectAdapter


class CopilotAdapter(SyncInjectAdapter):
    name = "copilot"
    relative_plugin_root = (".copilot", "skills", "loopengine")
    agents_relative = (".copilot", "AGENTS.md")

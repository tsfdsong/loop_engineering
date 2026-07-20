"""Pi Tier-3 adapter."""

from loopengine_install.adapters._sync_inject import SyncInjectAdapter


class PiAdapter(SyncInjectAdapter):
    name = "pi"
    relative_plugin_root = (".pi", "skills", "loopengine")
    agents_relative = (".pi", "AGENTS.md")

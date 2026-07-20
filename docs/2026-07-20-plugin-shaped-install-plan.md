# Plugin-Shaped Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `install.sh` / `install.ps1` deploy LoopEngine as a Superpowers-style plugin bundle (central package + per-tool adapters) with install/upgrade/uninstall, ending Cursor flat skills and registering Claude in `installed_plugins.json`.

**Architecture:** Single content root at `~/.loopengine/plugins/loopengine/<version>/`; adapters sync/link into each tool’s plugin root and write registries; `~/.loopengine/install-manifest.json` is the sole source of truth for upgrade/uninstall. P0 spikes gate Cursor `plugins/local` and Claude registry before P1+.

**Tech Stack:** Bash (`install.sh`, `scripts/install/_common.sh`), PowerShell (`install.ps1`), Python 3 helpers (`scripts/_lib/json_io.py`, new manifest/registry modules), unittest.

**Spec:** `docs/2026-07-20-plugin-shaped-install-design.md` (approved 2026-07-20)

---

## File map (create / modify)

| Path | Responsibility |
|------|----------------|
| `scripts/_lib/install_manifest.py` | Read/write/validate `install-manifest.json` |
| `scripts/_lib/plugin_sync.py` | Symlink-or-copy central → tool plugin_root; list skill names |
| `scripts/register_claude_marketplace.py` | Upsert Claude `known_marketplaces.json` + marketplace dir |
| `scripts/register_claude_plugin.py` | Upsert/remove Claude `installed_plugins.json` entry |
| `scripts/uninstall_loopengine.py` | Manifest-driven uninstall (packages + registries + redlines + MCP keys) |
| `scripts/install/_common.sh` | Central package build; remove flat Cursor copy; call adapters; `--uninstall`/`--upgrade` |
| `install.sh` / `install.ps1` | Parse new flags; dispatch uninstall |
| `tests/test_install_manifest.py` | Manifest schema + round-trip |
| `tests/test_register_claude_plugin.py` | Claude registry write/remove |
| `tests/test_plugin_sync.py` | Symlink/copy + skill name list |
| `tests/test_cursor_no_flat_deploy.py` | Assert deploy path logic does not flat-copy (unit against extracted functions or dry fixtures) |
| `docs/INSTALL.md` / `README.md` | Document new layout + flags |
| `scripts/audit_tools.py` | Optional P3: registry consistency check |

---

### Task 0: Mark spec approved + branch

**Files:**
- Modify: `docs/2026-07-20-plugin-shaped-install-design.md` (status line only)

- [ ] **Step 1: Update status**

Change header status from `Draft · 待用户审阅…` to `Approved · 2026-07-20`.

- [ ] **Step 2: Create feature branch**

```bash
git checkout -b go-plugin-shaped-install
git add docs/2026-07-20-plugin-shaped-install-design.md
git commit -m "docs(spec): mark plugin-shaped install design approved"
```

---

### Task 1: P0 Spike — Cursor `plugins/local` loads skills

**Files:**
- Create (temporary, do not commit unless useful): `/tmp/le-cursor-spike/` notes in spike log
- Create: `docs/spikes/2026-07-20-cursor-plugins-local.md` (commit result)

- [ ] **Step 1: Build minimal plugin tree**

```bash
SPIKE="$HOME/.cursor/plugins/local/loopengine-spike"
rm -rf "$SPIKE"
mkdir -p "$SPIKE/.cursor-plugin" "$SPIKE/skills/using-loopengine"
cp .cursor-plugin/plugin.json "$SPIKE/.cursor-plugin/plugin.json" 2>/dev/null || \
  printf '%s\n' '{"name":"loopengine-spike","version":"0.0.1","description":"spike"}' > "$SPIKE/.cursor-plugin/plugin.json"
cp skills/using-loopengine/SKILL.md "$SPIKE/skills/using-loopengine/SKILL.md"
# optional: copy one hook stub if hooks.json exists
```

- [ ] **Step 2: Manual verify in Cursor**

Open a **new** Cursor Agent chat. Ask: “Load using-loopengine and summarize LoopEngine cores.”  
Record PASS/FAIL in `docs/spikes/2026-07-20-cursor-plugins-local.md` with date and Cursor version if known.

- [ ] **Step 3: Gate**

If FAIL → **stop entire plan**; do not implement P1 flat-removal. Report to user.  
If PASS → commit spike notes and continue.

```bash
git add docs/spikes/2026-07-20-cursor-plugins-local.md
git commit -m "docs(spike): Cursor plugins/local skill load result"
```

---

### Task 2: P0 Spike — Claude local marketplace + `installed_plugins.json`

**Files:**
- Create: `docs/spikes/2026-07-20-claude-installed-plugins.md`
- Reference existing: `~/.claude/plugins/known_marketplaces.json`, `installed_plugins.json`

- [ ] **Step 1: Inspect live schema**

```bash
python3 - <<'PY'
import json
from pathlib import Path
home = Path.home()
for name in ["known_marketplaces.json", "installed_plugins.json"]:
    p = home / ".claude/plugins" / name
    print("===", name, "===")
    print(p.read_text()[:2000] if p.exists() else "MISSING")
PY
```

- [ ] **Step 2: Hand-register minimal loopengine-local**

Create:

```
~/.claude/plugins/marketplaces/loopengine-local/.claude-plugin/marketplace.json
~/.claude/plugins/cache/loopengine-local/loopengine/<version>/   # copy skills/go + .claude-plugin/plugin.json
```

Upsert `known_marketplaces.json` entry with `installLocation` pointing at the marketplace dir.  
Upsert `installed_plugins.json` key `loopengine@loopengine-local` with `installPath` = cache plugin root.

Exact JSON shape must match the sample entries already on the machine (map of plugin→list of records, `scope: user`).

- [ ] **Step 3: Verify in Claude Code**

New session: confirm plugin appears / skill loadable. Document PASS/FAIL and **lock** `installPath` choice (`cache/...` vs `skills/loopengine`) in the spike doc.

- [ ] **Step 4: Gate + commit**

FAIL → stop. PASS → commit spike doc; P2 Claude tasks must use the locked path.

```bash
git add docs/spikes/2026-07-20-claude-installed-plugins.md
git commit -m "docs(spike): Claude installed_plugins local marketplace result"
```

---

### Task 3: `install_manifest.py` (TDD)

**Files:**
- Create: `scripts/_lib/install_manifest.py`
- Create: `tests/test_install_manifest.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_install_manifest.py
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _lib.install_manifest import (
    Manifest,
    load_manifest,
    save_manifest,
    validate_manifest,
)


class TestInstallManifest(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "install-manifest.json"
            m = Manifest(
                schema_version=1,
                product="loopengine",
                version="1.3.2",
                central_root="/tmp/central",
                skill_names=["go", "loop"],
                components={
                    "cursor": {
                        "plugin_root": "/tmp/cursor-plugin",
                        "link_mode": "symlink",
                    }
                },
                extras={"redlines": [], "mcp": {"cursor": "", "keys": []}},
            )
            save_manifest(path, m)
            loaded = load_manifest(path)
            self.assertEqual(loaded.version, "1.3.2")
            self.assertEqual(loaded.skill_names, ["go", "loop"])
            self.assertEqual(loaded.components["cursor"]["link_mode"], "symlink")

    def test_validate_rejects_missing_version(self):
        bad = {"schema_version": 1, "product": "loopengine"}
        with self.assertRaises(ValueError):
            validate_manifest(bad)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_install_manifest.py -v
```

Expected: import error or missing module.

- [ ] **Step 3: Implement minimal module**

```python
# scripts/_lib/install_manifest.py
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


REQUIRED = ("schema_version", "product", "version", "central_root", "skill_names", "components")


@dataclass
class Manifest:
    schema_version: int
    product: str
    version: str
    central_root: str
    skill_names: list[str]
    components: dict[str, Any]
    extras: dict[str, Any] = field(default_factory=dict)
    installed_at: str = ""


def validate_manifest(data: dict[str, Any]) -> None:
    for key in REQUIRED:
        if key not in data:
            raise ValueError(f"missing required field: {key}")
    if not isinstance(data["skill_names"], list):
        raise ValueError("skill_names must be a list")
    if not isinstance(data["components"], dict):
        raise ValueError("components must be a dict")


def load_manifest(path: Path) -> Manifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_manifest(data)
    return Manifest(
        schema_version=int(data["schema_version"]),
        product=str(data["product"]),
        version=str(data["version"]),
        central_root=str(data["central_root"]),
        skill_names=list(data["skill_names"]),
        components=dict(data["components"]),
        extras=dict(data.get("extras") or {}),
        installed_at=str(data.get("installed_at") or ""),
    )


def save_manifest(path: Path, manifest: Manifest) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(manifest)
    validate_manifest(payload)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run — expect PASS**

```bash
python3 -m pytest tests/test_install_manifest.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/_lib/install_manifest.py tests/test_install_manifest.py
git commit -m "feat(install): add install-manifest read/write helper"
```

---

### Task 4: `plugin_sync.py` (symlink-or-copy + skill names)

**Files:**
- Create: `scripts/_lib/plugin_sync.py`
- Create: `tests/test_plugin_sync.py`

- [ ] **Step 1: Failing tests**

```python
# tests/test_plugin_sync.py
import os
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _lib.plugin_sync import list_skill_names, sync_plugin_root


class TestPluginSync(unittest.TestCase):
    def test_list_skill_names(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "skills" / "go").mkdir(parents=True)
            (root / "skills" / "loop").mkdir()
            (root / "skills" / "go" / "SKILL.md").write_text("x")
            (root / "skills" / "loop" / "SKILL.md").write_text("x")
            names = list_skill_names(root)
            self.assertEqual(names, ["go", "loop"])

    def test_sync_copy_mode(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "central"
            dst = td / "tool"
            (src / "skills" / "go").mkdir(parents=True)
            (src / "skills" / "go" / "SKILL.md").write_text("go")
            mode = sync_plugin_root(src, dst, prefer_symlink=False)
            self.assertEqual(mode, "copy")
            self.assertTrue((dst / "skills" / "go" / "SKILL.md").is_file())
            self.assertFalse(dst.is_symlink())
```

- [ ] **Step 2: Implement**

```python
# scripts/_lib/plugin_sync.py
from __future__ import annotations

import os
import shutil
from pathlib import Path


def list_skill_names(central_root: Path) -> list[str]:
    skills = Path(central_root) / "skills"
    if not skills.is_dir():
        return []
    names = []
    for child in sorted(skills.iterdir()):
        if child.is_dir() and (child / "SKILL.md").is_file():
            names.append(child.name)
    return names


def sync_plugin_root(src: Path, dst: Path, prefer_symlink: bool = True) -> str:
    """Replace dst with src contents. Returns 'symlink' or 'copy'."""
    src = Path(src).resolve()
    dst = Path(dst)
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if prefer_symlink:
        try:
            os.symlink(src, dst, target_is_directory=True)
            return "symlink"
        except OSError:
            pass
    shutil.copytree(src, dst)
    return "copy"
```

- [ ] **Step 3: pytest PASS + commit**

```bash
python3 -m pytest tests/test_plugin_sync.py -v
git add scripts/_lib/plugin_sync.py tests/test_plugin_sync.py
git commit -m "feat(install): add plugin_sync symlink-or-copy helper"
```

---

### Task 5: Claude registry scripts (TDD)

**Files:**
- Create: `scripts/register_claude_marketplace.py`
- Create: `scripts/register_claude_plugin.py`
- Create: `tests/test_register_claude_plugin.py`
- Pattern: mirror `scripts/register_zcode_plugin.py` + `_lib/json_io.py`

- [ ] **Step 1: Failing test for plugin upsert/remove**

```python
# tests/test_register_claude_plugin.py
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from register_claude_plugin import upsert_plugin, remove_plugin


class TestRegisterClaudePlugin(unittest.TestCase):
    def test_upsert_and_remove(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "installed_plugins.json"
            path.write_text(json.dumps({"version": 2, "plugins": {}}), encoding="utf-8")
            upsert_plugin(
                path,
                plugin_key="loopengine@loopengine-local",
                install_path="/tmp/le",
                version="1.3.2",
            )
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("loopengine@loopengine-local", data["plugins"])
            rec = data["plugins"]["loopengine@loopengine-local"][0]
            self.assertEqual(rec["installPath"], "/tmp/le")
            self.assertEqual(rec["scope"], "user")
            remove_plugin(path, "loopengine@loopengine-local")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("loopengine@loopengine-local", data["plugins"])
```

- [ ] **Step 2: Implement `register_claude_plugin.py`**

Export `upsert_plugin` / `remove_plugin` for tests; CLI:  
`python register_claude_plugin.py <installed_plugins.json> upsert|remove <plugin_key> [install_path] [version]`

Use `_lib.json_io.read_json` / `write_json`. Record shape:

```python
{
  "scope": "user",
  "installPath": install_path,
  "version": version,
  "installedAt": iso_now,
  "lastUpdated": iso_now,
}
```

If key exists, update first list element’s `installPath`/`version`/`lastUpdated`.

- [ ] **Step 3: Implement `register_claude_marketplace.py`**

CLI: `python register_claude_marketplace.py <known_marketplaces.json> <marketplace_id> <install_location>`

Upsert dict entry (Claude schema is object map, not ZCode list). Ensure marketplace directory exists with rendered `marketplace.json` (caller may copy).

- [ ] **Step 4: pytest + commit**

```bash
python3 -m pytest tests/test_register_claude_plugin.py -v
git add scripts/register_claude_*.py tests/test_register_claude_plugin.py
git commit -m "feat(install): Claude marketplace + installed_plugins registration"
```

---

### Task 6: P1 — Build central package in `_common.sh`

**Files:**
- Modify: `scripts/install/_common.sh`
- Modify: `install.sh` (expose version path vars)

- [ ] **Step 1: Add globals**

```bash
COMMON_CENTRAL_ROOT="$HOME/.loopengine/plugins/loopengine/$COMMON_VERSION"
COMMON_MANIFEST_FILE="$HOME/.loopengine/install-manifest.json"
```

- [ ] **Step 2: Add `common_build_central_package`**

After render_plugins + having `$COMMON_WORK`:

1. `rm -rf` then `mkdir -p "$COMMON_CENTRAL_ROOT"`
2. Copy `skills/`, `hooks/`, `commands/` from `$COMMON_WORK`
3. Copy rendered manifests into `.claude-plugin/`, `.zcode-plugin/`, `.cursor-plugin/`, `.codex-plugin/` as applicable
4. Copy `AGENTS.md`, `README.md`
5. Echo skill count

- [ ] **Step 3: Wire into main install path** before per-tool deploy; commit.

```bash
git add scripts/install/_common.sh install.sh
git commit -m "feat(install): build versioned central plugin package"
```

---

### Task 7: P1 — Cursor Adapter (no flat copy) + legacy cleanup

**Files:**
- Modify: `scripts/install/_common.sh` (`common_copy_skills_for`, deploy Cursor branch)
- Create: `tests/test_cursor_no_flat_deploy.py` (document contract; or bash-level fixture if extracting is hard)

- [ ] **Step 1: Replace Cursor branch in `common_copy_skills_for`**

For label `Cursor`:

- **Do not** copy into `dirname(root_dir)` flat skills.
- Instead: `python scripts/_lib` via small CLI or inline call:

```bash
# preferred
python "$COMMON_SCRIPT_DIR/scripts/_lib_plugin_sync_cli.py" \
  sync "$COMMON_CENTRAL_ROOT" "$HOME/.cursor/plugins/local/loopengine"
```

Or embed in `_common.sh`:

```bash
common_sync_cursor_plugin() {
  local dst="$HOME/.cursor/plugins/local/loopengine"
  python - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "$COMMON_SCRIPT_DIR/scripts")
from _lib.plugin_sync import sync_plugin_root, list_skill_names
mode = sync_plugin_root(Path("$COMMON_CENTRAL_ROOT"), Path("$dst"), prefer_symlink=True)
print(mode)
PY
}
```

- [ ] **Step 2: `common_cleanup_cursor_flat_skills`**

```bash
# for each name in skill_names from central package:
#   rm -rf "$HOME/.cursor/skills/$name"
# also: if "$HOME/.cursor/skills/loopengine" exists and has no skills/ subdir with SKILL.md children matching, remove or leave hooks-only dir per spec (remove whole loopengine under skills/)
```

- [ ] **Step 3: Manual smoke on macOS**

```bash
bash install.sh --only=cursor --force
test -d "$HOME/.cursor/plugins/local/loopengine/skills/go"
test ! -d "$HOME/.cursor/skills/go"   # after cleanup
```

- [ ] **Step 4: Commit**

```bash
git add scripts/install/_common.sh
git commit -m "feat(install): Cursor adapter uses plugins/local, remove flat skills"
```

---

### Task 8: P2 — Route all tools through central package sync

**Files:**
- Modify: `scripts/install/_common.sh` (`common_deploy_to_9_tools`, copy_skills/hooks)

- [ ] **Step 1: Change deploy model**

For each tool root (ZCode, Claude, Codex, …):

1. `sync_plugin_root(CENTRAL, plugin_root)` (copy preferred for non-Cursor if symlink confusing; Cursor symlink OK)
2. Ensure tool-specific overlay files from rendered dir still present inside synced tree (if sync replaces whole tree, re-copy manifests after sync OR include manifests inside central package — prefer **manifests already in central** from Task 6)
3. Stop separately copying skills into `root/skills` from WORK when central already has them

- [ ] **Step 2: Claude activate**

After Claude sync:

```bash
python "$COMMON_SCRIPT_DIR/scripts/register_claude_marketplace.py" \
  "$HOME/.claude/plugins/known_marketplaces.json" \
  loopengine-local \
  "$HOME/.claude/plugins/marketplaces/loopengine-local"

python "$COMMON_SCRIPT_DIR/scripts/register_claude_plugin.py" \
  "$HOME/.claude/plugins/installed_plugins.json" \
  upsert \
  loopengine@loopengine-local \
  "$CLAUDE_INSTALL_PATH" \
  "$COMMON_VERSION"
```

`$CLAUDE_INSTALL_PATH` = path locked in Task 2 spike.

Ensure marketplace dir contains marketplace.json (copy from central `.claude-plugin/marketplace.json`).

- [ ] **Step 3: Write manifest at end of successful install**

Call `save_manifest` via Python with all components + skill_names + extras (redline targets, mcp keys).

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(install): sync all tool roots from central package + Claude registry"
```

---

### Task 9: Uninstall + CLI flags

**Files:**
- Create: `scripts/uninstall_loopengine.py`
- Modify: `install.sh`, `install.ps1`, `scripts/install/_common.sh`
- Create: `tests/test_uninstall_loopengine.py`

- [ ] **Step 1: Failing test — uninstall removes plugin_root and registry key from temp fixtures**

Use tempfile copies of manifest + fake plugin dirs + fake installed_plugins.json; run uninstall; assert paths gone and key removed.

- [ ] **Step 2: Implement `uninstall_loopengine.py`**

Behavior:

1. Load `~/.loopengine/install-manifest.json` (if missing → exit 2 with message to run heuristic or reinstall once)
2. For each `components.*.plugin_root` → delete
3. Delete `central_root` and parent empty version dirs as needed
4. Cursor: delete flat `skill_names` under `~/.cursor/skills/`
5. Claude: `remove_plugin` + remove marketplace id if dedicated
6. ZCode: disable enabledPlugins key if present (optional call existing register script inverse)
7. Strip redline sentinels via existing inject inverse if available; else document manual
8. MCP: remove only `extras.mcp.keys` from cursor mcp.json
9. Delete manifest + `.installed_version`

- [ ] **Step 3: Wire flags**

```bash
# install.sh
--uninstall) COMMON_UNINSTALL=true ;;
--upgrade)   COMMON_FORCE=true ;;  # or dedicated path that always rebuilds central
```

If `COMMON_UNINSTALL`: call python uninstall and exit 0 (skip clone).

PowerShell: `-Uninstall`, `-Upgrade`.

- [ ] **Step 4: pytest + manual uninstall smoke + commit**

```bash
python3 -m pytest tests/test_uninstall_loopengine.py -v
git commit -m "feat(install): add manifest-driven uninstall and CLI flags"
```

---

### Task 10: P3 — Docs + audit + self-check

**Files:**
- Modify: `docs/INSTALL.md`, `README.md`
- Modify: `scripts/install/_common.sh` dry-run summary + post-install verify message
- Modify: `scripts/audit_tools.py` (add registry check if cheap)

- [ ] **Step 1: Update INSTALL verification block**

Replace orch/flat checks with:

```bash
ls ~/.cursor/plugins/local/loopengine/skills/go
test ! -d ~/.cursor/skills/go
python3 -c "import json;print('loopengine' in json.load(open('$HOME/.claude/plugins/installed_plugins.json'))['plugins'])"
bash install.sh --uninstall   # document only; don't run in CI casually
```

- [ ] **Step 2: README project structure** — Cursor plugins/local, no flat

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(install): document plugin-shaped install and uninstall"
```

---

### Task 11: Integration gate (human)

- [ ] **Step 1: Full install on macOS** (`--all` or detect)

- [ ] **Step 2: Confirm Cursor + Claude + ZCode sessions load `go`/`loop`**

- [ ] **Step 3: Upgrade path** — bump `COMMON_VERSION` in a local test or `--force`; confirm old central version removed

- [ ] **Step 4: Uninstall** — confirm clean; reinstall once

- [ ] **Step 5: Run full unittest**

```bash
python3 -m pytest tests/ -q
```

Expected: no new failures in install-related tests; pre-existing sandbox-only failures noted in report.

---

## Execution notes

1. **Do not skip P0.** Flat-skill removal without Cursor spike = user-visible breakage.  
2. Prefer shared Python helpers over duplicating JSON logic in bash/ps1.  
3. Heuristic uninstall (no manifest) is **out of P1**; if needed, add Task 9b after P2.  
4. Previous session’s orch→go doc fixes and untracked `skills/go/references/*` assets are **orthogonal**; keep on separate commits if still uncommitted.

## Plan approval

After this plan is written, ask the user whether to proceed with `/executing-plans` or `subagent-driven-development` starting at Task 0/1.

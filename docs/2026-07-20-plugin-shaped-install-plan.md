# Plugin-Shaped Install v2.3 Implementation Plan

> **Storage (D13 · design v2.3):** No symlinks. Central `current` is a pointer file.
> Each tool gets its own real `copy-tree`. Cursor is **plugin-only** (no LE flat skills).
> ZCode uses official plugin cache (not `~/.zcode/skills/loopengine`).
> Spec truth: `docs/2026-07-20-plugin-shaped-install-design-v2.md` (v2.3).

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Bash/PS install with a single `install.py` that deploys LoopEngine as official-style plugins (skills/hooks/MCP/AGENTS) with install/upgrade/uninstall for Tier-1 agents first.

**Architecture:** Central package under `~/.loopengine/plugins/loopengine/`; per-tool Adapters implement four methods (`sync_plugin`, `activate_registry`, `merge_mcp`, `inject_agents`); `install-manifest.json` records reversible `operations[]`. User CLI is only install / uninstall / upgrade(alias).

**Tech Stack:** Python ≥3.10 (stdlib + existing `scripts/_lib/json_io.py`), unittest, JSON Schema (stdlib `json` + lightweight validation or `jsonschema` if already available—prefer stdlib subset checks in tests).

**Spec:** `docs/2026-07-20-plugin-shaped-install-design-v2.md` (Approved · **v2.3**)

**Replaces:** Previous Bash-centric plan content in this file.

**Implementation status (2026-07-21):** Tier-1 Python install landed (`install.py` + `loopengine_install`). Legacy `install.sh`/`install.ps1` removed. Remaining: P3 doctor/repair productization; optional Tier-2/3 polish.

---

## File map

| Path | Responsibility |
|------|----------------|
| `install.py` | Sole user entry: version check, clone/update, dispatch CLI |
| `scripts/loopengine_install/__init__.py` | Package marker |
| `scripts/loopengine_install/__main__.py` | `python -m loopengine_install` |
| `scripts/loopengine_install/cli.py` | Argparse: install/uninstall/upgrade + flags |
| `scripts/loopengine_install/lifecycle.py` | Orchestrate package + adapters + manifest |
| `scripts/loopengine_install/ops.py` | Operation apply/revert, manifest load/save/validate |
| `scripts/loopengine_install/package.py` | Build central package, switch `current` |
| `scripts/loopengine_install/detect.py` | Detect installed agents + MCP binaries |
| `scripts/loopengine_install/adapters/base.py` | Adapter ABC + Operation builders |
| `scripts/loopengine_install/adapters/cursor.py` | Tier-1 Cursor |
| `scripts/loopengine_install/adapters/claude.py` | Tier-1 Claude |
| `scripts/loopengine_install/adapters/zcode.py` | Tier-1 ZCode |
| `scripts/loopengine_install/adapters/codex.py` / `gemini.py` | Tier-2 |
| `scripts/loopengine_install/adapters/copilot.py` / `pi.py` | Tier-3 |
| `schemas/install-manifest.schema.json` | Manifest schema |
| `docs/spikes/2026-07-20-cursor-plugins-local.md` | P0 Cursor spike log |
| `docs/spikes/2026-07-20-claude-installed-plugins.md` | P0 Claude spike log |
| `tests/test_loopengine_install_ops.py` | ops + manifest |
| `tests/test_loopengine_install_cursor.py` | Cursor adapter (tmp dirs) |
| `tests/test_loopengine_install_zcode.py` | ZCode official cache + marketplace |
| `tests/test_loopengine_install_check.py` | `install --check` mini-doctor |
| `tests/test_loopengine_install_cli.py` / `package.py` / `tier23.py` | CLI / central package / Tier-2·3 |
| Delete after P2 | ~~`install.sh`, `install.ps1`, `scripts/install/*.sh`~~ **done** |

**Reuse (call, do not fork blindly):** `scripts/render_plugins.py`, `scripts/merge_mcp_config.py`, `scripts/inject_rules.py`, `scripts/_lib/json_io.py`. Legacy `register_zcode_*.py` / `install_zcode_plugin.py` are **deprecated emergency CLI**; canonical logic lives in `loopengine_install/`.

**Locked plan defaults (spec §14):**

- Claude `installPath`: `~/.claude/plugins/cache/loopengine-local/loopengine/<version>/` (adjust only if P0 proves otherwise).
- Central package: versioned dir + `current` as **pointer text file** (never symlink; D13).
- Each tool: independent **copy-tree** (`symlinks=False`); Cursor is **plugin-only** (no LE flat).
- Helpers: **call** existing scripts as libraries where possible; relocate into package only if import path is painful.

---

### Task 0: Mark approved + branch

**Files:**
- Modify: `docs/2026-07-20-plugin-shaped-install-design-v2.md` (status—already Approved if committed)
- Create branch: `go-plugin-shaped-install-py`

- [x] **Step 1: Confirm spec header says Approved**

- [x] **Step 2: Create branch**

```bash
git checkout -b go-plugin-shaped-install-py
git status
```

- [x] **Step 3: Commit plan + approved spec if dirty**

```bash
git add docs/2026-07-20-plugin-shaped-install-design-v2.md docs/2026-07-20-plugin-shaped-install-plan.md
git commit -m "docs: approve plugin-shaped install v2.1 spec and Python plan"
```

---

### Task 1: P0 Spike — Cursor `plugins/local`

**Files:**
- Create: `docs/spikes/2026-07-20-cursor-plugins-local.md`

- [ ] **Step 1: Build minimal plugin tree**

```bash
SPIKE="$HOME/.cursor/plugins/local/loopengine-spike"
rm -rf "$SPIKE"
mkdir -p "$SPIKE/.cursor-plugin" "$SPIKE/skills/using-loopengine"
printf '%s\n' '{"name":"loopengine-spike","version":"0.0.1","description":"P0 spike"}' \
  > "$SPIKE/.cursor-plugin/plugin.json"
cp skills/using-loopengine/SKILL.md "$SPIKE/skills/using-loopengine/SKILL.md"
# If hooks-cursor.json exists, copy a minimal hooks stub into spike
```

- [ ] **Step 2: Manual verify in Cursor**

New Agent chat: ask to load `using-loopengine` and summarize LoopEngine cores.  
Record PASS/FAIL, Cursor version, date in spike doc.

- [ ] **Step 3: Gate**

If FAIL → **stop entire plan**; report to user; do not remove flat deploy.  
If PASS → commit spike doc.

```bash
git add docs/spikes/2026-07-20-cursor-plugins-local.md
git commit -m "docs(spike): Cursor plugins/local loads skills (P0)"
```

---

### Task 2: P0 Spike — Claude `installed_plugins.json`

**Files:**
- Create: `docs/spikes/2026-07-20-claude-installed-plugins.md`

- [ ] **Step 1: Inspect an existing official plugin entry**

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude/plugins/installed_plugins.json"
print(p.exists(), p)
if p.exists():
    data = json.loads(p.read_text())
    print(list(data.get("plugins", data).keys())[:5] if isinstance(data, dict) else type(data))
PY
```

- [ ] **Step 2: Write minimal local marketplace + one LE test key**

Follow Claude’s on-disk schema from Step 1 (do not invent fields). Document exact JSON shape in the spike file. Prefer:

- marketplace id: `loopengine-local`
- plugin key: `loopengine@loopengine-local`
- installPath under `~/.claude/plugins/cache/loopengine-local/loopengine/<ver>/` with one skill copied

- [ ] **Step 3: Verify Claude Code sees the plugin** (restart / new session if needed)

Record PASS/FAIL. If FAIL, try alternate installPath (`~/.claude/skills/loopengine`) and document winner.

- [ ] **Step 4: Gate + commit**

```bash
git add docs/spikes/2026-07-20-claude-installed-plugins.md
git commit -m "docs(spike): Claude installed_plugins local registration (P0)"
```

---

### Task 3: Manifest schema + ops (TDD)

**Files:**
- Create: `schemas/install-manifest.schema.json`
- Create: `scripts/loopengine_install/__init__.py`
- Create: `scripts/loopengine_install/ops.py`
- Create: `tests/test_loopengine_install_ops.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_loopengine_install_ops.py
import json
import tempfile
import unittest
from pathlib import Path

from loopengine_install.ops import (
    Manifest,
    Operation,
    apply_operation,
    revert_operation,
    load_manifest,
    save_manifest,
    validate_manifest,
)


class OpsTest(unittest.TestCase):
    def test_link_or_copy_and_revert(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src, dst = td / "src", td / "dst"
            src.mkdir()
            (src / "a.txt").write_text("x")
            op = Operation(
                id="op-1",
                kind="link-or-copy",
                ownership="managed",
                source=str(src),
                destination=str(dst),
            )
            apply_operation(op)
            self.assertTrue(dst.exists())
            revert_operation(op)
            self.assertFalse(dst.exists())

    def test_manifest_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "install-manifest.json"
            m = Manifest(
                schema_version=2,
                product="loopengine",
                version="1.3.2",
                installed_at="2026-07-20T00:00:00Z",
                central_root="/tmp/central",
                skill_names=["go", "loop"],
                components={},
                operations=[],
            )
            save_manifest(path, m)
            m2 = load_manifest(path)
            self.assertEqual(m2.version, "1.3.2")
            validate_manifest(m2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run — expect FAIL (import error)**

```bash
cd "$(git rev-parse --show-toplevel)"
PYTHONPATH=scripts python3 -m unittest tests.test_loopengine_install_ops -v
```

- [ ] **Step 3: Implement schema + ops**

`schemas/install-manifest.schema.json` — require `schema_version`, `product`, `version`, `central_root`, `skill_names`, `operations` (array of objects with `id`, `kind`, `ownership`).

`ops.py` — dataclasses; `copy-tree` always `shutil.copytree(..., symlinks=False)` (legacy `link-or-copy` is an alias); `merge-json` / `registry-write` / `inject-markers` applied by adapters.

Minimal `validate_manifest`: check required fields + `kind in ALLOWED_KINDS`.

- [ ] **Step 4: Run tests — expect PASS**

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_loopengine_install_ops -v
```

- [ ] **Step 5: Commit**

```bash
git add schemas/install-manifest.schema.json scripts/loopengine_install/ tests/test_loopengine_install_ops.py
git commit -m "feat(install): manifest ops apply/revert foundation"
```

---

### Task 4: Central package builder

**Files:**
- Create: `scripts/loopengine_install/package.py`
- Create: `tests/test_loopengine_install_package.py`
- Reuse: `scripts/render_plugins.py`

- [ ] **Step 1: Failing test** — `build_central_package(repo_root, home, version)` creates `home/plugins/loopengine/<ver>/skills` with at least one skill and rendered `.cursor-plugin/plugin.json`.

- [ ] **Step 2: Implement `package.py`**

```python
# Sketch — fill using render_plugins + copy skills/hooks/commands/AGENTS.md
def build_central_package(repo_root: Path, loopengine_home: Path, version: str) -> Path:
    dest = loopengine_home / "plugins" / "loopengine" / version
    # copy skills, hooks, commands; run render_plugins into dest overlays
    # write/update `current` pointer file (never symlink; D13)
    return dest
```

- [ ] **Step 3: Tests PASS + commit**

```bash
git commit -m "feat(install): build central plugin package"
```

---

### Task 5: CLI + install.py bootstrap

**Files:**
- Create: `install.py`
- Create: `scripts/loopengine_install/cli.py`
- Create: `scripts/loopengine_install/__main__.py`
- Create: `scripts/loopengine_install/detect.py`
- Create: `tests/test_loopengine_install_cli.py`

- [ ] **Step 1: CLI tests** — parse `[]` → command install; `["uninstall"]`; `["--dry-run","--json"]`; `["--only=cursor,zcode"]`.

- [ ] **Step 2: Implement argparse in `cli.py`**

Commands: `install` (default), `uninstall`, `upgrade`→install.  
Flags: `--dry-run`, `--json`, `--force`, `--all`, `--only`, `--check` (optional stub returning 0).

- [ ] **Step 3: `install.py`**

```python
#!/usr/bin/env python3
"""LoopEngine one-click installer entry (macOS / Windows / Linux)."""
import sys
from pathlib import Path

MIN = (3, 10)

def main(argv=None):
    if sys.version_info < MIN:
        print("LoopEngine requires Python >= 3.10", file=sys.stderr)
        return 1
    # If running from curl pipe: download/clone repo to ~/.loopengine/src then dispatch
    # If __file__ is inside a git checkout: use that repo root
    repo = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo / "scripts"))
    from loopengine_install.cli import main as cli_main
    return cli_main(argv)

if __name__ == "__main__":
    raise SystemExit(main())
```

Implement clone path carefully: when stdin is a pipe, `__file__` may be `<stdin>` — detect and clone `https://github.com/tsfdsong/loop_engineering.git` to `~/.loopengine/src`.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(install): install.py CLI entry and detect stubs"
```

---

### Task 6: Cursor Adapter four-pack (tracer bullet)

**Files:**
- Create: `scripts/loopengine_install/adapters/base.py`
- Create: `scripts/loopengine_install/adapters/cursor.py`
- Create: `scripts/loopengine_install/adapters/__init__.py`
- Create: `tests/test_loopengine_install_cursor.py`
- Reuse: `merge_mcp_config.merge_cursor`, `inject_rules`

- [ ] **Step 1: Failing tests with tmp HOME**

Cover: `sync_plugin` creates `plugins/local/loopengine`; does **not** write flat `skills/go`; `merge_mcp` adds jcodemunch key; `inject_agents` writes LOOPENGINE markers; uninstall reverts.

- [ ] **Step 2: Implement Cursor adapter**

```python
class CursorAdapter:
    name = "cursor"
    def sync_plugin(self, central: Path, dry_run=False) -> list[Operation]: ...
    def activate_registry(self, ...) -> list[Operation]:
        return []  # local folder discovery; no registry file unless spike found one
    def merge_mcp(self, ...) -> list[Operation]: ...
    def inject_agents(self, ...) -> list[Operation]: ...
```

Also: `cleanup_flat_skills(skill_names)` as install pre-step generating `remove-path` ops or delete then record.

- [ ] **Step 3: Wire into lifecycle install `--only=cursor --dry-run`**

- [ ] **Step 4: Manual smoke on real machine (optional but recommended)**

```bash
PYTHONPATH=scripts python3 install.py install --only=cursor --dry-run --json
PYTHONPATH=scripts python3 install.py install --only=cursor
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(install): Cursor adapter four-pack + flat skill cleanup"
```

---

### Task 7: Claude Adapter (registry required)

**Files:**
- Create: `scripts/loopengine_install/adapters/claude.py`
- Create: `tests/test_loopengine_install_claude.py`
- Use shapes from P0 spike doc

- [ ] **Step 1: Tests** — write/remove `installed_plugins` key; marketplace upsert; sync to cache installPath.

- [ ] **Step 2: Implement** — mirror ZCode register scripts’ style with atomic JSON writes via `json_io`.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(install): Claude marketplace + installed_plugins adapter"
```

---

### Task 8: ZCode Adapter

**Files:**
- Create: `scripts/loopengine_install/adapters/zcode.py`
- Create: `tests/test_loopengine_install_zcode.py`
- Call: `register_zcode_marketplace`, `register_zcode_plugin`, `merge_mcp_config.merge_zcode`, `inject_rules`

- [ ] **Step 1–3:** Same TDD pattern as Cursor; ensure uninstall removes enabledPlugins entry and LE MCP keys only.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(install): ZCode adapter four-pack"
```

---

### Task 9: Lifecycle install / uninstall

**Files:**
- Create: `scripts/loopengine_install/lifecycle.py`
- Create: `tests/test_loopengine_install_lifecycle.py`

- [ ] **Step 1: Tests** — temp home: install cursor+zcode dry fixtures → manifest has operations → uninstall empties plugin roots and clears managed keys.

- [ ] **Step 2: Implement**

```text
install:
  detect targets
  maybe heuristic cleanup if no manifest
  build_central_package
  for each adapter: four-pack; collect ops
  save_manifest
uninstall:
  load_manifest; reverse ops; delete manifest (and current package)
upgrade:
  same as install with force semantics for version bump
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(install): lifecycle install/uninstall with manifest"
```

---

### Task 10: Tier-2 / Tier-3 adapters

**Files:**
- Create: `adapters/codex.py`, `gemini.py`, `copilot.py`, `pi.py`
- Tests: lightweight tmp-dir sync + inject only where applicable

- [ ] **Step 1: Implement degraded four-pack** (registry no-op where N/A).

- [ ] **Step 2: Register in detect + adapter registry map**.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(install): Tier-2/3 adapters (semi-plugin / inject)"
```

---

### Task 11: Retire Shell install + docs

**Files:**
- Delete: `install.sh`, `install.ps1`, `scripts/install/_common.sh`, `scripts/install/macos.sh`, `scripts/install/linux.sh`, `scripts/install/windows.sh`
- Modify: `docs/INSTALL.md`, `README.md`, `CLAUDE.md` (install one-liner)
- Modify: `scripts/audit_tools.py` — note new paths / fail if old flat cursor skills present for LE names

- [ ] **Step 1: Update INSTALL.md**

Document:

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
python3 install.py uninstall
```

Tier table (one section). Fallback `-o install.py`. Python ≥3.10.

- [ ] **Step 2: Delete shell assets; fix any CI/docs references**

```bash
rg -n 'install\.sh|install\.ps1|_common\.sh' --glob '!docs/2026-07-20-plugin-shaped-install-design.md' .
```

- [ ] **Step 3: Full unittest**

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_loopengine_install*.py' -v
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(install): retire Bash/PS install; document install.py"
```

---

### Task 12: P3 optional (non-blocking)

- [ ] `--check` compares manifest ops vs disk (mini-doctor)
- [ ] `audit_tools.py` registry dimension for Claude/ZCode/Cursor paths
- [ ] Commit if done: `feat(install): install --check and audit registry dimension`

---

## Execution notes

- **Stop** if Task 1 or 2 FAIL.
- Prefer `PYTHONPATH=scripts` in all commands until/unless a tiny `pyproject.toml` is added (out of scope unless needed).
- Do not add `plan`/`doctor`/`repair`/`list` subcommands before Task 12.
- Windows: confirm `copy-tree` (no symlink) works once before declaring Task 11 done.

## Self-review checklist (author)

- [x] Spec §0 acceptance mapped to Tasks 6–11  
- [x] No Bash install business logic remaining after Task 11  
- [x] Tier-1 before Tier-2/3  
- [x] Four-pack includes MCP + AGENTS  
- [x] P0 gates explicit  

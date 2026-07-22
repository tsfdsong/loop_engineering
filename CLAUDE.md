# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

LoopEngine is a **meta-engineering framework for AI coding assistants** — not a traditional app. It's a collection of 32 skills, slash commands, hooks, and install scripts that gets injected into Claude Code, Cursor, ZCode, Codex, Gemini, Copilot, and Pi. There is no build step, no server to start, no app to run.

## Development commands

```bash
# Run all tests (pytest, project root)
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_loopengine_install_cli.py -v

# Run a single test function
python3 -m pytest tests/test_smart_commit.py::TestSmartCommit::test_xxx -v

# Audit tool deployment (6 dimensions: A-F)
python3 scripts/audit_tools.py --verbose
python3 scripts/audit_tools.py --json              # CI-friendly
python3 scripts/audit_tools.py --tool claude-code   # single-tool only

# Check install without side effects
python3 install.py install --dry-run
python3 install.py install --check --json

# Render plugin manifests for all supported tools
python3 scripts/render_plugins.py
```

`pytest.ini` sets `pythonpath = scripts` so `scripts/loopengine_install/` is importable as `loopengine_install`.

## Architecture

```
User request  →  Slash Command (/loop, /go, /audit, /git-commit)
                     │
                     ▼
              Skill (skills/<name>/SKILL.md + references/)
                     │
                     ▼
              AI tool executes the skill's methodology
                     │
                     ▼
              Hooks (SessionStart / PostToolUse / Stop) enforce guardrails
```

### Skills (`skills/`)

Each skill is a directory with a `SKILL.md` (YAML frontmatter + markdown body) defining a methodology an AI agent follows. Key structural skills:

- **`loop`** — thin closed-loop executor: goal + acceptance → code ↔ gate ↔ self-heal → deliver
- **`go`** — multi-tool orchestrator: family-first routing, worktree isolation, DAG parallelism
- **`supervisor`** — monitors loop/go execution, R1–R4 progressive intervention
- **`shared/`** — cross-skill references (e.g. `loop-execution-contract.md`) and helper scripts

Skills are NOT standalone executables — the AI tool reads them as context and follows them as instructions.

### Commands (`commands/`)

Slash-command definitions (markdown files with YAML frontmatter). Each routes to a skill:
- `/loop` → `skills/loop/SKILL.md`
- `/go` → `skills/go/SKILL.md`
- `/audit` → `python3 scripts/audit_tools.py`
- `/git-commit` → smart commit with conventional-commits enforcement

### Hooks (`hooks/`)

Shell scripts that run at session lifecycle boundaries:
- **SessionStart** — injects AGENTS.md context + tier hint + session state init
- **PostToolUse** — evidence collector (tracks code changes for verify gate)
- **Stop** — verify gate (blocks session end if code changes lack verdict.json)

### Install system (`scripts/loopengine_install/`)

Python package with per-tool adapters (`adapters/claude.py`, `cursor.py`, `zcode.py`, etc.). Each adapter knows that tool's config paths, hook formats, and rule injection mechanism. The common logic lives in `lifecycle.py` / `ops.py` / `package.py`.

### Rule injection

`AGENTS.md` is the single source of truth for AI behavior rules (5 Core Instincts + 7 Verbal Rules). The install system injects these rules (or tool-specific equivalents) into each supported tool's config directory using LOOPENGINE-MANAGED markers (`<!-- BEGIN/END LOOPENGINE-MANAGED ... -->`). `CLAUDE.md` (this file) is project-level only and is NOT injected.

## Key paths

| Path | Role |
|------|------|
| `AGENTS.md` | AI behavior rules — single source of truth |
| `CLAUDE.md` | This file — project-level dev guidance only |
| `install.py` | Entry point: curl-pipe or local install |
| `skills/` | 32 skill definitions |
| `commands/` | 4 slash-command routers |
| `hooks/` | Session lifecycle enforcement scripts |
| `scripts/loopengine_install/` | Install backend (CLI + adapters) |
| `scripts/_lib/` | Shared utilities (JSON I/O, redline markers) |
| `tests/` | pytest suite (install logic + go contracts + tools) |
| `schemas/` | JSON schemas (install manifest) |
| `.plugin-template.json` | Shared plugin manifest fields |
| `.loopengine.yaml` | Optional runtime config (fallback chain, supervisor) |

## Working with AGENTS.md

When editing `AGENTS.md`:
- H2 headings must stay in sync with `scripts/_lib/redline_markers.txt`
- Content within `<!-- BEGIN/END LOOPENGINE-MANAGED ... -->` markers is auto-injected into installed tools
- Red line rules must reference their source skill via `skills/<name>/SKILL.md` (single-source-of-truth principle)

## Testing philosophy

Tests cover the install pipeline and contract compliance — not skill execution (skills are AI-interpreted at runtime). Key test areas:
- CLI argument parsing (`test_loopengine_install_cli.py`)
- Per-tool adapter correctness (`test_loopengine_install_*.py`)
- `/go` worker contract and golden traces (`test_go_worker_contract.py`, `test_go_golden_traces.py`)
- Smart commit logic (`test_smart_commit.py`)
- MCP config merging (`test_merge_mcp_config.py`)

## Commit conventions

Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`. The `/git-commit` command enforces this.

"""Shared helpers for adapters: MCP merge, AGENTS inject, skill listing."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from _lib import json_io
from inject_rules import inject_block
from loopengine_install.ops import Operation, apply_operation


def list_skill_names(central_or_repo: Path) -> list[str]:
    skills = central_or_repo / "skills"
    if not skills.is_dir():
        return []
    names = []
    for p in sorted(skills.iterdir()):
        if p.is_dir() and (p / "SKILL.md").is_file() and not p.name.startswith("."):
            names.append(p.name)
    return names


def copy_tree_op(
    op_id: str, source: Path, destination: Path, dry_run: bool
) -> Operation:
    """Record + apply a real copy-tree (never symlink; D13)."""
    op = Operation(
        id=op_id,
        kind="copy-tree",
        ownership="managed",
        source=str(source),
        destination=str(destination),
    )
    if not dry_run:
        apply_operation(op)
    return op


# Back-compat alias for older call sites / tests
link_or_copy_op = copy_tree_op


def cleanup_flat_skills(
    skills_root: Path, skill_names: list[str], dry_run: bool, prefix: str
) -> list[Operation]:
    """Remove LoopEngine skill dirs from a flat skills root; record as managed removals via destination-only ops."""
    ops: list[Operation] = []
    for i, name in enumerate(skill_names):
        path = skills_root / name
        if not path.exists():
            continue
        op = Operation(
            id=f"{prefix}-rm-flat-{i:03d}-{name}",
            kind="copy-tree",
            ownership="managed",
            source=str(path),  # unused on revert after delete; we only delete now
            destination=str(path),
        )
        if not dry_run:
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
        # For uninstall we should NOT restore flat skills; mark ownership so revert
        # of copy-tree would delete destination again — skip recording delete-only
        # as reversible install ops. Flat cleanup is one-way migration.
        _ = op
    # Also remove semi-finished ~/.cursor/skills/loopengine if empty-ish hooks-only
    semi = skills_root / "loopengine"
    if semi.exists() and not dry_run:
        shutil.rmtree(semi)
    return ops


def merge_json_keys(
    op_id: str,
    destination: Path,
    keys: list[str],
    mutator,
    dry_run: bool,
) -> Operation:
    """Apply mutator(data)->data, write JSON; op records merge_keys for uninstall."""
    op = Operation(
        id=op_id,
        kind="merge-json",
        ownership="managed",
        destination=str(destination),
        merge_keys=keys,
    )
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = json_io.read_json(str(destination))
        data = mutator(data)
        json_io.atomic_write_json(str(destination), data)
    return op


def revert_merge_json(op: Operation) -> None:
    if not op.destination or not op.merge_keys:
        return
    path = Path(op.destination).expanduser()
    if not path.is_file():
        return
    data = json_io.read_json(str(path))
    # Try cursor mcpServers and zcode mcp.servers
    for key in op.merge_keys:
        if "mcpServers" in data and isinstance(data["mcpServers"], dict):
            data["mcpServers"].pop(key, None)
        servers = data.get("mcp", {}).get("servers") if isinstance(data.get("mcp"), dict) else None
        if isinstance(servers, dict):
            servers.pop(key, None)
    json_io.atomic_write_json(str(path), data)


def extract_redline_blocks(agents_md: Path, markers_file: Path) -> dict[str, str]:
    """title/marker from redline_markers.txt → wrapped block text."""
    text = agents_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks: dict[str, str] = {}
    if not markers_file.is_file():
        return blocks
    for raw in markers_file.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "|" not in raw:
            continue
        title, marker = raw.split("|", 1)
        title, marker = title.strip(), marker.strip()
        begin = None
        for i, line in enumerate(lines):
            if re.search(rf"^#+\s+.*{re.escape(title)}", line):
                begin = i
                break
        if begin is None:
            continue
        end = len(lines) - 1
        in_code = False
        for j in range(begin + 1, len(lines)):
            if re.match(r"^[ \t]*```", lines[j]):
                in_code = not in_code
                continue
            if not in_code and lines[j].startswith("## "):
                end = j - 1
                break
        body = "\n".join(lines[begin : end + 1])
        blocks[marker] = (
            f"<!-- BEGIN LOOPENGINE-MANAGED {marker} -->\n"
            f"{body}\n"
            f"<!-- END LOOPENGINE-MANAGED {marker} -->"
        )
    return blocks


def inject_agents_file(
    op_id: str,
    target: Path,
    blocks: dict[str, str],
    dry_run: bool,
) -> Operation | None:
    if not blocks:
        return None
    op = Operation(
        id=op_id,
        kind="inject-markers",
        ownership="managed",
        destination=str(target),
        payload={"markers": list(blocks.keys())},
    )
    if dry_run:
        return op
    target.parent.mkdir(parents=True, exist_ok=True)
    content = target.read_text(encoding="utf-8") if target.is_file() else ""
    for marker, block in blocks.items():
        content, _ = inject_block(content, marker, block)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)
    return op


def revert_inject_markers(op: Operation) -> None:
    if not op.destination or not op.payload:
        return
    path = Path(op.destination).expanduser()
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    markers = op.payload.get("markers") or []
    for marker in markers:
        begin = f"<!-- BEGIN LOOPENGINE-MANAGED {marker} -->"
        end = f"<!-- END LOOPENGINE-MANAGED {marker} -->"
        pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
        content = pattern.sub("", content)
    path.write_text(content, encoding="utf-8")


def write_registry_json(
    op_id: str,
    path: Path,
    key: str,
    registry: str,
    mutator,
    dry_run: bool,
) -> Operation:
    op = Operation(
        id=op_id,
        kind="registry-write",
        ownership="managed",
        destination=str(path),
        registry=registry,
        key=key,
    )
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json_io.read_json(str(path)) if path.is_file() else {}
        data = mutator(data if data else {})
        json_io.atomic_write_json(str(path), data)
    return op


def revert_registry_write(op: Operation) -> None:
    if not op.destination or not op.key:
        return
    path = Path(op.destination).expanduser()
    if not path.is_file():
        return
    data = json_io.read_json(str(path))
    # Claude: plugins map
    if isinstance(data.get("plugins"), dict) and op.key in data["plugins"]:
        data["plugins"].pop(op.key, None)
        json_io.atomic_write_json(str(path), data)
        return
    # ZCode marketplace.json plugins[] by name
    if op.registry == "zcode.marketplace.plugins" and isinstance(data.get("plugins"), list):
        data["plugins"] = [
            p
            for p in data["plugins"]
            if not (isinstance(p, dict) and p.get("name") == op.key)
        ]
        json_io.atomic_write_json(str(path), data)
        return
    # known_marketplaces top-level key (Claude)
    if op.key in data and op.registry and "marketplace" in (op.registry or ""):
        data.pop(op.key, None)
        json_io.atomic_write_json(str(path), data)
        return
    # ZCode known_marketplaces list by id
    if op.registry and "known_marketplaces" in (op.registry or ""):
        mps = data.get("marketplaces")
        if isinstance(mps, list):
            data["marketplaces"] = [
                x
                for x in mps
                if not (isinstance(x, dict) and x.get("id") == op.key)
            ]
            json_io.atomic_write_json(str(path), data)
            return
    # ZCode enabledPlugins
    enabled = data.get("plugins", {}).get("enabledPlugins")
    if isinstance(enabled, dict) and op.key in enabled:
        enabled.pop(op.key, None)
        json_io.atomic_write_json(str(path), data)

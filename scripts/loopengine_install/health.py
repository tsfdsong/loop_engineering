"""Shared install health checks for `install --check` and audit_tools."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from loopengine_install.ops import Manifest, Operation


@dataclass(frozen=True)
class HealthIssue:
    id: str
    message: str
    severity: str = "error"


def is_real_dir(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink()


def manifest_has_cursor(manifest: Manifest) -> bool:
    if "cursor" in (manifest.components or {}):
        return True
    return any(
        str(op.destination or "").endswith("plugins/local/loopengine")
        for op in manifest.operations
    )


def check_central_and_pointer(home: Path, manifest: Manifest) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    central = Path(manifest.central_root).expanduser()
    if not central.exists():
        issues.append(
            HealthIssue("central", f"central_root missing: {central}")
        )

    current = home / ".loopengine" / "plugins" / "loopengine" / "current"
    if current.is_symlink():
        issues.append(
            HealthIssue(
                "current-symlink",
                "plugins/loopengine/current is a symlink; must be pointer file (D13)",
            )
        )
    elif not current.is_file() and central.exists():
        issues.append(
            HealthIssue(
                "current-missing",
                "plugins/loopengine/current pointer file missing",
            )
        )
    return issues


def check_cursor_plugin(home: Path, manifest: Manifest) -> list[HealthIssue]:
    if not manifest_has_cursor(manifest):
        return []

    issues: list[HealthIssue] = []
    flat = home / ".cursor" / "skills"
    if flat.is_dir() and manifest.skill_names:
        leftover = [
            n
            for n in manifest.skill_names
            if (flat / n / "SKILL.md").is_file()
        ]
        if leftover:
            issues.append(
                HealthIssue(
                    "cursor-flat",
                    (
                        "LE skills still under ~/.cursor/skills "
                        f"(D3 forbids flat): {leftover[:8]}"
                    ),
                )
            )

    plugin = home / ".cursor" / "plugins" / "local" / "loopengine"
    if plugin.is_symlink():
        issues.append(
            HealthIssue(
                "cursor-symlink",
                (
                    "plugins/local/loopengine is a symlink; "
                    "D13 requires a real copy — reinstall"
                ),
            )
        )
    elif is_real_dir(plugin):
        skills_dir = plugin / "skills"
        skill_dirs = (
            list(skills_dir.glob("*/SKILL.md")) if skills_dir.is_dir() else []
        )
        if len(skill_dirs) < max(1, len(manifest.skill_names) - 1):
            issues.append(
                HealthIssue(
                    "cursor-plugin-skills",
                    (
                        f"plugin skills count low: {len(skill_dirs)} "
                        f"(expected ~{len(manifest.skill_names)})"
                    ),
                )
            )
        for rel, cid in (
            (".cursor-plugin/plugin.json", "cursor-plugin-json"),
            ("hooks/hooks.json", "cursor-hooks"),
        ):
            if not (plugin / rel).is_file():
                issues.append(
                    HealthIssue(
                        cid,
                        f"missing {rel} under plugins/local/loopengine",
                    )
                )
    return issues


def check_operation(op: Operation, home: Path) -> HealthIssue | None:
    kind = op.kind
    if kind in {"copy-tree", "link-or-copy"}:
        if not op.destination:
            return None
        dst = Path(op.destination).expanduser()
        if not dst.exists():
            return HealthIssue(op.id, f"{kind} destination missing: {dst}")
        if dst.is_symlink():
            return HealthIssue(
                op.id,
                f"{kind} destination is a symlink (D13 forbids): {dst}",
            )
        return None
    if kind == "merge-json":
        if not op.destination or not op.merge_keys:
            return None
        path = Path(op.destination).expanduser()
        if not path.is_file():
            return HealthIssue(op.id, f"merge-json file missing: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return HealthIssue(op.id, f"merge-json invalid JSON: {exc}")
        missing = []
        for key in op.merge_keys:
            in_cursor = key in (data.get("mcpServers") or {})
            servers = (data.get("mcp") or {}).get("servers")
            in_zcode = isinstance(servers, dict) and key in servers
            if isinstance(servers, list):
                in_zcode = any(
                    isinstance(x, dict) and x.get("name") == key for x in servers
                )
            if not (in_cursor or in_zcode):
                missing.append(key)
        if missing:
            return HealthIssue(op.id, f"merge-json keys missing: {missing}")
        return None
    if kind == "inject-markers":
        if not op.destination or not op.payload:
            return None
        path = Path(op.destination).expanduser()
        if not path.is_file():
            return HealthIssue(op.id, f"inject target missing: {path}")
        text = path.read_text(encoding="utf-8")
        missing = [
            m
            for m in (op.payload.get("markers") or [])
            if f"BEGIN LOOPENGINE-MANAGED {m}" not in text
        ]
        if missing:
            return HealthIssue(op.id, f"markers missing: {missing}")
        return None
    if kind == "registry-write":
        if not op.destination or not op.key:
            return None
        path = Path(op.destination).expanduser()
        if not path.is_file():
            return HealthIssue(op.id, f"registry file missing: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return HealthIssue(op.id, f"registry invalid JSON: {exc}")
        key = op.key
        plugins = data.get("plugins")
        if isinstance(plugins, dict) and key in plugins:
            return None
        if isinstance(plugins, list) and any(
            isinstance(x, dict) and x.get("name") == key for x in plugins
        ):
            return None
        if isinstance(plugins, list) and any(
            isinstance(x, dict) and x.get("id") == key for x in plugins
        ):
            return None
        if isinstance(plugins, dict):
            enabled = plugins.get("enabledPlugins")
            if isinstance(enabled, dict) and enabled.get(key) is True:
                return None
            # Claude / ZCode dict-form installed_plugins keyed by plugin id
            if key in plugins:
                return None
        if key in data:
            return None
        mps = data.get("marketplaces")
        if isinstance(mps, list) and any(
            isinstance(x, dict) and x.get("id") == key for x in mps
        ):
            return None
        return HealthIssue(op.id, f"registry key missing: {key}")
    return None


def run_health_checks(manifest: Manifest, home: Path) -> list[HealthIssue]:
    """Manifest-driven install health (shared by install --check and audit)."""
    issues: list[HealthIssue] = []
    issues.extend(check_central_and_pointer(home, manifest))
    issues.extend(check_cursor_plugin(home, manifest))
    for op in manifest.operations:
        if op.ownership != "managed":
            continue
        issue = check_operation(op, home)
        if issue:
            issues.append(issue)
    return issues


def issues_as_dicts(issues: list[HealthIssue]) -> list[dict]:
    return [{"id": i.id, "message": i.message} for i in issues]

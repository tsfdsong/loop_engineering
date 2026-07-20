"""Install / uninstall orchestration."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from loopengine_install.adapters import ALL_TOOLS, get_adapters
from loopengine_install.adapters.base import AdapterContext
from loopengine_install.adapters.helpers import list_skill_names
from loopengine_install.detect import detect_agents, detect_mcp_binaries
from loopengine_install.ops import Manifest, load_manifest, revert_operation, save_manifest
from loopengine_install.package import build_central_package, read_repo_version


def loopengine_home(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".loopengine"


def manifest_path(home: Path | None = None) -> Path:
    return loopengine_home(home) / "install-manifest.json"


def select_targets(
    *,
    home: Path,
    only: list[str] | None,
    all_tools: bool,
) -> list[str]:
    known = list(ALL_TOOLS)
    if only:
        unknown = [t for t in only if t not in known]
        if unknown:
            raise ValueError(f"unknown tools: {unknown} (known: {known})")
        return list(only)
    if all_tools:
        return list(known)
    detected = detect_agents(home)
    return [t for t in known if t in detected] or ["cursor"]


def do_install(
    *,
    repo_root: Path,
    home: Path | None = None,
    only: list[str] | None = None,
    all_tools: bool = False,
    dry_run: bool = False,
    force: bool = False,
    json_out: bool = False,
) -> dict:
    home = home or Path.home()
    le_home = loopengine_home(home)
    version = read_repo_version(repo_root)
    targets = select_targets(home=home, only=only, all_tools=all_tools)
    skill_names = list_skill_names(repo_root)
    mcp_bins = detect_mcp_binaries()

    plan = {
        "command": "install",
        "version": version,
        "targets": targets,
        "dry_run": dry_run,
        "skill_count": len(skill_names),
    }
    if dry_run:
        if json_out:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print(f"[dry-run] install v{version} → {targets}")
        return plan

    central = build_central_package(repo_root, le_home, version)
    skill_names = list_skill_names(central) or skill_names
    adapters = get_adapters(targets)
    all_ops = []
    components = {}
    ctx = AdapterContext(
        home=home,
        repo_root=repo_root,
        central=central,
        version=version,
        skill_names=skill_names,
        dry_run=False,
        mcp_bins=mcp_bins,
    )
    for adapter in adapters:
        ops = adapter.install(ctx)
        all_ops.extend(ops)
        components[adapter.name] = {
            "plugin_root": str(
                getattr(adapter, "plugin_root", lambda c: central)(ctx)
                if hasattr(adapter, "plugin_root")
                else central
            ),
            "ops": len(ops),
        }

    manifest = Manifest(
        schema_version=2,
        product="loopengine",
        version=version,
        installed_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        central_root=str(central),
        skill_names=skill_names,
        components=components,
        operations=all_ops,
    )
    save_manifest(manifest_path(home), manifest)
    plan["central_root"] = str(central)
    plan["operations"] = len(all_ops)
    plan["manifest"] = str(manifest_path(home))
    if json_out:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print(
            f"✅ LoopEngine v{version} installed → {targets} "
            f"({len(all_ops)} ops, central={central})"
        )
    return plan


def do_check(
    *,
    home: Path | None = None,
    json_out: bool = False,
) -> dict:
    """Mini-doctor: manifest exists + managed ops still match disk/registry."""
    home = home or Path.home()
    path = manifest_path(home)
    report: dict = {
        "command": "check",
        "manifest": str(path),
        "ok": True,
        "issues": [],
    }
    if not path.is_file():
        report["ok"] = False
        report["issues"].append({"id": "manifest", "message": "missing install-manifest.json"})
        _emit_check(report, json_out)
        return report

    try:
        manifest = load_manifest(path)
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["issues"].append({"id": "manifest", "message": f"invalid: {exc}"})
        _emit_check(report, json_out)
        return report

    report["version"] = manifest.version
    report["operations"] = len(manifest.operations)

    central = Path(manifest.central_root).expanduser()
    if not central.exists():
        report["ok"] = False
        report["issues"].append(
            {"id": "central", "message": f"central_root missing: {central}"}
        )

    # Flat Cursor LE skills must stay gone
    flat = home / ".cursor" / "skills"
    if flat.is_dir() and manifest.skill_names:
        leaked = [
            n
            for n in manifest.skill_names
            if (flat / n).exists()
        ]
        if leaked:
            report["ok"] = False
            report["issues"].append(
                {
                    "id": "cursor-flat",
                    "message": f"LE skills still flat under ~/.cursor/skills: {leaked[:8]}",
                }
            )

    for op in manifest.operations:
        if op.ownership != "managed":
            continue
        issue = _check_operation(op, home)
        if issue:
            report["ok"] = False
            report["issues"].append(issue)

    _emit_check(report, json_out)
    return report


def _emit_check(report: dict, json_out: bool) -> None:
    if json_out:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(
            f"check: ok (v{report.get('version', '?')}, "
            f"{report.get('operations', 0)} ops)"
        )
    else:
        print(f"check: FAIL ({len(report['issues'])} issues)")
        for iss in report["issues"]:
            print(f"  - [{iss.get('id')}] {iss.get('message')}")


def _check_operation(op, home: Path) -> dict | None:
    kind = op.kind
    if kind == "link-or-copy":
        if not op.destination:
            return None
        dst = Path(op.destination).expanduser()
        if not dst.exists():
            return {"id": op.id, "message": f"link-or-copy destination missing: {dst}"}
        return None
    if kind == "merge-json":
        if not op.destination or not op.merge_keys:
            return None
        path = Path(op.destination).expanduser()
        if not path.is_file():
            return {"id": op.id, "message": f"merge-json file missing: {path}"}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {"id": op.id, "message": f"merge-json invalid JSON: {exc}"}
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
            return {
                "id": op.id,
                "message": f"merge-json keys missing: {missing}",
            }
        return None
    if kind == "inject-markers":
        if not op.destination or not op.payload:
            return None
        path = Path(op.destination).expanduser()
        if not path.is_file():
            return {"id": op.id, "message": f"inject target missing: {path}"}
        text = path.read_text(encoding="utf-8")
        missing = [
            m
            for m in (op.payload.get("markers") or [])
            if f"BEGIN LOOPENGINE-MANAGED {m}" not in text
        ]
        if missing:
            return {"id": op.id, "message": f"markers missing: {missing}"}
        return None
    if kind == "registry-write":
        if not op.destination or not op.key:
            return None
        path = Path(op.destination).expanduser()
        if not path.is_file():
            return {"id": op.id, "message": f"registry file missing: {path}"}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {"id": op.id, "message": f"registry invalid JSON: {exc}"}
        key = op.key
        if isinstance(data.get("plugins"), dict) and key in data["plugins"]:
            return None
        enabled = (data.get("plugins") or {}).get("enabledPlugins")
        if isinstance(enabled, dict) and enabled.get(key) is True:
            return None
        if key in data:
            return None
        # zcode marketplaces list by id
        mps = data.get("marketplaces")
        if isinstance(mps, list) and any(
            isinstance(x, dict) and x.get("id") == key for x in mps
        ):
            return None
        return {"id": op.id, "message": f"registry key missing: {key}"}
    return None


def do_uninstall(
    *,
    home: Path | None = None,
    dry_run: bool = False,
    json_out: bool = False,
) -> dict:
    home = home or Path.home()
    path = manifest_path(home)
    plan = {"command": "uninstall", "dry_run": dry_run, "manifest": str(path)}
    if not path.is_file():
        plan["ok"] = False
        plan["error"] = "no install-manifest.json"
        if json_out:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print("❌ No install-manifest.json — nothing to uninstall via manifest")
        return plan

    manifest = load_manifest(path)
    plan["version"] = manifest.version
    plan["operations"] = len(manifest.operations)
    if dry_run:
        if json_out:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print(f"[dry-run] uninstall v{manifest.version} ({len(manifest.operations)} ops)")
        return plan

    for op in reversed(manifest.operations):
        try:
            revert_operation(op)
        except Exception as exc:  # noqa: BLE001 — best-effort uninstall
            print(f"  ⚠ revert {op.id}: {exc}")

    central = Path(manifest.central_root)
    if central.exists():
        shutil.rmtree(central, ignore_errors=True)
    current = loopengine_home(home) / "plugins" / "loopengine" / "current"
    if current.exists() or current.is_symlink():
        if current.is_symlink() or current.is_file():
            current.unlink(missing_ok=True)
        else:
            shutil.rmtree(current, ignore_errors=True)
    path.unlink(missing_ok=True)
    plan["ok"] = True
    if json_out:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print(f"✅ Uninstalled LoopEngine v{manifest.version}")
    return plan

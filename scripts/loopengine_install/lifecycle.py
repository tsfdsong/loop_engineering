"""Install / uninstall orchestration."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from loopengine_install.adapters import get_adapters
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
    known = ["cursor", "claude", "zcode"]
    if only:
        return [t for t in only if t in known]
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

    # Remove central package tree for this version
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

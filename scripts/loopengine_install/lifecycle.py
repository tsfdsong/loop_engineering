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
from loopengine_install.health import issues_as_dicts, run_health_checks
from loopengine_install.package import (
    build_central_package,
    prune_old_versions,
    read_repo_version,
)


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


def _skip_blocked_reason(
    home: Path, targets: list[str], existing: Manifest
) -> str | None:
    """Return why same-version skip must NOT happen; None → safe to skip.

    Incomplete manifest (e.g. cursor-only) or broken ZCode discovery must
    trigger repair without requiring --force.
    """
    installed = set((existing.components or {}).keys())
    missing = [t for t in targets if t not in installed]
    if missing:
        return f"manifest missing targets: {', '.join(missing)}"

    if "zcode" in targets:
        key = "loopengine@zcode-plugins-official"
        mp = (
            home
            / ".zcode"
            / "cli"
            / "plugins"
            / "marketplaces"
            / "zcode-plugins-official"
            / "marketplace.json"
        )
        if not mp.is_file():
            return "zcode marketplace.json missing"
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return "zcode marketplace.json invalid"
        plugins = data.get("plugins") or []
        if not any(
            isinstance(p, dict) and p.get("name") == "loopengine" for p in plugins
        ):
            return "zcode marketplace.json missing loopengine entry"

        cfg = home / ".zcode" / "cli" / "config.json"
        if cfg.is_file():
            try:
                cdata = json.loads(cfg.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return "zcode config.json invalid"
            plugins_obj = cdata.get("plugins") or {}
            enabled = plugins_obj.get("enabledPlugins") or {}
            if enabled.get(key) is not True:
                return f"zcode enabledPlugins missing {key}"
            suppressed = plugins_obj.get("suppressedBuiltins") or []
            if isinstance(suppressed, list) and key in suppressed:
                return f"zcode suppressedBuiltins contains {key}"

        cache = (
            home
            / ".zcode"
            / "cli"
            / "plugins"
            / "cache"
            / "zcode-plugins-official"
            / "loopengine"
            / existing.version
        )
        if not (cache / ".zcode-plugin" / "plugin.json").is_file():
            return f"zcode cache missing plugin.json under {cache}"

    return None


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

    plan: dict = {
        "command": "install",
        "version": version,
        "targets": targets,
        "dry_run": dry_run,
        "force": force,
        "skill_count": len(skill_names),
    }

    # D4: same version → tip unless --force or install incomplete / unhealthy
    mpath = manifest_path(home)
    if mpath.is_file() and not force:
        try:
            existing = load_manifest(mpath)
            if existing.version == version and not dry_run:
                reason = _skip_blocked_reason(home, targets, existing)
                if reason is None:
                    plan["skipped"] = True
                    plan["message"] = (
                        f"already installed v{version}; pass --force to reinstall"
                    )
                    if json_out:
                        print(json.dumps(plan, ensure_ascii=False, indent=2))
                    else:
                        print(f"ℹ️  {plan['message']}")
                    return plan
                plan["repair"] = reason
                if not json_out:
                    print(f"🔧 repairing install: {reason}")
        except Exception:  # noqa: BLE001
            pass

    if dry_run:
        # Plan ops without mutating disk (central source ≈ repo tree)
        adapters = get_adapters(targets)
        all_ops = []
        components = {}
        ctx = AdapterContext(
            home=home,
            repo_root=repo_root,
            central=repo_root,
            version=version,
            skill_names=skill_names,
            dry_run=True,
            mcp_bins=mcp_bins,
        )
        for adapter in adapters:
            ops = adapter.install(ctx)
            all_ops.extend(ops)
            components[adapter.name] = {"ops": len(ops)}
        plan["operations"] = [op.to_dict() for op in all_ops]
        plan["operation_count"] = len(all_ops)
        plan["components"] = components
        if json_out:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print(
                f"[dry-run] install v{version} → {targets} "
                f"({len(all_ops)} planned ops)"
            )
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

    pruned = prune_old_versions(le_home, version)
    manifest = Manifest(
        schema_version=2,
        product="loopengine",
        version=version,
        installed_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        central_root=str(central),
        skill_names=skill_names,
        components=components,
        operations=all_ops,
        extras={"pruned_versions": pruned} if pruned else {},
    )
    save_manifest(mpath, manifest)
    plan["central_root"] = str(central)
    plan["operations"] = len(all_ops)
    plan["manifest"] = str(mpath)
    if pruned:
        plan["pruned_versions"] = pruned
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

    health_issues = run_health_checks(manifest, home)
    if health_issues:
        report["ok"] = False
        report["issues"].extend(issues_as_dicts(health_issues))

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

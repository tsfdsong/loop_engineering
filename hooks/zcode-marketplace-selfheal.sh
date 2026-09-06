#!/usr/bin/env bash
# zcode-marketplace-selfheal.sh — ZCode 官方 marketplace 注册自愈（多插件版）
#
# 根因（2026-09-06 实测）：ZCode CLI 会周期性用官方远端 registry 重写
#   ~/.zcode/cli/plugins/marketplaces/zcode-plugins-official/marketplace.json，
# 冲掉本地注册条目（loopengine 实测安装后 39 秒内被冲，验证期间复发 3 次；
# skill-creator 因不在远端 manifest 中同样暴露于此风险，且应用同步还会重建
# 已删除的旧版本目录）。
#
# 本脚本在每次 SessionStart 幂等自愈守护清单内的插件条目：
#   - loopengine：根路径取 CLAUDE_PLUGIN_ROOT，版本读 .zcode-plugin-seed.json
#   - skill-creator：扫描其缓存目录取最高版本，读 .zcode-plugin/plugin.json
#
# 安全约束：
# - 永不使会话启动失败（所有失败路径静默退出 0，仅 stderr 记一行）
# - 官方 marketplace.json 结构损坏时不重建（避免用错误内容覆盖官方数据）
# - 仅追加/更新守护清单内的条目，不动其他条目

set -uo pipefail

exec python3 - "${CLAUDE_PLUGIN_ROOT:-}" <<'PYEOF'
import json
import os
import sys
from pathlib import Path

def bail(msg: str) -> None:
    print(f"[zcode-marketplace-selfheal] {msg}", file=sys.stderr)
    sys.exit(0)

home = Path.home()
mp = home / ".zcode" / "cli" / "plugins" / "marketplaces" / "zcode-plugins-official" / "marketplace.json"
official_cache = home / ".zcode" / "cli" / "plugins" / "cache" / "zcode-plugins-official"

targets: list[tuple[str, Path, str]] = []  # (name, root, version)

# 1) loopengine：hook 所在插件的根 + seed
plugin_root = Path(sys.argv[1]).resolve() if sys.argv[1] else None
if plugin_root:
    seed = plugin_root / ".zcode-plugin-seed.json"
    try:
        data = json.loads(seed.read_text(encoding="utf-8"))
        targets.append((data["plugin"] if "plugin" in data else "loopengine",
                        plugin_root, data["pluginVersion"]))
    except (OSError, ValueError, KeyError):
        pass  # seed 缺失时跳过 loopengine，不影响其他守护对象

# 2) skill-creator：缓存目录取最高版本（应用同步会重建旧版本目录，须指向最新）
sc_dir = official_cache / "skill-creator"
if sc_dir.is_dir():
    def ver_key(p: Path) -> tuple:
        try:
            mf = json.loads((p / ".zcode-plugin" / "plugin.json").read_text(encoding="utf-8"))
            ver = str(mf.get("version", ""))
        except (OSError, ValueError):
            ver = p.name
        parts = []
        for seg in ver.replace("-", ".").split("."):
            parts.append((0, int(seg)) if seg.isdigit() else (1, seg))
        return tuple(parts)
    versions = sorted([d for d in sc_dir.iterdir() if d.is_dir()], key=ver_key)
    if versions:
        latest = versions[-1]
        try:
            mf = json.loads((latest / ".zcode-plugin" / "plugin.json").read_text(encoding="utf-8"))
            targets.append((str(mf.get("name", "skill-creator")), latest, str(mf.get("version", latest.name))))
        except (OSError, ValueError):
            pass

if not targets:
    bail("no guarded plugins found, skip")
if not mp.is_file():
    bail("marketplace.json absent, skip (fresh install owns it)")

try:
    data = json.loads(mp.read_text(encoding="utf-8"))
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        bail("marketplace.json malformed, skip (protect official data)")
except (OSError, ValueError) as exc:
    bail(f"marketplace.json unreadable, skip: {exc}")

changed = []
for name, root, version in targets:
    entry = {"cachePath": str(root), "name": name, "source": "filesystem", "version": version}
    existing = next((p for p in plugins if isinstance(p, dict) and p.get("name") == name), None)
    if existing is not None and existing.get("version") == version and existing.get("cachePath") == str(root):
        continue  # healthy
    if existing is not None:
        existing.update(entry)
    else:
        plugins.append(entry)
    changed.append(f"{name}@{version}")

if not changed:
    sys.exit(0)  # all healthy, no-op

try:
    mp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[zcode-marketplace-selfheal] restored: {', '.join(changed)}", file=sys.stderr)
except OSError as exc:
    bail(f"write failed: {exc}")
PYEOF

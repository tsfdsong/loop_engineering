#!/usr/bin/env bash
# zcode-marketplace-selfheal.sh — ZCode 官方 marketplace 注册自愈
#
# 根因（2026-09-06 实测）：ZCode CLI 会周期性用官方远端 registry 重写
#   ~/.zcode/cli/plugins/marketplaces/zcode-plugins-official/marketplace.json，
# 冲掉 install.py 注入的 loopengine 条目（实测安装后 39 秒内被冲一次）。
# 适配器 docstring（2026-07-14 对 zcode.cjs 验证）确认 marketplace 条目是
# 插件加载三要件之一，被冲期间插件加载存在风险。
#
# 本脚本在每次 SessionStart 幂等自愈：条目存在 → no-op；缺失 → 按缓存
# 目录的 .zcode-plugin-seed.json 重建。绝不触碰官方远端插件条目。
#
# 设计约束：
# - 永不使会话启动失败（所有失败路径静默退出 0，仅 stderr 记一行）
# - 官方 marketplace.json 结构损坏时不重建（避免用错误内容覆盖官方数据）
# - 仅追加/更新自己的 loopengine 条目，不动其他条目

set -uo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$PLUGIN_ROOT" ]; then
  exit 0
fi

exec python3 - "$PLUGIN_ROOT" <<'PYEOF'
import json
import os
import sys
from pathlib import Path

plugin_root = Path(sys.argv[1]).resolve()
seed_path = plugin_root / ".zcode-plugin-seed.json"

def bail(msg: str) -> None:
    print(f"[zcode-marketplace-selfheal] {msg}", file=sys.stderr)
    sys.exit(0)

if not seed_path.is_file():
    bail("seed not found, skip")
try:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    version = seed["pluginVersion"]
except (OSError, ValueError, KeyError) as exc:
    bail(f"seed unreadable: {exc}")

home = Path.home()
mp = home / ".zcode" / "cli" / "plugins" / "marketplaces" / "zcode-plugins-official" / "marketplace.json"
entry = {
    "cachePath": str(plugin_root),
    "name": "loopengine",
    "source": "filesystem",
    "version": version,
}

if not mp.is_file():
    bail("marketplace.json absent, skip (fresh install owns it)")

try:
    data = json.loads(mp.read_text(encoding="utf-8"))
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        bail("marketplace.json malformed, skip (protect official data)")
except (OSError, ValueError) as exc:
    bail(f"marketplace.json unreadable, skip: {exc}")

existing = next(
    (p for p in plugins if isinstance(p, dict) and p.get("name") == "loopengine"),
    None,
)
if existing is not None and existing.get("version") == version and existing.get("cachePath") == str(plugin_root):
    sys.exit(0)  # healthy, no-op

if existing is not None:
    existing.update(entry)
else:
    plugins.append(entry)

try:
    mp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[zcode-marketplace-selfheal] restored loopengine@{version}", file=sys.stderr)
except OSError as exc:
    bail(f"write failed: {exc}")
PYEOF

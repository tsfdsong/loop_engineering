#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/register_zcode_plugin.py — 注册 loopengine 到 ZCode enabledPlugins
# ────────────────────────────────────────────────────────────
# 用法: python register_zcode_plugin.py <config.json> <plugin_name> <marketplace_id>
#   - config.json:    ZCode CLI config (默认 ~/.zcode/cli/config.json)
#   - plugin_name:    plugin 标识 (loopengine)
#   - marketplace_id: marketplace 标识 (zcode-plugins-official)
#
# 行为 (idempotent):
#   - 读取 config.json (缺失则报错退出非0)
#   - 确保 plugins.enabledPlugins 包含 "{plugin_name}@{marketplace_id}": true
#   - 已存在则不修改、不报错
#   - 写入 config.json (UTF-8, indent=2)
#
# 不在 enabledPlugins 列表的 plugin 即使物理存在也不会被 ZCode 加载,
# 这就是 v1.2.5 找不到 loopengine 的根因。
# ────────────────────────────────────────────────────────────

import json
import os
import sys
from datetime import datetime, timezone


def _read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <config.json> <plugin_name> <marketplace_id>",
            file=sys.stderr,
        )
        sys.exit(2)

    cfg_path = os.path.abspath(sys.argv[1])
    plugin_name = sys.argv[2]
    marketplace_id = sys.argv[3]
    plugin_key = f"{plugin_name}@{marketplace_id}"

    if not os.path.isfile(cfg_path):
        print(f"  ⚠ config 不存在: {cfg_path}", file=sys.stderr)
        sys.exit(1)

    try:
        cfg = _read_json(cfg_path)
    except json.JSONDecodeError as e:
        print(f"  ⚠ config JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 确保 plugins.enabledPlugins 结构
    plugins = cfg.setdefault("plugins", {})
    enabled = plugins.setdefault("enabledPlugins", {})

    if enabled.get(plugin_key) is True:
        # 已注册，不重复写
        return 0

    enabled[plugin_key] = True
    _write_json(cfg_path, cfg)
    print(f"  ✅ 已注册: {plugin_key} → enabled")
    return 0


if __name__ == "__main__":
    main()
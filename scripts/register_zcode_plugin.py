#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/register_zcode_plugin.py — DEPRECATED CLI（emergency only）
# ────────────────────────────────────────────────────────────
# Production path: python3 install.py install → loopengine_install.adapters.zcode
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

import os
import sys

# 单一真源（红线 9 R5.2）：从 _lib 导入，消除本文件重复实现
from _lib.json_io import read_json, write_json

# 兼容旧接口（tests/test_register_zcode_plugin.py 通过 _read_json/_write_json 调用）
_read_json = read_json
_write_json = write_json


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

    cfg = read_json(cfg_path)
    if not cfg:
        print(f"  ⚠ config 解析失败或为空: {cfg_path}", file=sys.stderr)
        sys.exit(1)

    # 确保 plugins.enabledPlugins 结构
    plugins = cfg.setdefault("plugins", {})
    enabled = plugins.setdefault("enabledPlugins", {})

    changed = False
    if enabled.get(plugin_key) is not True:
        enabled[plugin_key] = True
        changed = True

    # R3.5：enabled=true 仍可能被 suppressedBuiltins 压制
    suppressed = plugins.get("suppressedBuiltins")
    if isinstance(suppressed, list) and plugin_key in suppressed:
        plugins["suppressedBuiltins"] = [x for x in suppressed if x != plugin_key]
        changed = True

    if not changed:
        return 0

    write_json(cfg_path, cfg)
    print(f"  ✅ 已注册: {plugin_key} → enabled（已清除 suppressedBuiltins）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/merge_zcode_config.py — 合并 MCP 配置到 ZCode 桌面版
# ────────────────────────────────────────────────────────────
# 用途：把 2 个真 MCP server 路径注入到 ~/.zcode/cli/config.json 的 mcp.servers
#       （jcodemunch-mcp + repomix；headroom 是 AI CLI 助手非 MCP server 已剔除）
# 保留用户其他顶层字段（provider / model / 自定义设置等）。
# 由 install.sh write_zcode_desktop_config() 调用。
#
# v1.2.3 修复（2026-07-01）：
#   • 删 headroom entry（包无 MCP server 接口）
#   • 签名 4 参数 → 3 参数（移除 head_exe）
# ────────────────────────────────────────────────────────────

import json
import os
import sys


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <config.json> <jcode_exe> <repo_exe>",
              file=sys.stderr)
        sys.exit(2)

    cfg, jcode, repo = sys.argv[1:4]

    data = {}
    if os.path.isfile(cfg):
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ⚠ {cfg}: 读取失败 ({e.__class__.__name__})，按空配置重写",
                  file=sys.stderr)
            data = {}

    data.setdefault('mcp', {}).setdefault('servers', {})

    # 桌面版 ZCode 用 type="stdio" + command + args（与 .mcp.json 的 mcpServers schema 不同）
    data['mcp']['servers']['jcodemunch'] = {
        'type': 'stdio', 'command': jcode, 'args': ['serve']
    }
    data['mcp']['servers']['repomix'] = {
        'type': 'stdio', 'command': repo, 'args': ['--mcp']
    }
    # 兼容清理：v1.2.2 之前写入的空 headroom entry 自动清除
    data['mcp']['servers'].pop('headroom', None)

    # 原子写：先写 .tmp 再 rename，避免中途崩溃留截断 JSON
    tmp = cfg + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, cfg)
    except OSError as e:
        print(f"  ❌ 写入 {cfg} 失败: {e}", file=sys.stderr)
        if os.path.exists(tmp):
            os.remove(tmp)
        sys.exit(1)

    print(f"  ✅ {cfg}")


if __name__ == '__main__':
    main()
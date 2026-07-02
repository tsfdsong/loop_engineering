#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/merge_cursor_config.py — 合并 MCP 配置到 Cursor IDE
# ────────────────────────────────────────────────────────────
# 用途：把 3 个 MCP server 路径注入到 ~/.cursor/mcp.json 的 mcpServers
#       （jcodemunch-mcp + repomix + headroom；headroom 已在 LoopEngine 中作为
#        supplemental MCP server 部署，遵循 .mcp.json 既有 schema）
# 保留用户其他顶层字段与任何已有 MCP server（如 drawio 等）。
# 由 install.sh write_cursor_mcp_config() 调用。
#
# Schema 关键差异（[F] 来自本机 .mcp.json 实测）：
#   • Cursor IDE: "mcpServers": { "<name>": { "command": "...", "args": [...] } }
#     （**无** type 字段，无 stdin/stdout 标记，符合 Cursor 0.40+ 约定）
#   • ZCode 桌面版: "mcp.servers": { "<name>": { "type": "stdio", "command": "...", "args": [...] } }
#     （type:"stdio" 是 ZCode 桌面版特有 schema，不适用于 Cursor）
#
# v1.3.0 新增（2026-07-02）：
#   • 对齐 skill-hub-install-reference.md §4.4 "Cursor IDE MCP 配置" 缺口
#   • 保留 drawio / 其他用户自有 MCP server（与 merge_zcode_config.py 行为一致）
#   • 强制覆写 jcodemunch/repomix/headroom 3 key（路径变化时同步）
# ────────────────────────────────────────────────────────────

import json
import os
import sys


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <cursor_mcp.json> <jcode_exe> <repo_exe> <hdrm_exe>",
              file=sys.stderr)
        sys.exit(2)

    cfg, jcode, repo, hdrm = sys.argv[1:5]

    data = {}
    if os.path.isfile(cfg):
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ⚠ {cfg}: 读取失败 ({e.__class__.__name__})，按空配置重写",
                  file=sys.stderr)
            data = {}

    # 顶层 mcpServers 字典保留（包含用户自有 server 如 drawio）
    data.setdefault('mcpServers', {})

    # Cursor IDE MCP schema: command + args（无 type 字段）
    data['mcpServers']['jcodemunch'] = {
        'command': jcode, 'args': ['serve']
    }
    data['mcpServers']['repomix'] = {
        'command': repo, 'args': ['--mcp']
    }
    data['mcpServers']['headroom'] = {
        'command': hdrm, 'args': ['mcp', 'serve']
    }

    # 原子写：先写 .tmp 再 rename，避免中途崩溃留截断 JSON
    tmp = cfg + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, cfg)
    except OSError as e:
        print(f"  ❌ 写入 {cfg} 失败: {e}", file=sys.stderr)
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        sys.exit(1)

    print(f"  ✅ {cfg}")


if __name__ == '__main__':
    main()

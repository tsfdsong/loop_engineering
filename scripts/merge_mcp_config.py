#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/merge_mcp_config.py — 合并 MCP 配置到 AI 工具
# ────────────────────────────────────────────────────────────
# 用途：把 MCP server 路径注入到目标 AI 工具的 MCP 配置文件
# 合并两个 schema：
#   • zcode: ~/.zcode/cli/config.json → mcp.servers.<name>.{type:"stdio",command,args}
#     （ZCode 桌面版特有 schema）
#   • cursor: ~/.cursor/mcp.json → mcpServers.<name>.{command,args}
#     （Cursor IDE 0.40+ schema，无 type 字段）
# 由 install.sh 的 common_write_zcode_desktop_config / common_deploy_cursor_mcp 调用
#
# 保留用户其他顶层字段与已有 MCP server（合并幂等）。
# 强制覆写脚本负责的 server key（路径变化时同步）。
# 原子写：先写 .tmp 再 rename，避免中途崩溃留截断 JSON
#
# v1.3.1 新增：合并 ZCode 桌面版 + Cursor IDE 两种 MCP schema
# 由 install.sh 的 common_write_zcode_desktop_config / common_deploy_cursor_mcp 调用
# ────────────────────────────────────────────────────────────

import json
import os
import sys


def merge_zcode(cfg, jcode, repo):
    """ZCode 桌面版：~/.zcode/cli/config.json → mcp.servers.<name>.{type,command,args}"""
    data = _read_json(cfg)
    data.setdefault('mcp', {}).setdefault('servers', {})

    data['mcp']['servers']['jcodemunch'] = {
        'type': 'stdio', 'command': jcode, 'args': ['serve']
    }
    data['mcp']['servers']['repomix'] = {
        'type': 'stdio', 'command': repo, 'args': ['--mcp']
    }
    # 兼容清理：v1.2.2 之前写入的空 headroom entry 自动清除
    data['mcp']['servers'].pop('headroom', None)
    return data


def merge_cursor(cfg, jcode, repo, hdrm):
    """Cursor IDE：~/.cursor/mcp.json → mcpServers.<name>.{command,args}
    v1.3.2: headroom 可选——为空字符串时跳过该 entry（不再强制 3 个全找到才写）。
    同时清理可能存在的旧 headroom entry（避免残留失效路径）。
    """
    data = _read_json(cfg)
    data.setdefault('mcpServers', {})

    data['mcpServers']['jcodemunch'] = {
        'command': jcode, 'args': ['serve']
    }
    data['mcpServers']['repomix'] = {
        'command': repo, 'args': ['--mcp']
    }
    # headroom 可选：有路径才写，无路径清理旧 entry
    if hdrm:
        data['mcpServers']['headroom'] = {
            'command': hdrm, 'args': ['mcp', 'serve']
        }
    else:
        data['mcpServers'].pop('headroom', None)
    return data


def _read_json(cfg):
    """读 JSON；不存在/损坏 → 空 dict（带 stderr 警告）"""
    data = {}
    if os.path.isfile(cfg):
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ⚠ {cfg}: 读取失败 ({e.__class__.__name__})，按空配置重写",
                  file=sys.stderr)
            data = {}
    return data


def _atomic_write_json(cfg, data):
    """原子写：先写 .tmp 再 rename，避免中途崩溃留截断 JSON"""
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


def main():
    # zcode:   python merge_mcp_config.py zcode   <cfg> <jcode> <repo>
    # cursor:  python merge_mcp_config.py cursor  <cfg> <jcode> <repo> <hdrm>
    args = sys.argv[1:]
    if not args or args[0] not in ('zcode', 'cursor'):
        print(f"Usage: {sys.argv[0]} {{zcode|cursor}} <config.json> <jcode> <repo> [<hdrm>]",
              file=sys.stderr)
        sys.exit(2)

    schema = args[0]
    if schema == 'zcode':
        if len(args) != 4:
            print(f"Usage: {sys.argv[0]} zcode <config.json> <jcode_exe> <repo_exe>",
                  file=sys.stderr)
            sys.exit(2)
        cfg, jcode, repo = args[1:4]
        data = merge_zcode(cfg, jcode, repo)
    else:  # cursor
        if len(args) != 5:
            print(f"Usage: {sys.argv[0]} cursor <mcp.json> <jcode_exe> <repo_exe> <hdrm_exe>",
                  file=sys.stderr)
            sys.exit(2)
        cfg, jcode, repo, hdrm = args[1:5]
        data = merge_cursor(cfg, jcode, repo, hdrm)

    _atomic_write_json(cfg, data)
    print(f"  ✅ {cfg}")


if __name__ == '__main__':
    main()

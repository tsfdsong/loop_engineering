#!/usr/bin/env python3
"""Token 配置管理：检查、设置、查看、清除。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import CREDENTIALS_FILE, clear_token, load_config, save_token  # noqa: E402

TOKEN_PREFIX = "aih_"


def check() -> None:
    """检查是否已配置 token（静默，仅退出码）。"""
    _, token = load_config()
    if token:
        sys.exit(0)
    sys.exit(1)


def cmd_set(token: str, url: str = "") -> None:
    """保存 token。"""
    token = token.strip()
    if not token.startswith(TOKEN_PREFIX):
        print(f"❌ Token 格式无效：应以 {TOKEN_PREFIX} 开头")
        sys.exit(1)
    if len(token) < len(TOKEN_PREFIX) + 16:
        print(f"❌ Token 长度不足：至少 {len(TOKEN_PREFIX) + 16} 个字符")
        sys.exit(1)
    save_token(url, token)
    print("✅ Token 已保存至", str(CREDENTIALS_FILE))


def cmd_show() -> None:
    """显示当前配置。"""
    url, token = load_config()
    if not token:
        print("⚠️ 未配置 Token")
        print()
        print("获取步骤：")
        print("  1. 浏览器打开 https://test-yimiaihub.yimidida.com/yimiaihub/dashboard/settings")
        print("  2. 登录后拉到「API Token 管理」→ 点击「生成新 Token」")
        print("  3. 复制 token 后在此对话中输入")
        print("  4. 同时提供平台地址（如 https://test-yimiaihub.yimidida.com/yimiaihub）")
        sys.exit(0)

    mask = token[:8] + "***" + token[-4:] if len(token) > 12 else token[0] + "***"
    print("平台地址:", url or "(未设置)")
    print("Token:", mask)
    print("配置文件:", str(CREDENTIALS_FILE))


def cmd_clear() -> None:
    clear_token()
    print("✅ Token 已清除")


def print_usage() -> None:
    print("用法: python config.py <子命令> [参数]")
    print("  --check              检查是否已配置（退出码 0=已配 1=未配）")
    print("  set --token T --url U 保存 token 和平台地址")
    print("  show                 查看当前配置")
    print("  clear                清除已保存的 token")
    print()
    print("示例:")
    print("  python config.py set --token aih_abc123 --url https://test-yimiaihub.yimidida.com/yimiaihub")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        check()  # 默认同 --check

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "--check":
        check()
    elif cmd == "set":
        token_arg = ""
        url_arg = ""
        i = 0
        while i < len(args):
            if args[i] == "--token" and i + 1 < len(args):
                token_arg = args[i + 1]
                i += 2
            elif args[i] == "--url" and i + 1 < len(args):
                url_arg = args[i + 1]
                i += 2
            else:
                i += 1
        if not token_arg:
            print("❌ 缺少 --token 参数")
            sys.exit(1)
        cmd_set(token_arg, url_arg)
    elif cmd == "show":
        cmd_show()
    elif cmd == "clear":
        cmd_clear()
    else:
        print_usage()
        sys.exit(1)

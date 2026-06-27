#!/usr/bin/env python3
"""在平台上搜索已有技能（查重）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import APIError, load_config, search_skills_api  # noqa: E402


def search(query: str) -> None:
    url, token = load_config()
    if not token:
        print("❌ 未配置 Token，请先运行: python config.py set --token <你的token>")
        sys.exit(2)

    try:
        results = search_skills_api(url, token, query)
        if not isinstance(results, list):
            results = []
    except APIError as e:
        if e.status_code == 401:
            print("❌ 认证失败，Token 无效或已过期，请在平台重新生成")
            sys.exit(2)
        print(f"❌ 搜索失败: {e.detail}")
        sys.exit(1)

    if not results:
        print(f"平台未找到与「{query}」匹配的技能")
    else:
        print(f"平台已有 {len(results)} 个匹配技能：")
        for r in results:
            if not isinstance(r, dict):
                continue
            slug = r.get("slug", "?")
            name = r.get("name", slug)
            owner = r.get("author", "?")
            print(f"  • {name} ({slug}) — 作者: {owner}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python search.py <查询词>")
        sys.exit(1)

    search(sys.argv[1])

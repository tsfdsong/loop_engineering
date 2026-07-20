#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/register_zcode_marketplace.py — 注册 zcode-plugins-official marketplace
# ────────────────────────────────────────────────────────────
# 用法: python register_zcode_marketplace.py <known_marketplaces.json> <marketplace_id>
#   - known_marketplaces.json: 默认 ~/.zcode/cli/plugins/known_marketplaces.json
#   - marketplace_id:          zcode-plugins-official
#
# 行为 (idempotent):
#   - 确保 marketplaces 列表包含 id=marketplace_id 的条目
#   - 已存在则不修改、不报错
#   - source.type = "local" 指向 ~/.zcode/cli/plugins/cache/zcode-plugins-official
# ────────────────────────────────────────────────────────────

import os
import sys
from datetime import datetime, timezone

# 单一真源（红线 9 R5.2）：从 _lib 导入，消除本文件重复实现
from _lib.json_io import read_json, write_json

# 兼容旧接口（tests/test_register_zcode_marketplace.py 通过 _read_json/_write_json 调用）
_read_json = read_json
_write_json = write_json


def main():
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <known_marketplaces.json> <marketplace_id>",
            file=sys.stderr,
        )
        sys.exit(2)

    mp_path = os.path.abspath(sys.argv[1])
    marketplace_id = sys.argv[2]

    if not os.path.isfile(mp_path):
        print(f"  ⚠ marketplaces.json 不存在: {mp_path}", file=sys.stderr)
        sys.exit(1)

    mp = read_json(mp_path)
    if not mp:
        print(f"  ⚠ marketplaces.json 解析失败或为空: {mp_path}", file=sys.stderr)
        sys.exit(1)

    marketplaces = mp.setdefault("marketplaces", [])

    # 已存在则不重复加
    for entry in marketplaces:
        if entry.get("id") == marketplace_id:
            return 0

    # 推断 home 路径（POSIX: $HOME；Windows: %USERPROFILE%）
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or ""
    cache_path = os.path.join(home, ".zcode", "cli", "plugins", "cache", "zcode-plugins-official")

    new_entry = {
        "id": marketplace_id,
        "source": {
            "source": "local",
            "path": cache_path,
        },
        "name": marketplace_id,
        "description": f"ZCode official plugins cache ({marketplace_id}) — registered by LoopEngine install.py",
        "addedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "pluginCount": 0,
    }
    marketplaces.append(new_entry)
    write_json(mp_path, mp)
    print(f"  ✅ 已注册 marketplace: {marketplace_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
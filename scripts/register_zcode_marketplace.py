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

    try:
        mp = _read_json(mp_path)
    except json.JSONDecodeError as e:
        print(f"  ⚠ marketplaces.json JSON 解析失败: {e}", file=sys.stderr)
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
        "description": f"ZCode official plugins cache ({marketplace_id}) — registered by LoopEngine install.sh",
        "addedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "pluginCount": 0,
    }
    marketplaces.append(new_entry)
    _write_json(mp_path, mp)
    print(f"  ✅ 已注册 marketplace: {marketplace_id}")
    return 0


if __name__ == "__main__":
    main()
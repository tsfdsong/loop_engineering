#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/_lib/json_io.py — JSON / 合并 公共真源
# ────────────────────────────────────────────────────────────
# 单一真源（红线 9 R5.2 减法）：
#   - read_json / write_json        : 安全读/写 + UTF-8 + indent=2 + ensure_ascii=False
#   - atomic_write_json             : 先写 .tmp 再 rename，避免截断
#   - deep_merge / strip_meta       : 递归合并（_comment 丢弃）
#
# 由以下脚本 import（消除 5 处独立实现）：
#   - render_plugins.py
#   - merge_mcp_config.py
#   - register_zcode_marketplace.py
#   - register_zcode_plugin.py
#   - install_zcode_plugin.py
# ────────────────────────────────────────────────────────────

import json
import os
import sys
from typing import Any


def read_json(path: str) -> dict:
    """读 JSON 文件，UTF-8；文件不存在/损坏返回空 dict（stderr 警告）。"""
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(
            f"  ⚠ {path}: 读取失败 ({e.__class__.__name__})，按空配置返回",
            file=sys.stderr,
        )
        return {}


def write_json(path: str, data: Any) -> None:
    """写 JSON（UTF-8 + indent=2 + ensure_ascii=False + trailing newline）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def atomic_write_json(path: str, data: Any) -> None:
    """原子写：先写 .tmp 再 rename，避免中途崩溃留截断 JSON。失败 → exit 1。"""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError as e:
        print(f"  ❌ 写入 {path} 失败: {e}", file=sys.stderr)
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        sys.exit(1)


def strip_meta(d: Any) -> Any:
    """递归删除所有 _xxx 元数据字段（_comment / _meta / _xxx）。"""
    if isinstance(d, dict):
        return {k: strip_meta(v) for k, v in d.items() if not k.startswith("_")}
    if isinstance(d, list):
        return [strip_meta(x) if isinstance(x, dict) else x for x in d]
    return d


def deep_merge(base: dict, overlay: dict) -> dict:
    """深合并：overlay 字段覆盖 base 字段；dict 递归合并；list/scalar 替换。
    元数据字段（_ 开头）在 overlay 中被丢弃。
    """
    merged = dict(base)
    for k, v in overlay.items():
        if k.startswith("_"):
            continue
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged
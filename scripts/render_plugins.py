#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/render_plugins.py — 合并 .plugin-template.json + 工具 overlay
# ────────────────────────────────────────────────────────────
# 用法：python render_plugins.py <project_root> <out_dir>
#   - project_root:  含 .plugin-template.json 的项目根
#   - out_dir:       输出目录（mkdir -p）；如已存在同名文件则覆盖
#
# 自动发现并渲染的 manifest（按目录组织）：
#   .claude-plugin/plugin.json      → out_dir/claude-plugin/plugin.json
#   .codex-plugin/plugin.json       → out_dir/codex-plugin/plugin.json
#   .cursor-plugin/plugin.json      → out_dir/cursor-plugin/plugin.json
#   .kimi-plugin/plugin.json        → out_dir/kimi-plugin/plugin.json
#   .zcode-plugin/plugin.json       → out_dir/zcode-plugin/plugin.json
#   gemini-extension.json           → out_dir/gemini-extension.json
#   .claude-plugin/marketplace.json → out_dir/claude-plugin/marketplace.json
#
# 合并规则（深合并）：
#   - dict 递归合并
#   - list/scalar 替换
#   - 顶层 _comment 字段被丢弃（仅用于人工阅读）
#   - overlay 字段优先于 template
#
# 由 install.sh Step 2 部署插件 manifest 时调用。
# 同步更新：package.json 的 version 与 .plugin-template.json 的 version 必须一致。
# ────────────────────────────────────────────────────────────

import glob
import json
import os
import sys


def deep_merge(base: dict, overlay: dict) -> dict:
    """深合并：overlay 字段覆盖 base 字段；dict 递归合并。"""
    merged = dict(base)
    for k, v in overlay.items():
        if k.startswith("_"):
            # 元数据字段（_comment）丢弃，不进入输出
            continue
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def strip_meta(d: dict) -> dict:
    """递归删除所有 _comment / _xxx 元数据字段。"""
    out = {}
    for k, v in d.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            out[k] = strip_meta(v)
        elif isinstance(v, list):
            out[k] = [strip_meta(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


# ── P4 重构：抽公共 JSON I/O 公共函数 ─────────────────────────
def _read_json(path: str) -> dict:
    """读 JSON 文件，UTF-8 编码。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    """写 JSON 文件（带 newline + ensure_ascii=False + indent=2）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def render_plugin_json(template: dict, overlay_path: str, out_path: str, label: str) -> bool:
    """渲染单个工具的 plugin.json。返回 True 成功。label 是人类可读名（如 "claude-plugin/plugin.json"）。"""
    if not os.path.isfile(overlay_path):
        return False
    overlay = _read_json(overlay_path)
    merged = deep_merge(template, overlay)
    _write_json(out_path, merged)
    print(f"  ✅ {label}")
    return True


def render_marketplace(template: dict, mp_path: str, out_path: str, label: str) -> bool:
    """渲染 marketplace.json（独立 schema：含 plugins[] 数组），同步版本号。"""
    if not os.path.isfile(mp_path):
        return False
    mp = strip_meta(_read_json(mp_path))
    for plugin in mp.get("plugins", []):
        plugin["version"] = template.get("version", plugin.get("version"))
        plugin["description"] = template.get("description", plugin.get("description"))
    _write_json(out_path, mp)
    print(f"  ✅ {label}")
    return True


def main():
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <project_root> <out_dir>",
            file=sys.stderr,
        )
        sys.exit(2)

    project_root = os.path.abspath(sys.argv[1])
    out_dir = os.path.abspath(sys.argv[2])
    template_path = os.path.join(project_root, ".plugin-template.json")

    if not os.path.isfile(template_path):
        print(f"  ❌ 模板不存在: {template_path}", file=sys.stderr)
        sys.exit(1)

    template = strip_meta(_read_json(template_path))

    os.makedirs(out_dir, exist_ok=True)
    rendered = 0

    # ── P5 重构：自动发现 .*-plugin/plugin.json（不再硬编码 5 个目录名）──
    overlay_paths = sorted(glob.glob(os.path.join(project_root, ".*-plugin", "plugin.json")))
    for overlay_path in overlay_paths:
        # 从 .claude-plugin/plugin.json 提取 claude-plugin（去前导点）
        parent_name = os.path.basename(os.path.dirname(overlay_path))  # e.g. ".claude-plugin"
        short = parent_name.lstrip(".")
        out_path = os.path.join(out_dir, short, "plugin.json")
        if render_plugin_json(template, overlay_path, out_path, f"{short}/plugin.json"):
            rendered += 1

    # gemini-extension.json（顶层）
    if render_plugin_json(
        template,
        os.path.join(project_root, "gemini-extension.json"),
        os.path.join(out_dir, "gemini-extension.json"),
        "gemini-extension.json",
    ):
        rendered += 1

    # marketplace.json（独立 schema）
    if render_marketplace(
        template,
        os.path.join(project_root, ".claude-plugin", "marketplace.json"),
        os.path.join(out_dir, "claude-plugin", "marketplace.json"),
        "claude-plugin/marketplace.json",
    ):
        rendered += 1

    if rendered == 0:
        print("  ❌ 未渲染任何 manifest", file=sys.stderr)
        sys.exit(1)
    print(f"  ✅ 渲染 {rendered} 个 manifest")


if __name__ == "__main__":
    main()

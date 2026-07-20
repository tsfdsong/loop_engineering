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
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Callable, List, Optional

# v2.0 修复（2026-07-18 · system-review 发现的 v1.x 遗留 bug）：
# render_plugins.py 被 install.sh 调用时 cwd 是临时 clone 目录，
# 不一定是 scripts/ 自身。需要把 scripts/ 父目录加到 sys.path，
# 让 `from _lib.json_io import ...` 在任何 cwd 下都能解析。
_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = _HERE  # render_plugins.py 位于 scripts/ 下
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# 单一真源（红线 9 R5.2）：从 _lib 导入，消除本文件独立实现
from _lib.json_io import deep_merge, strip_meta, write_json


def _status_print(message: str, *, error: bool = False) -> None:
    """在不同终端编码下安全打印状态信息。"""
    stream = sys.stderr if error else sys.stdout
    try:
        print(message, file=stream)
    except UnicodeEncodeError:
        sanitized = (
            message.encode(stream.encoding or "utf-8", errors="replace")
            .decode(stream.encoding or "utf-8", errors="replace")
        )
        print(sanitized, file=stream)


# deep_merge / strip_meta / write_json 已从 _lib.json_io 导入
# 保留 _read_json / _write_json 别名供本文件内部使用（避免改全文调用点）
def _read_json(path: str) -> dict:
    """读 JSON 文件，UTF-8 编码。"""
    from _lib.json_io import read_json
    return read_json(path)


_write_json = write_json


def render_plugin_json(template: dict, overlay_path: str, out_path: str, label: str) -> bool:
    """渲染单个工具的 plugin.json。返回 True 成功。label 是人类可读名（如 "claude-plugin/plugin.json"）。"""
    if not os.path.isfile(overlay_path):
        return False
    overlay = _read_json(overlay_path)
    merged = deep_merge(template, overlay)
    _write_json(out_path, merged)
    _status_print(f"  ✅ {label}")
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
    _status_print(f"  ✅ {label}")
    return True


# ── ToolAdapter 注册表（v1.4 Registry 重构）─────────────


@dataclass
class ToolAdapter:
    """单个工具的 plugin manifest 适配器元数据 + 渲染策略 + 激活策略。

    数据+行为混合是有意 trade-off（决策 4）：让新工具单点注册。
    代价是 activate Callable 需在测试中 mock。
    """

    id: str
    label: str
    compliance: str  # "native" / "adapter-backed" / "instruction-backed"
    overlay_path: str
    output_path: str
    notes: str = ""
    drop_fields: List[str] = field(default_factory=list)
    extra_outputs: List[dict] = field(default_factory=list)
    activate: Optional[Callable] = None


def activate_zcode_plugin(project_root: str, out_dir: str) -> bool:
    """ZCode plugin 激活：注册 marketplace + 写入 enabledPlugins。

    调用 register_zcode_marketplace.py + register_zcode_plugin.py。
    返回 True 表示成功。失败时回滚 config.json（R7 风险缓解）。
    """
    config_path = os.path.expanduser("~/.zcode/cli/config.json")
    known_mp_path = os.path.expanduser(
        "~/.zcode/cli/plugins/known_marketplaces.json"
    )
    backup = config_path + ".loopengine-bak"

    # 先备份 config.json
    if os.path.isfile(config_path):
        shutil.copy2(config_path, backup)

    try:
        # 1. 注册 marketplace
        subprocess.run(
            [
                sys.executable,
                os.path.join(project_root, "scripts/register_zcode_marketplace.py"),
                known_mp_path,
                "zcode-plugins-official",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        # 2. 注册 plugin 到 enabledPlugins
        subprocess.run(
            [
                sys.executable,
                os.path.join(project_root, "scripts/register_zcode_plugin.py"),
                config_path,
                "loopengine",
                "zcode-plugins-official",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        _status_print(f"  ✅ ZCode plugin 激活成功")
        return True
    except subprocess.CalledProcessError as e:
        _status_print(
            f"  ⚠️ ZCode plugin 激活失败: {e.stderr or e.stdout}", error=True
        )
        # 回滚
        if os.path.isfile(backup):
            shutil.move(backup, config_path)
        return False
    finally:
        if os.path.isfile(backup):
            os.remove(backup)


TOOL_ADAPTERS: List[ToolAdapter] = [
    # ── Native ──
    ToolAdapter(
        id="claude-code",
        label="Claude Code",
        compliance="native",
        overlay_path=".claude-plugin/plugin.json",
        output_path="claude-plugin/plugin.json",
        notes="完整 hooks + skills + commands 支持",
        extra_outputs=[
            {
                "kind": "marketplace",
                "input_path": ".claude-plugin/marketplace.json",
                "output_path": "claude-plugin/marketplace.json",
            }
        ],
    ),
    # ── Adapter-backed ──
    ToolAdapter(
        id="zcode",
        label="ZCode",
        compliance="adapter-backed",
        overlay_path=".zcode-plugin/plugin.json",
        output_path="zcode-plugin/plugin.json",
        notes=(
            "skills 走 plugin 内嵌；hooks 走 plugin hooks；"
            "MCP 写 config.json mcp.servers"
        ),
        drop_fields=["mcpServers"],
        # activate stays None: package render must not side-activate ~/.zcode.
        # ZCode activation belongs to loopengine_install adapters only (D10/C3).
        activate=None,
    ),
    ToolAdapter(
        id="cursor",
        label="Cursor",
        compliance="adapter-backed",
        overlay_path=".cursor-plugin/plugin.json",
        output_path="cursor-plugin/plugin.json",
        notes=(
            "skills 用户级平铺；rules 用 .mdc"
            "（需 alwaysApply frontmatter）"
        ),
    ),
    ToolAdapter(
        id="codex",
        label="Codex",
        compliance="adapter-backed",
        overlay_path=".codex-plugin/plugin.json",
        output_path="codex-plugin/plugin.json",
    ),
    ToolAdapter(
        id="gemini-cli",
        label="Gemini CLI",
        compliance="adapter-backed",
        overlay_path="gemini-extension.json",
        output_path="gemini-extension.json",
        notes="用 contextFileName 机制（非标准 plugin.json）",
    ),
    # Kimi Code：模板已准备，尚未接入 COMMON_ALL_AGENT_IDS，待接入后启用
    # GitHub Copilot / Pi：不走 manifest → 不进 TOOL_ADAPTERS
]


def render_adapter(
    template: dict, adapter: ToolAdapter, project_root: str, out_dir: str
) -> bool:
    """渲染单个 ToolAdapter 的主 manifest。返回 True 成功。"""
    overlay_full = os.path.join(project_root, adapter.overlay_path)
    out_full = os.path.join(out_dir, adapter.output_path)
    if not os.path.isfile(overlay_full):
        return False
    merged = deep_merge(template, _read_json(overlay_full))
    # drop_fields 处理（如 ZCode 剥离 mcpServers）
    for f in adapter.drop_fields:
        merged.pop(f, None)
    _write_json(out_full, merged)
    _status_print(f"  ✅ {adapter.label}: {adapter.output_path}")
    return True


def render_extra_outputs(
    template: dict, adapter: ToolAdapter, project_root: str, out_dir: str
) -> int:
    """渲染 marketplace.json 等额外输出。返回渲染数。"""
    count = 0
    for extra in adapter.extra_outputs:
        if extra.get("kind") == "marketplace":
            mp_in = os.path.join(project_root, extra["input_path"])
            mp_out = os.path.join(out_dir, extra["output_path"])
            if render_marketplace(template, mp_in, mp_out, extra["output_path"]):
                count += 1
    return count


def main():
    if len(sys.argv) != 3:
        _status_print(
            f"Usage: {sys.argv[0]} <project_root> <out_dir>",
            error=True,
        )
        sys.exit(2)

    project_root = os.path.abspath(sys.argv[1])
    out_dir = os.path.abspath(sys.argv[2])
    template_path = os.path.join(project_root, ".plugin-template.json")

    if not os.path.isfile(template_path):
        _status_print(f"  ❌ 模板不存在: {template_path}", error=True)
        sys.exit(1)

    template = strip_meta(_read_json(template_path))
    os.makedirs(out_dir, exist_ok=True)
    rendered = 0
    activated = []

    # 遍历 TOOL_ADAPTERS
    known_overlays = {a.overlay_path for a in TOOL_ADAPTERS}
    for adapter in TOOL_ADAPTERS:
        if render_adapter(template, adapter, project_root, out_dir):
            rendered += 1
        rendered += render_extra_outputs(template, adapter, project_root, out_dir)
        # 激活回调（如 ZCode）
        if adapter.activate:
            if adapter.activate(project_root, out_dir):
                activated.append(adapter.id)

    # Glob 兜底：扫描不在 TOOL_ADAPTERS 里的 .*-plugin/plugin.json
    overlay_paths = sorted(
        glob.glob(os.path.join(project_root, ".*-plugin", "plugin.json"))
    )
    for overlay_path in overlay_paths:
        rel = os.path.relpath(overlay_path, project_root)
        if rel in known_overlays:
            continue
        _status_print(f"  ⚠️ Glob 兜底（未注册）: {rel}")
        parent_name = os.path.basename(os.path.dirname(overlay_path))
        short = parent_name.lstrip(".")
        out_path = os.path.join(out_dir, short, "plugin.json")
        if render_plugin_json(
            template, overlay_path, out_path, f"{short}/plugin.json"
        ):
            rendered += 1

    if rendered == 0:
        _status_print("  ❌ 未渲染任何 manifest", error=True)
        sys.exit(1)
    _status_print(f"  ✅ 渲染 {rendered} 个 manifest")
    if activated:
        _status_print(
            f"  ✅ 激活 {len(activated)} 个工具: {', '.join(activated)}"
        )


if __name__ == "__main__":
    main()

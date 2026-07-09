#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/audit_tools.py — 6 维度部署审计
# ────────────────────────────────────────────────────────────
# 用法：
#   python3 scripts/audit_tools.py             # 人友好输出
#   python3 scripts/audit_tools.py --json      # CI 友好 JSON
#   python3 scripts/audit_tools.py --tool X    # 单工具
#   python3 scripts/audit_tools.py --verbose   # 详细输出
#
# 退出码：0=OK/warnings, 1=有 error, 2=参数错误
#
# 6 维度：
#   A. 工具部署完整性（高）
#   B. 技能完整性（info — 仅哨兵）
#   C. 红线一致性（info — 仅哨兵）
#   D. MCP 健康（中 — 全部未装→warning）
#   E. 版本一致性（中）
#   F. Schema 合法性（低）
# ────────────────────────────────────────────────────────────

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
sys.path.insert(0, SCRIPTS_DIR)

from render_plugins import TOOL_ADAPTERS  # noqa: E402


@dataclass
class AuditResult:
    """单个检查项结果。"""

    dimension: str  # "A" ~ "F"
    severity: str  # "error" / "warning" / "info" / "ok"
    tool: str  # "claude-code" / "zcode" / "all"
    message: str
    detail: dict = field(default_factory=dict)


# ── A 维度：工具部署完整性 ──────────────────────────────


def dimension_a_tool_deploy(
    tool_filter: Optional[str] = None,
) -> List[AuditResult]:
    """A 维度：每个 ToolAdapter 对应的部署目录存在。"""
    results = []
    home = os.path.expanduser("~")
    checks = {
        "claude-code": os.path.join(home, ".claude", "skills", "loopengine"),
        "zcode": os.path.join(home, ".zcode", "skills", "loopengine"),
        "cursor": os.path.join(home, ".cursor", "skills", "loopengine"),
    }
    for adapter in TOOL_ADAPTERS:
        if tool_filter and adapter.id != tool_filter:
            continue
        if adapter.id not in checks:
            continue
        path = checks[adapter.id]
        if os.path.isdir(path):
            results.append(
                AuditResult("A", "ok", adapter.id, f"部署目录存在: {path}")
            )
        else:
            results.append(
                AuditResult(
                    "A", "warning", adapter.id, f"部署目录不存在: {path}"
                )
            )
    return results


# ── D 维度：MCP 健康 ──────────────────────────────────


def dimension_d_mcp_health(
    tool_filter: Optional[str] = None,
) -> List[AuditResult]:
    """D 维度：MCP 工具 --version 检查。

    全部未装 → warning；部分未装 → 逐个 skip（info）。
    """
    mcp_tools = [
        ("jcodemunch-mcp", ["jcodemunch-mcp", "--version"]),
        ("repomix", ["repomix", "--version"]),
        ("headroom", ["headroom", "--version"]),
    ]
    results = []
    missing = []
    for name, cmd in mcp_tools:
        try:
            subprocess.run(
                cmd, capture_output=True, timeout=10, check=True
            )
            results.append(AuditResult("D", "ok", "all", f"{name} 可用"))
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            missing.append(name)
            results.append(
                AuditResult("D", "info", "all", f"{name} 未安装（skip）")
            )

    if len(missing) == len(mcp_tools):
        results = [
            AuditResult(
                "D",
                "warning",
                "all",
                "所有 MCP 工具均未安装"
                "——你可能忘了装 jcodemunch/repomix/headroom",
            )
        ]
    return results


# ── B 维度：技能完整性（info 级 · 哨兵）──────────────────


def dimension_b_skill_integrity(
    tool_filter: Optional[str] = None,
) -> List[AuditResult]:
    """B 维度（info 级）：skills/ 目录下每个 SKILL.md frontmatter 合法。

    info 级：仅验证 inject_rules 正常工作的哨兵，非阻塞。
    跳过无 SKILL.md 的目录（如 shared/）。
    """
    results: List[AuditResult] = []
    skills_dir = os.path.join(PROJECT_ROOT, "skills")
    if not os.path.isdir(skills_dir):
        return [
            AuditResult(
                "B", "warning", "all", f"skills 目录不存在: {skills_dir}"
            )
        ]
    valid = 0
    invalid = 0
    for name in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue  # 跳过 shared/ 等无 SKILL.md 的目录
        with open(skill_md, encoding="utf-8") as f:
            first_line = f.readline()
        if first_line.strip() == "---":
            valid += 1
        else:
            invalid += 1
            results.append(
                AuditResult(
                    "B", "info", "all", f"{name}/SKILL.md 无 frontmatter"
                )
            )
    results.append(
        AuditResult(
            "B",
            "info",
            "all",
            f"技能完整性: {valid} 合法, {invalid} 无 frontmatter",
        )
    )
    return results


# ── C 维度：红线一致性（info 级 · 哨兵）────────────────


REDLINE_MARKERS = [
    "BEGIN LOOPENGINE-MANAGED INTERACTION-RULES",
    "BEGIN LOOPENGINE-MANAGED MCP-RULES",
    "BEGIN LOOPENGINE-MANAGED EVIDENCE-RULES",
    "BEGIN LOOPENGINE-MANAGED SUMMARY-RULES",
    "BEGIN LOOPENGINE-MANAGED VERIFICATION-RULES",
    "BEGIN LOOPENGINE-MANAGED PROGRESS-RULES",
    "BEGIN LOOPENGINE-MANAGED SUBAGENT-RULES",
    "BEGIN LOOPENGINE-MANAGED CONSISTENCY-RULES",
    "BEGIN LOOPENGINE-MANAGED ENGINEERING-RULES",
]


def dimension_c_redline_consistency(
    tool_filter: Optional[str] = None,
) -> List[AuditResult]:
    """C 维度（info 级）：用户级指令文件含 9 条红线 marker。

    info 级：inject_rules.py 已保障安装，此处仅做哨兵。
    """
    results: List[AuditResult] = []
    home = os.path.expanduser("~")
    targets = {
        "claude-code": os.path.join(home, ".claude", "CLAUDE.md"),
        "zcode": os.path.join(home, ".zcode", "AGENTS.md"),
        "cursor": os.path.join(
            home, ".cursor", "rules", "loopengine-interaction.mdc"
        ),
    }
    for tid, path in targets.items():
        if tool_filter and tid != tool_filter:
            continue
        if not os.path.isfile(path):
            results.append(
                AuditResult(
                    "C", "info", tid, f"指令文件不存在: {path}"
                )
            )
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        missing = [m for m in REDLINE_MARKERS if m not in content]
        if missing:
            results.append(
                AuditResult(
                    "C", "info", tid, f"缺少 {len(missing)} 个 marker"
                )
            )
        else:
            results.append(
                AuditResult("C", "ok", tid, "9 条红线 marker 齐全")
            )
    return results


# ── E 维度：版本一致性 ────────────────────────────────


def dimension_e_version_consistency(
    tool_filter: Optional[str] = None,
) -> List[AuditResult]:
    """E 维度：.plugin-template.json::version = package.json::version
    = marketplace.json::plugins[0].version。
    """
    results: List[AuditResult] = []
    template_ver = None
    package_ver = None
    marketplace_ver = None

    tpl_path = os.path.join(PROJECT_ROOT, ".plugin-template.json")
    if os.path.isfile(tpl_path):
        with open(tpl_path, encoding="utf-8") as f:
            template_ver = json.load(f).get("version")

    pkg_path = os.path.join(PROJECT_ROOT, "package.json")
    if os.path.isfile(pkg_path):
        with open(pkg_path, encoding="utf-8") as f:
            package_ver = json.load(f).get("version")

    mp_path = os.path.join(
        PROJECT_ROOT, ".claude-plugin", "marketplace.json"
    )
    if os.path.isfile(mp_path):
        with open(mp_path, encoding="utf-8") as f:
            plugins = json.load(f).get("plugins", [])
            if plugins:
                marketplace_ver = plugins[0].get("version")

    versions = {
        "template": template_ver,
        "package": package_ver,
        "marketplace": marketplace_ver,
    }
    unique = {v for v in versions.values() if v}
    if len(unique) == 1:
        results.append(
            AuditResult("E", "ok", "all", f"版本一致: {template_ver}")
        )
    else:
        results.append(
            AuditResult(
                "E", "warning", "all", f"版本不一致: {versions}"
            )
        )
    return results


# ── F 维度：Schema 合法性 ─────────────────────────────


def dimension_f_schema(
    tool_filter: Optional[str] = None,
) -> List[AuditResult]:
    """F 维度（低）：渲染后 plugin.json 含 compliance 期望字段。

    检查最近一次渲染产物（若存在）。
    """
    results: List[AuditResult] = []
    # 渲染产物可能在 /tmp 或 COMMON_RENDERED_DIR；这里检查项目内是否有 rendered-output
    rendered_base = os.path.join(PROJECT_ROOT, "rendered-output")
    if not os.path.isdir(rendered_base):
        return [
            AuditResult(
                "F",
                "info",
                "all",
                "无渲染产物可检查（先跑 install.sh）",
            )
        ]
    for adapter in TOOL_ADAPTERS:
        if tool_filter and adapter.id != tool_filter:
            continue
        rendered = os.path.join(rendered_base, adapter.output_path)
        if not os.path.isfile(rendered):
            continue
        with open(rendered, encoding="utf-8") as f:
            data = json.load(f)
        if "name" not in data:
            results.append(
                AuditResult(
                    "F", "error", adapter.id, "plugin.json 缺 name 字段"
                )
            )
        elif adapter.compliance == "native" and "hooks" not in data:
            results.append(
                AuditResult(
                    "F",
                    "warning",
                    adapter.id,
                    "native 工具建议有 hooks",
                )
            )
        else:
            results.append(
                AuditResult("F", "ok", adapter.id, "schema 合法")
            )
    return results


# ── 维度分发（B/C/E/F 在 PR-3 实现）──────────────────


def run_dimension(
    dim: str, verbose: bool = False, tool_filter: Optional[str] = None
) -> List[AuditResult]:
    """运行单个维度。"""
    dispatch = {
        "A": dimension_a_tool_deploy,
        "B": dimension_b_skill_integrity,
        "C": dimension_c_redline_consistency,
        "D": dimension_d_mcp_health,
        "E": dimension_e_version_consistency,
        "F": dimension_f_schema,
    }
    handler = dispatch.get(dim)
    if handler:
        return handler(tool_filter)
    return [AuditResult(dim, "error", "all", f"未知维度: {dim}")]


# ── 输出格式化 ────────────────────────────────────────


def format_human(results: List[AuditResult], verbose: bool) -> int:
    """人友好输出。返回退出码。"""
    errors = [r for r in results if r.severity == "error"]
    warnings = [r for r in results if r.severity == "warning"]
    print(
        f"\n🔍 Audit: {len(results)} 项检查, "
        f"{len(errors)} error, {len(warnings)} warning\n"
    )
    for r in results:
        icon = {
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "ok": "✅",
        }.get(r.severity, "?")
        print(f"  {icon} [{r.dimension}] {r.tool}: {r.message}")
        if verbose and r.detail:
            print(f"     {r.detail}")
    return 1 if errors else 0


def main():
    args = sys.argv[1:]
    json_mode = "--json" in args
    verbose = "--verbose" in args
    tool_filter = None
    if "--tool" in args:
        idx = args.index("--tool")
        tool_filter = args[idx + 1] if idx + 1 < len(args) else None

    dimensions = ["A", "B", "C", "D", "E", "F"]
    all_results: List[AuditResult] = []
    for dim in dimensions:
        all_results.extend(run_dimension(dim, verbose, tool_filter))

    if json_mode:
        print(
            json.dumps(
                [
                    {
                        "dimension": r.dimension,
                        "severity": r.severity,
                        "tool": r.tool,
                        "message": r.message,
                        "detail": r.detail,
                    }
                    for r in all_results
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        code = format_human(all_results, verbose)
        sys.exit(code)


if __name__ == "__main__":
    main()

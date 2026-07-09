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


# ── 维度分发（B/C/E/F 在 PR-3 实现）──────────────────


def run_dimension(
    dim: str, verbose: bool = False, tool_filter: Optional[str] = None
) -> List[AuditResult]:
    """运行单个维度。"""
    if dim == "A":
        return dimension_a_tool_deploy(tool_filter)
    elif dim == "D":
        return dimension_d_mcp_health(tool_filter)
    # B/C/E/F 在 PR-3 实现
    return [
        AuditResult(dim, "info", "all", f"维度 {dim} 尚未实现（PR-3）")
    ]


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

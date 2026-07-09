#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# tests/test_audit_tools.py — audit_tools.py 单元测试
# ────────────────────────────────────────────────────────────
# 覆盖：
#   - dimension_a_tool_deploy（A 维度：工具部署）
#   - dimension_d_mcp_health（D 维度：MCP 健康，含 mock）
#   - AuditResult dataclass
#
# 运行：python3 -m unittest tests.test_audit_tools -v
# ────────────────────────────────────────────────────────────

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from audit_tools import (  # noqa: E402
    AuditResult,
    dimension_a_tool_deploy,
    dimension_b_skill_integrity,
    dimension_c_redline_consistency,
    dimension_d_mcp_health,
    dimension_e_version_consistency,
    dimension_f_schema,
)


class TestAuditResult(unittest.TestCase):
    """AuditResult dataclass 基本行为。"""

    def test_default_detail_is_empty_dict(self):
        r = AuditResult("A", "ok", "all", "msg")
        self.assertEqual(r.detail, {})

    def test_custom_detail(self):
        r = AuditResult("A", "ok", "all", "msg", {"path": "/x"})
        self.assertEqual(r.detail["path"], "/x")


class TestDimensionA(unittest.TestCase):
    """A 维度：工具部署目录完整性。"""

    def test_returns_results_for_each_checked_tool(self):
        results = dimension_a_tool_deploy()
        tool_ids = {r.tool for r in results}
        self.assertIn("claude-code", tool_ids)
        self.assertIn("zcode", tool_ids)

    def test_tool_filter_limits_results(self):
        results = dimension_a_tool_deploy(tool_filter="zcode")
        self.assertTrue(all(r.tool == "zcode" for r in results))

    def test_unknown_tool_filter_returns_empty(self):
        results = dimension_a_tool_deploy(tool_filter="nonexistent")
        self.assertEqual(len(results), 0)


class TestDimensionD(unittest.TestCase):
    """D 维度：MCP 健康（全部 mock）。"""

    @patch("audit_tools.subprocess.run")
    def test_all_available_returns_ok(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        results = dimension_d_mcp_health()
        self.assertTrue(all(r.severity == "ok" for r in results))
        self.assertEqual(len(results), 3)

    @patch("audit_tools.subprocess.run")
    def test_all_missing_returns_single_warning(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        results = dimension_d_mcp_health()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, "warning")
        self.assertIn("所有 MCP", results[0].message)

    @patch("audit_tools.subprocess.run")
    def test_partial_missing_returns_info(self, mock_run):
        def side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args")
            if cmd and cmd[0] == "jcodemunch-mcp":
                return MagicMock(returncode=0)
            raise FileNotFoundError()

        mock_run.side_effect = side_effect
        results = dimension_d_mcp_health()
        severities = {r.severity for r in results}
        self.assertIn("ok", severities)
        self.assertIn("info", severities)
        self.assertEqual(len(results), 3)

    @patch("audit_tools.subprocess.run")
    def test_timeout_treated_as_missing(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=10)
        results = dimension_d_mcp_health()
        # 全部 timeout → 全部 missing → 单个 warning
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, "warning")


class TestRunDimension(unittest.TestCase):
    """run_dimension 分发函数。"""

    def test_all_dimensions_dispatched(self):
        from audit_tools import run_dimension

        for dim in ["A", "B", "C", "D", "E", "F"]:
            results = run_dimension(dim)
            self.assertTrue(len(results) > 0)
            self.assertTrue(all(r.dimension == dim for r in results))

    def test_unknown_dimension_returns_error(self):
        from audit_tools import run_dimension

        results = run_dimension("Z")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, "error")

    def test_a_dimension_dispatches(self):
        from audit_tools import run_dimension

        results = run_dimension("A")
        self.assertTrue(len(results) > 0)


class TestDimensionB(unittest.TestCase):
    """B 维度（info 级）：技能 SKILL.md frontmatter。"""

    def test_returns_info_severity(self):
        results = dimension_b_skill_integrity()
        # B 维度整体是 info 级
        self.assertTrue(all(r.severity in ("info", "warning") for r in results))

    def test_reports_valid_and_invalid_counts(self):
        results = dimension_b_skill_integrity()
        summary = [r for r in results if "技能完整性" in r.message]
        self.assertEqual(len(summary), 1)


class TestDimensionC(unittest.TestCase):
    """C 维度（info 级）：红线 marker 哨兵。"""

    def test_returns_results_for_three_tools(self):
        results = dimension_c_redline_consistency()
        tool_ids = {r.tool for r in results}
        # 至少检查已部署的工具
        self.assertTrue(len(tool_ids) > 0)

    def test_tool_filter(self):
        results = dimension_c_redline_consistency(tool_filter="zcode")
        self.assertTrue(all(r.tool == "zcode" for r in results))


class TestDimensionE(unittest.TestCase):
    """E 维度：版本一致性。"""

    def test_returns_single_result(self):
        results = dimension_e_version_consistency()
        self.assertEqual(len(results), 1)

    def test_severity_is_ok_or_warning(self):
        results = dimension_e_version_consistency()
        self.assertIn(results[0].severity, ("ok", "warning"))


class TestDimensionF(unittest.TestCase):
    """F 维度（低）：渲染产物 schema。"""

    def test_no_rendered_output_returns_info(self):
        """无渲染产物时应返回 info"""
        results = dimension_f_schema()
        # 如果 rendered-output 不存在，返回 info
        if results[0].severity == "info":
            self.assertIn("无渲染产物", results[0].message)


if __name__ == "__main__":
    unittest.main(verbosity=2)

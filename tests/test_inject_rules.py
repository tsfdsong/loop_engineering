#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# tests/test_inject_rules.py — inject_rules.py 单元测试
# ────────────────────────────────────────────────────────────
# 覆盖 2 个核心函数：
#   - parse_marker  （从块文本提取 marker 类型）
#   - inject_block  （替换或追加 marker 块）
#
# 运行：python3 -m unittest tests.test_inject_rules -v
# ────────────────────────────────────────────────────────────

import os
import sys
import unittest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from inject_rules import inject_block, parse_marker  # noqa: E402


class TestParseMarker(unittest.TestCase):
    """parse_marker: 从 BEGIN LOOPENGINE-MANAGED 标签提取 marker 类型。"""

    def test_extract_simple_marker(self):
        block = (
            "<!-- BEGIN LOOPENGINE-MANAGED INTERACTION-RULES -->\n"
            "内容\n"
            "<!-- END LOOPENGINE-MANAGED INTERACTION-RULES -->"
        )
        self.assertEqual(parse_marker(block), "INTERACTION-RULES")

    def test_extract_complex_marker_with_dash(self):
        block = (
            "<!-- BEGIN LOOPENGINE-MANAGED MCP-RULES -->\n"
            "<!-- END LOOPENGINE-MANAGED MCP-RULES -->"
        )
        self.assertEqual(parse_marker(block), "MCP-RULES")

    def test_extract_long_marker_name(self):
        block = (
            "<!-- BEGIN LOOPENGINE-MANAGED ENGINEERING-RULES -->\n"
            "<!-- END LOOPENGINE-MANAGED ENGINEERING-RULES -->"
        )
        self.assertEqual(parse_marker(block), "ENGINEERING-RULES")

    def test_returns_none_if_no_marker(self):
        self.assertIsNone(parse_marker("普通文本，无 marker"))
        self.assertIsNone(parse_marker(""))
        self.assertIsNone(parse_marker("<!-- BEGIN OTHER-MANAGED X -->"))


class TestInjectBlock(unittest.TestCase):
    """inject_block: 替换或追加 marker 块。"""

    def test_append_when_no_existing_block(self):
        content = "# My Doc\n"
        block = (
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\n"
            "rules\n"
            "<!-- END LOOPENGINE-MANAGED X -->"
        )
        result, action = inject_block(content, "X", block)
        self.assertEqual(action, "APPENDED")
        self.assertIn(block, result)

    def test_update_existing_block(self):
        old_block = (
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\n"
            "old\n"
            "<!-- END LOOPENGINE-MANAGED X -->"
        )
        new_block = (
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\n"
            "new\n"
            "<!-- END LOOPENGINE-MANAGED X -->"
        )
        result, action = inject_block(old_block, "X", new_block)
        self.assertEqual(action, "UPDATED")
        self.assertIn("new", result)
        self.assertNotIn("old", result)

    def test_preserves_other_content_on_update(self):
        content = (
            "# Header\n\n"
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\n"
            "old\n"
            "<!-- END LOOPENGINE-MANAGED X -->\n\n"
            "# Footer"
        )
        new_block = (
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\n"
            "new\n"
            "<!-- END LOOPENGINE-MANAGED X -->"
        )
        result, action = inject_block(content, "X", new_block)
        self.assertEqual(action, "UPDATED")
        self.assertIn("# Header", result)
        self.assertIn("# Footer", result)

    def test_multiple_different_markers_coexist(self):
        """不同 marker 的块应共存，互不影响"""
        content = (
            "<!-- BEGIN LOOPENGINE-MANAGED A -->\n"
            "a content\n"
            "<!-- END LOOPENGINE-MANAGED A -->"
        )
        block_b = (
            "<!-- BEGIN LOOPENGINE-MANAGED B -->\n"
            "b content\n"
            "<!-- END LOOPENGINE-MANAGED B -->"
        )
        result, action = inject_block(content, "B", block_b)
        self.assertEqual(action, "APPENDED")
        self.assertIn("LOOPENGINE-MANAGED A", result)
        self.assertIn("LOOPENGINE-MANAGED B", result)

    def test_append_adds_blank_line_separator(self):
        """追加模式应保证块前有足够空行"""
        content = "# Doc without trailing newline"
        block = (
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\n"
            "rules\n"
            "<!-- END LOOPENGINE-MANAGED X -->"
        )
        result, action = inject_block(content, "X", block)
        self.assertEqual(action, "APPENDED")
        # 内容和块之间应有空行
        self.assertIn("\n\n<!-- BEGIN", result)

    def test_handles_windows_line_endings(self):
        """Windows \r\n 换行不应破坏 marker 匹配"""
        content = "# Doc\r\n\r\n"
        block = (
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\r\n"
            "rules\r\n"
            "<!-- END LOOPENGINE-MANAGED X -->"
        )
        result, action = inject_block(content, "X", block)
        self.assertEqual(action, "APPENDED")

    def test_empty_content_appends_block(self):
        """空内容应直接追加块"""
        block = (
            "<!-- BEGIN LOOPENGINE-MANAGED X -->\n"
            "rules\n"
            "<!-- END LOOPENGINE-MANAGED X -->"
        )
        result, action = inject_block("", "X", block)
        self.assertEqual(action, "APPENDED")
        self.assertIn(block, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

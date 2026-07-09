#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# tests/test_merge_mcp_config.py — merge_mcp_config.py 单元测试
# ────────────────────────────────────────────────────────────
# 覆盖 4 个核心函数：
#   - merge_zcode       （ZCode 嵌套 mcp.servers schema）
#   - merge_cursor      （Cursor 平铺 mcpServers schema）
#   - _read_json        （容错读取）
#   - _atomic_write_json（原子写）
#
# 运行：python3 -m unittest tests.test_merge_mcp_config -v
# ────────────────────────────────────────────────────────────

import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from merge_mcp_config import (  # noqa: E402
    _atomic_write_json,
    _read_json,
    merge_cursor,
    merge_zcode,
)


class TestReadJson(unittest.TestCase):
    """_read_json: 容错读取（不存在→空 dict，损坏→空 dict）。"""

    def test_read_valid_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            try:
                result = _read_json(f.name)
                self.assertEqual(result, {"key": "value"})
            finally:
                os.unlink(f.name)

    def test_read_utf8_content(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"中文": "测试"}, f)
            f.flush()
            try:
                result = _read_json(f.name)
                self.assertEqual(result, {"中文": "测试"})
            finally:
                os.unlink(f.name)

    def test_missing_file_returns_empty_dict(self):
        """文件不存在应返回空 dict，不抛异常"""
        result = _read_json("/nonexistent/path/that/does/not/exist.json")
        self.assertEqual(result, {})

    def test_corrupt_json_returns_empty_dict(self):
        """损坏 JSON 应返回空 dict"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("{invalid json content")
            f.flush()
            try:
                result = _read_json(f.name)
                self.assertEqual(result, {})
            finally:
                os.unlink(f.name)


class TestMergeZcode(unittest.TestCase):
    """merge_zcode: ZCode 桌面版嵌套 mcp.servers schema。"""

    def test_creates_nested_mcp_servers_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "config.json")
            with open(cfg, "w") as f:
                json.dump({}, f)
            result = merge_zcode(cfg, "/path/jcodemunch-mcp", "/path/repomix")
            self.assertIn("mcp", result)
            self.assertIn("servers", result["mcp"])
            self.assertEqual(
                result["mcp"]["servers"]["jcodemunch"]["command"],
                "/path/jcodemunch-mcp",
            )
            self.assertEqual(result["mcp"]["servers"]["jcodemunch"]["type"], "stdio")
            self.assertEqual(
                result["mcp"]["servers"]["jcodemunch"]["args"], ["serve"]
            )

    def test_overwrites_existing_servers(self):
        """已存在的 server 应被覆盖（路径更新时同步）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "config.json")
            with open(cfg, "w") as f:
                json.dump(
                    {"mcp": {"servers": {"jcodemunch": {"command": "old-path"}}}},
                    f,
                )
            result = merge_zcode(cfg, "/new/jcodemunch-mcp", "/new/repomix")
            self.assertEqual(
                result["mcp"]["servers"]["jcodemunch"]["command"],
                "/new/jcodemunch-mcp",
            )

    def test_clears_legacy_headroom_entry(self):
        """v1.2.2 之前的空 headroom entry 应被清除"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "config.json")
            with open(cfg, "w") as f:
                json.dump(
                    {"mcp": {"servers": {"headroom": {"command": "old-headroom"}}}},
                    f,
                )
            result = merge_zcode(cfg, "/path/jcode", "/path/repomix")
            self.assertNotIn("headroom", result["mcp"]["servers"])

    def test_preserves_other_top_level_fields(self):
        """合并应保留用户其他顶层字段"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "config.json")
            with open(cfg, "w") as f:
                json.dump({"plugins": {"enabledPlugins": {}}, "other": "keep"}, f)
            result = merge_zcode(cfg, "/path/jcode", "/path/repomix")
            self.assertEqual(result["other"], "keep")
            self.assertIn("plugins", result)


class TestMergeCursor(unittest.TestCase):
    """merge_cursor: Cursor IDE 平铺 mcpServers schema（无 type 字段）。"""

    def test_creates_top_level_mcpServers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "mcp.json")
            with open(cfg, "w") as f:
                json.dump({}, f)
            result = merge_cursor(cfg, "/path/jcode", "/path/repomix", "/path/headroom")
            self.assertIn("mcpServers", result)
            self.assertEqual(
                result["mcpServers"]["jcodemunch"]["command"], "/path/jcode"
            )
            # Cursor 不应有 type 字段
            self.assertNotIn("type", result["mcpServers"]["jcodemunch"])

    def test_headroom_optional_empty_skips(self):
        """headroom 为空字符串时应跳过该 entry"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "mcp.json")
            with open(cfg, "w") as f:
                json.dump({}, f)
            result = merge_cursor(cfg, "/path/jcode", "/path/repomix", "")
            self.assertNotIn("headroom", result["mcpServers"])

    def test_headroom_empty_clears_legacy(self):
        """headroom 为空时应清理旧 entry"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "mcp.json")
            with open(cfg, "w") as f:
                json.dump(
                    {"mcpServers": {"headroom": {"command": "old"}}}, f
                )
            result = merge_cursor(cfg, "/path/jcode", "/path/repomix", "")
            self.assertNotIn("headroom", result["mcpServers"])

    def test_headroom_present_writes_entry(self):
        """headroom 有路径时应写入 entry"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = os.path.join(tmpdir, "mcp.json")
            with open(cfg, "w") as f:
                json.dump({}, f)
            result = merge_cursor(cfg, "/j", "/r", "/h")
            self.assertEqual(result["mcpServers"]["headroom"]["command"], "/h")
            self.assertEqual(result["mcpServers"]["headroom"]["args"], ["mcp", "serve"])


class TestAtomicWriteJson(unittest.TestCase):
    """_atomic_write_json: 原子写（先 .tmp 再 rename）。"""

    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "out.json")
            _atomic_write_json(path, {"a": 1})
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                self.assertEqual(json.load(f), {"a": 1})

    def test_write_ensures_utf8(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "out.json")
            _atomic_write_json(path, {"中文": "值"})
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("中文", content)

    def test_write_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "out.json")
            _atomic_write_json(path, {"old": 1})
            _atomic_write_json(path, {"new": 2})
            with open(path) as f:
                self.assertEqual(json.load(f), {"new": 2})

    def test_no_tmp_file_left_after_write(self):
        """原子写后不应残留 .tmp 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "out.json")
            _atomic_write_json(path, {"a": 1})
            self.assertFalse(os.path.exists(path + ".tmp"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# tests/test_register_zcode_marketplace.py — register_zcode_marketplace.py 测试
# ────────────────────────────────────────────────────────────
# 覆盖：
#   - _read_json / _write_json 往返
#   - main() 的 marketplace 注册逻辑（idempotent）
#
# 运行：python3 -m unittest tests.test_register_zcode_marketplace -v
# ────────────────────────────────────────────────────────────

import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from register_zcode_marketplace import _read_json, _write_json  # noqa: E402


class TestRegisterMarketplace(unittest.TestCase):
    """marketplace 注册逻辑（通过 main 函数行为间接测试）。"""

    def _make_empty_known(self):
        return {"version": 1, "marketplaces": []}

    def test_read_write_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "known.json")
            original = self._make_empty_known()
            _write_json(path, original)
            result = _read_json(path)
            self.assertEqual(result, original)

    def test_write_creates_parent_dir(self):
        """_write_json 应自动创建父目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nested", "deep", "known.json")
            _write_json(path, {"a": 1})
            self.assertTrue(os.path.exists(path))

    def test_write_utf8_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "known.json")
            _write_json(path, {"描述": "中文测试"})
            result = _read_json(path)
            self.assertEqual(result["描述"], "中文测试")


class TestMainIdempotent(unittest.TestCase):
    """main() 幂等性：重复注册同一 marketplace 不产生重复条目。"""

    def test_main_registers_marketplace(self):
        """首次注册应追加 marketplace 条目"""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            known_path = os.path.join(tmpdir, "known.json")
            _write_json(known_path, {"version": 1, "marketplaces": []})
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_marketplace.py"),
                 known_path, "test-mp"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0)
            data = _read_json(known_path)
            ids = [m["id"] for m in data["marketplaces"]]
            self.assertIn("test-mp", ids)

    def test_main_idempotent_on_rerun(self):
        """重复注册同一 marketplace 应不产生重复"""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            known_path = os.path.join(tmpdir, "known.json")
            _write_json(known_path, {"version": 1, "marketplaces": []})
            # 跑两次
            for _ in range(2):
                subprocess.run(
                    [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_marketplace.py"),
                     known_path, "test-mp"],
                    capture_output=True, text=True,
                )
            data = _read_json(known_path)
            ids = [m["id"] for m in data["marketplaces"]]
            self.assertEqual(ids.count("test-mp"), 1)

    def test_main_exit_code_2_on_wrong_args(self):
        """参数不足应返回 exit code 2"""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_marketplace.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# tests/test_register_zcode_plugin.py — register_zcode_plugin.py 测试
# ────────────────────────────────────────────────────────────
# 覆盖：
#   - main() 的 enabledPlugins 注册逻辑（idempotent）
#   - exit code 正确性
#
# 运行：python3 -m unittest tests.test_register_zcode_plugin -v
# ────────────────────────────────────────────────────────────

import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from register_zcode_plugin import _read_json, _write_json  # noqa: E402


class TestRegisterPlugin(unittest.TestCase):
    """plugin 注册逻辑（通过 main 函数行为间接测试）。"""

    def test_main_enables_plugin(self):
        """注册 plugin 应在 enabledPlugins 写入 true"""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = os.path.join(tmpdir, "config.json")
            _write_json(cfg_path, {"plugins": {"enabledPlugins": {}}})
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_plugin.py"),
                 cfg_path, "loopengine", "test-mp"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0)
            data = _read_json(cfg_path)
            self.assertTrue(data["plugins"]["enabledPlugins"]["loopengine@test-mp"])

    def test_main_overwrites_false_to_true(self):
        """已禁用(False)的 plugin 重新启用应覆盖为 True"""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = os.path.join(tmpdir, "config.json")
            _write_json(cfg_path, {
                "plugins": {"enabledPlugins": {"loopengine@test-mp": False}}
            })
            subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_plugin.py"),
                 cfg_path, "loopengine", "test-mp"],
                capture_output=True, text=True,
            )
            data = _read_json(cfg_path)
            self.assertTrue(data["plugins"]["enabledPlugins"]["loopengine@test-mp"])

    def test_main_idempotent_when_already_true(self):
        """已 enabled 的 plugin 重复注册不应报错"""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = os.path.join(tmpdir, "config.json")
            _write_json(cfg_path, {"plugins": {"enabledPlugins": {}}})
            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_plugin.py"),
                     cfg_path, "loopengine", "test-mp"],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0)
            data = _read_json(cfg_path)
            self.assertTrue(data["plugins"]["enabledPlugins"]["loopengine@test-mp"])

    def test_main_creates_plugins_structure_if_missing(self):
        """config.json 无 plugins 键时应自动创建结构"""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = os.path.join(tmpdir, "config.json")
            _write_json(cfg_path, {"other": "keep"})
            subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_plugin.py"),
                 cfg_path, "loopengine", "test-mp"],
                capture_output=True, text=True,
            )
            data = _read_json(cfg_path)
            self.assertIn("plugins", data)
            self.assertIn("enabledPlugins", data["plugins"])
            self.assertTrue(data["plugins"]["enabledPlugins"]["loopengine@test-mp"])
            # 保留其他字段
            self.assertEqual(data["other"], "keep")

    def test_main_exit_code_2_on_wrong_args(self):
        """参数不足应返回 exit code 2"""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "register_zcode_plugin.py"),
             "/tmp/x"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

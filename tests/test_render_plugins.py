#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# tests/test_render_plugins.py — render_plugins.py 单元测试
# ────────────────────────────────────────────────────────────
# 覆盖 4 个核心函数：
#   - deep_merge       （深合并 + _comment 过滤）
#   - strip_meta       （递归删除 _ 前缀元数据）
#   - render_plugin_json  （单 manifest 渲染）
#   - render_marketplace  （marketplace 特殊 schema + version 同步）
#
# 运行：python -m pytest tests/test_render_plugins.py -v
#       python -m unittest tests.test_render_plugins -v
# ────────────────────────────────────────────────────────────

import json
import os
import sys
import tempfile
import unittest

# 添加 scripts/ 到 sys.path（让 import render_plugins 可工作）
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from render_plugins import (  # noqa: E402
    deep_merge,
    render_marketplace,
    render_plugin_json,
    strip_meta,
)


class TestDeepMerge(unittest.TestCase):
    """深合并：overlay 字段覆盖 base 字段；dict 递归合并。"""

    def test_simple_scalar_override(self):
        result = deep_merge({"a": 1, "b": 2}, {"b": 3, "c": 4})
        self.assertEqual(result, {"a": 1, "b": 3, "c": 4})

    def test_nested_dict_merge(self):
        result = deep_merge(
            {"x": {"a": 1, "b": 2}, "y": 5},
            {"x": {"b": 3, "c": 4}, "z": 6},
        )
        self.assertEqual(result, {"x": {"a": 1, "b": 3, "c": 4}, "y": 5, "z": 6})

    def test_list_replaces_not_concat(self):
        """list 应完全替换，不拼接（避免意外合并）"""
        result = deep_merge({"items": [1, 2, 3]}, {"items": [4, 5]})
        self.assertEqual(result, {"items": [4, 5]})

    def test_skip_underscore_keys_in_overlay(self):
        """overlay 中的 _comment 等元数据应被丢弃"""
        result = deep_merge({"a": 1}, {"_comment": "metadata", "b": 2})
        self.assertNotIn("_comment", result)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_dict_in_dict_underscore_filtered(self):
        """嵌套 dict 中 overlay 的 _comment 应被过滤；base 的 _comment 保留
        （base 的 _comment 由 strip_meta() 在 deep_merge 调用前处理）"""
        result = deep_merge(
            {"a": {"b": 1}},
            {"a": {"_comment": "ignored", "c": 2}},
        )
        self.assertNotIn("_comment", result["a"])
        self.assertEqual(result["a"], {"b": 1, "c": 2})


class TestStripMeta(unittest.TestCase):
    """递归删除所有 _comment / _xxx 元数据字段。"""

    def test_strip_top_level(self):
        result = strip_meta({"_comment": "x", "a": 1, "_meta": "y"})
        self.assertNotIn("_comment", result)
        self.assertNotIn("_meta", result)
        self.assertEqual(result, {"a": 1})

    def test_strip_nested_dict(self):
        result = strip_meta({"a": {"_comment": "x", "b": 1}})
        self.assertNotIn("_comment", result["a"])
        self.assertEqual(result, {"a": {"b": 1}})

    def test_strip_in_list(self):
        result = strip_meta({"items": [{"_comment": "x", "a": 1}, {"b": 2}]})
        self.assertNotIn("_comment", result["items"][0])
        self.assertEqual(result, {"items": [{"a": 1}, {"b": 2}]})

    def test_strip_in_deeply_nested(self):
        result = strip_meta(
            {"a": {"b": {"c": {"_comment": "x", "d": 1}}}}
        )
        self.assertNotIn("_comment", result["a"]["b"]["c"])
        self.assertEqual(result["a"]["b"]["c"], {"d": 1})


class TestRenderPluginJson(unittest.TestCase):
    """单工具 plugin.json 渲染。"""

    def _write_json(self, path: str, data: dict) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_basic_render_with_override(self):
        """基础场景：overlay 覆盖 template"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 不需要 template 文件，只需 in-memory dict
            template = {"name": "loopengine", "version": "1.0.0"}
            overlay_path = os.path.join(tmpdir, "overlay.json")
            self._write_json(overlay_path, {"version": "2.0.0"})
            out_path = os.path.join(tmpdir, "out.json")

            self.assertTrue(render_plugin_json(template, overlay_path, out_path, "test"))

            with open(out_path) as f:
                data = json.load(f)
            self.assertEqual(data, {"name": "loopengine", "version": "2.0.0"})

    def test_overlay_adds_new_field(self):
        """overlay 可加新字段"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = {"name": "x", "version": "1.0.0"}
            overlay_path = os.path.join(tmpdir, "overlay.json")
            self._write_json(overlay_path, {"hooks": "./hooks/run.sh"})
            out_path = os.path.join(tmpdir, "out.json")

            render_plugin_json(template, overlay_path, out_path, "test")

            with open(out_path) as f:
                data = json.load(f)
            self.assertEqual(data["hooks"], "./hooks/run.sh")

    def test_overlay_strips_meta_keys(self):
        """overlay 的 _comment 不应进入输出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = {"name": "x"}
            overlay_path = os.path.join(tmpdir, "overlay.json")
            self._write_json(overlay_path, {"_comment": "meta", "version": "1.0.0"})
            out_path = os.path.join(tmpdir, "out.json")

            render_plugin_json(template, overlay_path, out_path, "test")

            with open(out_path) as f:
                data = json.load(f)
            self.assertNotIn("_comment", data)
            self.assertEqual(data["version"], "1.0.0")

    def test_missing_overlay_returns_false(self):
        """overlay 不存在时返回 False，不写文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.json")
            result = render_plugin_json({}, "/nonexistent/path.json", out_path, "test")
            self.assertFalse(result)
            self.assertFalse(os.path.exists(out_path))

    def test_creates_parent_directory(self):
        """output 父目录不存在时自动创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = {"name": "x"}
            overlay_path = os.path.join(tmpdir, "overlay.json")
            self._write_json(overlay_path, {"v": 1})
            out_path = os.path.join(tmpdir, "deep", "nested", "dir", "out.json")

            render_plugin_json(template, overlay_path, out_path, "test")
            self.assertTrue(os.path.exists(out_path))


class TestRenderMarketplace(unittest.TestCase):
    """marketplace.json 特殊 schema：含 plugins[] 数组，version 同步自 template。"""

    def _write_json(self, path: str, data: dict) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_version_sync_from_template(self):
        """template.version 应覆盖 plugins[].version"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp_path = os.path.join(tmpdir, "mp.json")
            self._write_json(mp_path, {"plugins": [{"name": "x", "version": "old"}]})
            out_path = os.path.join(tmpdir, "out.json")
            template = {"version": "1.0.0", "description": "new desc"}

            render_marketplace(template, mp_path, out_path, "test")

            with open(out_path) as f:
                data = json.load(f)
            self.assertEqual(data["plugins"][0]["version"], "1.0.0")
            self.assertEqual(data["plugins"][0]["description"], "new desc")

    def test_strips_meta_in_plugins(self):
        """plugins[] 内的 _comment 应被 strip"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp_path = os.path.join(tmpdir, "mp.json")
            self._write_json(
                mp_path,
                {
                    "plugins": [
                        {"_comment": "meta", "name": "x", "version": "1.0.0"}
                    ]
                },
            )
            out_path = os.path.join(tmpdir, "out.json")
            template = {"version": "1.0.0"}

            render_marketplace(template, mp_path, out_path, "test")

            with open(out_path) as f:
                data = json.load(f)
            self.assertNotIn("_comment", data["plugins"][0])

    def test_missing_marketplace_returns_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.json")
            result = render_marketplace(
                {"version": "1.0.0"},
                "/nonexistent/mp.json",
                out_path,
                "test",
            )
            self.assertFalse(result)
            self.assertFalse(os.path.exists(out_path))


class TestIntegration(unittest.TestCase):
    """集成测试：模拟 .plugin-template.json + 5 个 overlay 的实际渲染场景。"""

    def test_full_render_simulation(self):
        """完整渲染流程模拟"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 项目结构
            project_root = os.path.join(tmpdir, "project")
            out_dir = os.path.join(tmpdir, "out")
            os.makedirs(os.path.join(project_root, ".claude-plugin"))
            os.makedirs(os.path.join(project_root, ".codex-plugin"))

            # 模板
            template = {
                "name": "loopengine",
                "version": "1.0.0",
                "mcpServers": {
                    "jcodemunch": {"command": "jcodemunch-mcp", "args": ["serve"]},
                },
            }
            template_path = os.path.join(project_root, ".plugin-template.json")
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(template, f)

            # Claude overlay（特异字段 hooks）
            claude_overlay = {
                "_comment": "claude 特异",
                "hooks": "./hooks/hooks.json",
            }
            with open(
                os.path.join(project_root, ".claude-plugin", "plugin.json"), "w"
            ) as f:
                json.dump(claude_overlay, f)

            # Codex overlay（特异字段 skills + hooks）
            codex_overlay = {
                "_comment": "codex 特异",
                "skills": "./skills/",
                "hooks": "./hooks/hooks-codex.json",
            }
            with open(
                os.path.join(project_root, ".codex-plugin", "plugin.json"), "w"
            ) as f:
                json.dump(codex_overlay, f)

            # 渲染
            template_loaded = strip_meta(json.load(open(template_path)))
            self.assertTrue(
                render_plugin_json(
                    template_loaded,
                    os.path.join(project_root, ".claude-plugin", "plugin.json"),
                    os.path.join(out_dir, "claude-plugin", "plugin.json"),
                    "claude-plugin/plugin.json",
                )
            )
            self.assertTrue(
                render_plugin_json(
                    template_loaded,
                    os.path.join(project_root, ".codex-plugin", "plugin.json"),
                    os.path.join(out_dir, "codex-plugin", "plugin.json"),
                    "codex-plugin/plugin.json",
                )
            )

            # 验证输出
            claude_out = json.load(
                open(os.path.join(out_dir, "claude-plugin", "plugin.json"))
            )
            self.assertEqual(claude_out["name"], "loopengine")
            self.assertEqual(claude_out["version"], "1.0.0")
            self.assertEqual(claude_out["hooks"], "./hooks/hooks.json")
            self.assertNotIn("_comment", claude_out)
            # mcpServers 应从 template 继承
            self.assertIn("jcodemunch", claude_out["mcpServers"])

            codex_out = json.load(
                open(os.path.join(out_dir, "codex-plugin", "plugin.json"))
            )
            self.assertEqual(codex_out["skills"], "./skills/")
            self.assertEqual(codex_out["hooks"], "./hooks/hooks-codex.json")


from render_plugins import (  # noqa: E402
    TOOL_ADAPTERS,
    ToolAdapter,
    render_adapter,
)


class TestToolAdapter(unittest.TestCase):
    """ToolAdapter 注册表测试（v1.4 PR-1）。"""

    def test_tool_adapters_has_5_active_entries(self):
        """TOOL_ADAPTERS 应有 5 个启用条目（Kimi 注释掉）"""
        self.assertEqual(len(TOOL_ADAPTERS), 5)

    def test_zcode_adapter_has_activate_callable(self):
        """ZCode 必须有 activate 回调"""
        zcode = next(a for a in TOOL_ADAPTERS if a.id == "zcode")
        self.assertIsNotNone(zcode.activate)

    def test_claude_adapter_has_marketplace_extra_output(self):
        """Claude Code 必须有 marketplace.json extra_output"""
        cc = next(a for a in TOOL_ADAPTERS if a.id == "claude-code")
        self.assertTrue(
            any(e.get("kind") == "marketplace" for e in cc.extra_outputs)
        )

    def test_zcode_adapter_drops_mcpServers(self):
        """ZCode 的 drop_fields 应含 mcpServers"""
        zcode = next(a for a in TOOL_ADAPTERS if a.id == "zcode")
        self.assertIn("mcpServers", zcode.drop_fields)

    def test_render_adapter_drops_fields(self):
        """render_adapter 应剥离 drop_fields 中的字段"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = {"name": "x", "version": "1.0", "mcpServers": {"s": {}}}
            overlay_dir = os.path.join(tmpdir, ".zcode-plugin")
            overlay_path = os.path.join(overlay_dir, "plugin.json")
            os.makedirs(overlay_dir)
            with open(overlay_path, "w") as f:
                json.dump({"skills": "./skills/"}, f)
            adapter = ToolAdapter(
                id="test",
                label="Test",
                compliance="adapter-backed",
                overlay_path=".zcode-plugin/plugin.json",
                output_path="out.json",
                drop_fields=["mcpServers"],
            )
            result = render_adapter(template, adapter, tmpdir, tmpdir)
            self.assertTrue(result)
            with open(os.path.join(tmpdir, "out.json")) as f:
                data = json.load(f)
            self.assertNotIn("mcpServers", data)
            self.assertIn("skills", data)

    def test_render_adapter_returns_false_for_missing_overlay(self):
        """overlay 不存在时返回 False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = ToolAdapter(
                id="test",
                label="Test",
                compliance="adapter-backed",
                overlay_path=".nonexistent/plugin.json",
                output_path="out.json",
            )
            result = render_adapter({}, adapter, tmpdir, tmpdir)
            self.assertFalse(result)

    def test_all_adapters_have_unique_ids(self):
        """所有 adapter 的 id 应唯一"""
        ids = [a.id for a in TOOL_ADAPTERS]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_zcode_runner_module():
    module_name = "zcode_runner_test_module"
    if module_name in sys.modules:
        return sys.modules[module_name]

    stub_git_ops = types.ModuleType("git_ops")
    stub_state_manager = types.ModuleType("state_manager")
    stub_state_manager._global_locks_guard = object()
    sys.modules.setdefault("git_ops", stub_git_ops)
    sys.modules.setdefault("state_manager", stub_state_manager)

    module_path = ROOT / "skills" / "go" / "scripts" / "zcode_runner.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


def load_orchestrator_module():
    module_name = "orchestrator_test_module"
    if module_name in sys.modules:
        return sys.modules[module_name]

    stub_complexity_evaluator = types.ModuleType("complexity_evaluator")
    stub_state_manager = types.ModuleType("state_manager")
    stub_state_manager.TASK_PENDING = "pending"
    stub_git_ops = types.ModuleType("git_ops")
    stub_zcode_runner = types.ModuleType("zcode_runner")

    sys.modules.setdefault("complexity_evaluator", stub_complexity_evaluator)
    sys.modules.setdefault("state_manager", stub_state_manager)
    sys.modules.setdefault("git_ops", stub_git_ops)
    sys.modules.setdefault("zcode_runner", stub_zcode_runner)

    module_path = ROOT / "skills" / "go" / "scripts" / "orchestrator.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


class TestOrchV2Assets(unittest.TestCase):
    def test_reference_asset_paths_exist(self):
        required = [
            "skills/orch/references/intent-schema.json",
            "skills/orch/references/capability-registry.yaml",
            "skills/orch/references/dag-rules.yaml",
            "skills/orch/references/executor-contracts/direct-skill.json",
            "skills/orch/references/executor-contracts/loop.json",
            "skills/orch/references/executor-contracts/go.json",
            "skills/orch/references/families/review.yaml",
            "skills/orch/references/families/debug_fix.yaml",
            "skills/orch/references/families/design_build.yaml",
            "skills/orch/references/families/research_compare.yaml",
            "skills/orch/references/families/web_qa.yaml",
            "skills/orch/references/families/parallel_investigation.yaml",
            "skills/orch/references/golden-traces/review-full-pipeline.json",
            "skills/orch/references/golden-traces/web-qa-parallel.json",
            "skills/orch/references/golden-traces/single-pr-review.json",
            "skills/orch/references/golden-traces/cross-family-mix.json",
            "skills/orch/references/golden-traces/low-confidence-clarify.json",
            "skills/orch/references/handoff-orch-schema.json",
        ]
        for rel in required:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_intent_schema_confidence_bands(self):
        data = json.loads(
            (ROOT / "skills/orch/references/intent-schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["confidence_bands"]["auto_execute_min"], 0.85)
        self.assertEqual(data["confidence_bands"]["confirm_min"], 0.70)
        self.assertIn("review", data["scenario_family"])
        self.assertIn("web_qa", data["scenario_family"])
        self.assertIn("parallel_investigation", data["scenario_family"])

    def test_skill_md_drops_type_language(self):
        text = (ROOT / "skills/orch/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("/orch 1", text)
        self.assertNotIn("type 1-6", text)
        self.assertIn("自然语言优先", text)
        self.assertIn("family-first", text)
        self.assertIn("rule-first", text)

    def test_hook_context_mentions_natural_language_first_orch(self):
        text = (ROOT / "hooks/_lib.sh").read_text(encoding="utf-8")
        self.assertIn("natural-language-first", text)
        self.assertIn("family-first", text)
        self.assertNotIn("user must explicitly type /orch", text)
        self.assertIn("load_orch_runtime_bundle", text)

    def test_session_start_uses_runtime_bundle(self):
        text = (ROOT / "hooks/session-start").read_text(encoding="utf-8")
        self.assertIn("load_orch_runtime_bundle", text)

    def test_user_docs_stop_teaching_type_numbers(self):
        for rel in ["README.md", "skills/using-loopengine/SKILL.md"]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("/orch 1", text, rel)
            self.assertNotIn("/orch 2", text, rel)
            self.assertIn("自然语言优先", text, rel)

    def test_review_golden_trace_matches_family_rule(self):
        trace = json.loads(
            (
                ROOT
                / "skills/orch/references/golden-traces/review-full-pipeline.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(trace["scenario_family"], "review")
        self.assertEqual(
            trace["expected_dag"][:3],
            ["system-review", "code-reviewer", "clean-code"],
        )

    def test_executor_contracts_have_required_fields(self):
        contract_dir = ROOT / "skills/orch/references/executor-contracts"
        direct_skill = json.loads(
            (contract_dir / "direct-skill.json").read_text(encoding="utf-8")
        )
        loop = json.loads((contract_dir / "loop.json").read_text(encoding="utf-8"))
        go = json.loads((contract_dir / "go.json").read_text(encoding="utf-8"))

        self.assertIn("skill", direct_skill["required_fields"])
        self.assertIn("task_summary", loop["required_fields"])
        self.assertIn("plan_path", go["required_fields"])
        self.assertEqual(direct_skill["executor"], "direct_skill")
        self.assertEqual(loop["executor"], "loop")
        self.assertEqual(go["executor"], "go")

    def test_build_prompt_includes_orch_runtime_context(self):
        zcode_runner = load_zcode_runner_module()
        task = {
            "id": "T1",
            "name": "实现 orch v2 运行时接线",
            "prompt": "消费 orch v2 references 真源，不要只改文档",
            "files": ["skills/orch/SKILL.md", "hooks/_lib.sh"],
        }
        prompt = zcode_runner.build_prompt(task, str(ROOT), [])
        normalized_prompt = prompt.replace("\\", "/")
        self.assertIn("## orch v2 运行时真源", prompt)
        self.assertIn("skills/orch/references/intent-schema.json", normalized_prompt)
        self.assertIn("executor-contracts/go.json", normalized_prompt)

    def test_split_prompt_includes_orch_planning_context(self):
        orchestrator = load_orchestrator_module()
        prompt = orchestrator._build_split_prompt(
            "实现 orch v2 运行时接线路径",
            str(ROOT),
            "L3",
        )
        normalized_prompt = prompt.replace("\\", "/")
        self.assertIn("运行时真源会约束拆分方式", prompt)
        self.assertIn("skills/orch/references/intent-schema.json", normalized_prompt)
        self.assertIn("skills/orch/references/dag-rules.yaml", normalized_prompt)


if __name__ == "__main__":
    unittest.main()

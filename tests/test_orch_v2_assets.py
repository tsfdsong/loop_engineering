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
            "skills/go/references/intent-schema.json",
            "skills/go/references/capability-registry.yaml",
            "skills/go/references/dag-rules.yaml",
            "skills/go/references/executor-contracts/direct-skill.json",
            "skills/go/references/executor-contracts/loop.json",
            "skills/go/references/executor-contracts/go.json",
            "skills/go/references/families/review.yaml",
            "skills/go/references/families/debug_fix.yaml",
            "skills/go/references/families/design_build.yaml",
            "skills/go/references/families/research_compare.yaml",
            "skills/go/references/families/web_qa.yaml",
            "skills/go/references/families/parallel_investigation.yaml",
            "skills/go/references/golden-traces/review-full-pipeline.json",
            "skills/go/references/golden-traces/web-qa-parallel.json",
            "skills/go/references/golden-traces/single-pr-review.json",
            "skills/go/references/golden-traces/cross-family-mix.json",
            "skills/go/references/golden-traces/low-confidence-clarify.json",
            "skills/go/references/handoff-orch-schema.json",
        ]
        for rel in required:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_intent_schema_confidence_bands(self):
        data = json.loads(
            (ROOT / "skills/go/references/intent-schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["confidence_bands"]["auto_execute_min"], 0.85)
        self.assertEqual(data["confidence_bands"]["confirm_min"], 0.70)
        self.assertIn("review", data["scenario_family"])
        self.assertIn("web_qa", data["scenario_family"])
        self.assertIn("parallel_investigation", data["scenario_family"])

    def test_skill_md_drops_type_language(self):
        text = (ROOT / "skills/go/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("/orch 1", text)
        self.assertNotIn("type 1-6", text)
        self.assertIn("family-first", text)
        self.assertIn("rule-first", text)

    def test_hook_context_mentions_family_first_go(self):
        text = (ROOT / "hooks/_lib.sh").read_text(encoding="utf-8")
        self.assertIn("family-first", text)
        self.assertNotIn("user must explicitly type /orch", text)
        self.assertIn("load_go_runtime_bundle", text)

    def test_session_start_uses_runtime_bundle(self):
        text = (ROOT / "hooks/session-start").read_text(encoding="utf-8")
        self.assertIn("load_go_runtime_bundle", text)

    def test_session_start_codex_uses_runtime_bundle(self):
        """Regression for system-review finding C1: Codex must not use the
        degraded load_orch_content path; it must share the runtime bundle."""
        text = (ROOT / "hooks/session-start-codex").read_text(encoding="utf-8")
        self.assertIn("load_go_runtime_bundle", text)
        self.assertNotIn("load_orch_content", text)

    def test_runtime_bundle_includes_families_and_golden_traces(self):
        """Regression for system-review finding C2: bootstrap must inject
        family rules + golden-traces + handoff schema, not just the core 7."""
        text = (ROOT / "hooks/_lib.sh").read_text(encoding="utf-8")
        self.assertIn("families", text)
        self.assertIn("golden-traces", text)
        self.assertIn("handoff-orch-schema.json", text)

    def test_skill_md_lists_handoff_schema_in_refs(self):
        """Regression for system-review finding H3: SKILL.md must reference
        the new handoff-orch-schema.json in its 参考真源 section."""
        text = (ROOT / "skills/go/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("handoff-orch-schema.json", text)

    def test_web_qa_family_includes_plan_execution(self):
        """Regression for system-review finding H1: web_qa family actions
        must include plan_execution to align with dag-rules append.plan."""
        import yaml as _yaml
        data = _yaml.safe_load(
            (ROOT / "skills/go/references/families/web_qa.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("plan_execution", data["actions"])

    def test_handoff_schema_phase_enum_excludes_executor_types(self):
        """Regression for system-review finding H2: phase enum identifies
        a skill phase, not an executor type."""
        data = json.loads(
            (
                ROOT / "skills/go/references/handoff-orch-schema.json"
            ).read_text(encoding="utf-8")
        )
        phase_enum = set(data["properties"]["phase"]["enum"])
        leaked = phase_enum & {"go", "loop", "loop-fix"}
        self.assertFalse(leaked, f"executor types leaked into phase enum: {leaked}")

    def test_user_docs_stop_teaching_type_numbers(self):
        for rel in ["README.md", "skills/using-loopengine/SKILL.md"]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("/orch 1", text, rel)
            self.assertNotIn("/orch 2", text, rel)
            self.assertIn("family", text.lower(), rel)

    def test_review_golden_trace_matches_family_rule(self):
        trace = json.loads(
            (
                ROOT
                / "skills/go/references/golden-traces/review-full-pipeline.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(trace["scenario_family"], "review")
        self.assertEqual(
            trace["expected_dag"][:3],
            ["system-review", "code-reviewer", "clean-code"],
        )

    def test_executor_contracts_have_required_fields(self):
        contract_dir = ROOT / "skills/go/references/executor-contracts"
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

    def test_build_prompt_includes_go_runtime_context(self):
        zcode_runner = load_zcode_runner_module()
        task = {
            "id": "T1",
            "name": "实现 go family 路由运行时接线",
            "prompt": "消费 go references 真源，不要只改文档",
            "files": ["skills/go/SKILL.md", "hooks/_lib.sh"],
        }
        prompt = zcode_runner.build_prompt(task, str(ROOT), [])
        normalized_prompt = prompt.replace("\\", "/")
        self.assertIn("## go 编排运行时真源", prompt)
        self.assertIn("skills/go/references/intent-schema.json", normalized_prompt)
        self.assertIn("executor-contracts/go.json", normalized_prompt)

    def test_split_prompt_includes_go_planning_context(self):
        orchestrator = load_orchestrator_module()
        prompt = orchestrator._build_split_prompt(
            "实现 go family 路由接线路径",
            str(ROOT),
            "L3",
        )
        normalized_prompt = prompt.replace("\\", "/")
        self.assertIn("运行时真源会约束拆分方式", prompt)
        self.assertIn("skills/go/references/intent-schema.json", normalized_prompt)
        self.assertIn("skills/go/references/dag-rules.yaml", normalized_prompt)


if __name__ == "__main__":
    unittest.main()

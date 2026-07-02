#!/usr/bin/env python3
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestOrchV2Assets(unittest.TestCase):
    def test_reference_asset_paths_exist(self):
        required = [
            "skills/orch/references/intent-schema.json",
            "skills/orch/references/capability-registry.yaml",
            "skills/orch/references/dag-rules.yaml",
            "skills/orch/references/families/review.yaml",
            "skills/orch/references/families/debug_fix.yaml",
            "skills/orch/references/families/design_build.yaml",
            "skills/orch/references/families/research_compare.yaml",
            "skills/orch/references/families/web_qa.yaml",
            "skills/orch/references/golden-traces/review-full-plan.json",
            "skills/orch/references/golden-traces/web-qa-report.json",
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
                / "skills/orch/references/golden-traces/review-full-plan.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(trace["scenario_family"], "review")
        self.assertEqual(
            trace["expected_dag"][:3],
            ["system-review", "code-reviewer", "clean-code"],
        )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""go family golden-trace acceptance runner.

Validates golden-traces under skills/go/references/golden-traces/
satisfy the spec's acceptance criteria (docs/superpowers/specs/2026-07-02-
orch-v2-c-lite-design.md §15.1-§15.5; historical filename) and that
handoff-schema.json is a well-formed JSON Schema draft-07 file.

Run: python -m unittest tests.test_go_golden_traces -v
"""
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = ROOT / "skills" / "go" / "references" / "golden-traces"
HANDOFF_SCHEMA = ROOT / "skills" / "go" / "references" / "handoff-schema.json"

# Spec resolution (v1.3.2 · 2026-07-02):
#   1. External repo (~/.loopengine/specs/) — preferred after externalization
#   2. Local cache (docs/superpowers/specs/) — 7-day transition cache (gitignored)
#   3. Skip — neither found (LOOPENGINE_REQUIRE_SPECS=1 fails instead of skipping)
import os as _os
from pathlib import Path as _Path
_SPEC_FILENAME = "2026-07-02-orch-v2-c-lite-design.md"
_EXTERNAL_SPEC = _Path(_os.environ.get("LOOPENGINE_SPECS_DIR", str(_Path.home() / ".loopengine" / "specs"))) / "specs" / _SPEC_FILENAME
_LOCAL_SPEC = ROOT / "docs" / "superpowers" / "specs" / _SPEC_FILENAME
SPEC_FILE = _EXTERNAL_SPEC if _EXTERNAL_SPEC.exists() else _LOCAL_SPEC
_REQUIRE_SPECS = _os.environ.get("LOOPENGINE_REQUIRE_SPECS", "0") == "1"


def _load(name):
    return json.loads((GOLDEN_DIR / name).read_text(encoding="utf-8"))


class TestGoGoldenTraces(unittest.TestCase):
    """Spec §15.1-§15.5 acceptance criteria."""

    # --- §15.1 review family: 5-step DAG, must include code-reviewer + clean-code ---
    def test_ac15_1_review_family_full_pipeline(self):
        trace = _load("review-full-pipeline.json")
        self.assertEqual(trace["scenario_family"], "review")
        dag = trace["expected_dag"]
        self.assertEqual(len(dag), 5, f"review DAG must have 5 steps, got {len(dag)}: {dag}")
        self.assertIn("code-reviewer", dag)
        self.assertIn("clean-code", dag)
        # Order: system-review → code-reviewer → clean-code → ... → spec-driven-development
        self.assertEqual(dag[0], "system-review")
        self.assertEqual(dag[-1], "spec-driven-development")

    # --- §15.2 web_qa: fan-out must be 4 parallel web-* skills ---
    def test_ac15_2_web_qa_four_parallel_web_skills(self):
        trace = _load("web-qa-parallel.json")
        self.assertEqual(trace["scenario_family"], "web_qa")
        nodes = trace["expected_parallel_nodes"]
        self.assertEqual(len(nodes), 4, f"web_qa must fan-out 4 nodes, got {len(nodes)}: {nodes}")
        required = {"web-regression-e2e", "web-visual-diff", "web-audit-a11y", "web-perf-budget"}
        self.assertEqual(set(nodes), required, f"missing/extra nodes: {set(nodes) ^ required}")
        # browser_accessibility_audit must also be present in actions
        self.assertIn("browser_accessibility_audit", trace["actions"])

    # --- §15.3 single_skill task: go must NOT intervene ---
    def test_ac15_3_single_pr_review_is_single_skill(self):
        trace = _load("single-pr-review.json")
        self.assertEqual(trace["task_shape"], "single_skill")
        self.assertEqual(trace["scenario_family"], None)
        self.assertEqual(trace["expected_behavior"], "go_exit_native_match")
        self.assertEqual(trace["go_role"], "passthrough")
        # Per spec §1.4 G1: single_skill → go 退出
        self.assertEqual(trace["actions"], ["code_review"])

    # --- §15.4 cross-family mix: MUST clarify, NOT auto-merge ---
    def test_ac15_4_cross_family_mix_clarifies(self):
        trace = _load("cross-family-mix.json")
        self.assertEqual(trace["task_shape"], "multi_skill")
        self.assertEqual(trace["scenario_family"], None)
        self.assertEqual(trace["expected_behavior"], "clarify_no_merge")
        self.assertEqual(trace["go_role"], "ask_user_question")
        # Must detect at least 2 primary families
        self.assertGreaterEqual(len(trace["detected_families"]), 2)
        # AskUserQuestion template must be present and have 2 options
        tmpl = trace["ask_user_question_template"]
        self.assertEqual(tmpl["options_min"], 2)
        self.assertGreaterEqual(len(tmpl["options"]), 2)

    # --- §15.5 low confidence (<0.70): MUST clarify via AskUserQuestion ---
    def test_ac15_5_low_confidence_clarifies(self):
        trace = _load("low-confidence-clarify.json")
        self.assertLess(trace["confidence"], 0.70)
        self.assertEqual(trace["expected_behavior"], "clarify_low_confidence")
        self.assertEqual(trace["go_role"], "ask_user_question")
        tmpl = trace["ask_user_question_template"]
        self.assertIn("family_explanation", tmpl["must_include"])
        self.assertGreaterEqual(tmpl["options_max"], 2)


class TestGoHandoffSchema(unittest.TestCase):
    """Validate handoff-schema.json (spec §10.1 + §11)."""

    def test_handoff_schema_file_exists(self):
        self.assertTrue(HANDOFF_SCHEMA.exists(), f"missing: {HANDOFF_SCHEMA}")

    def test_handoff_schema_is_valid_json(self):
        data = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)

    def test_handoff_schema_declares_draft_07(self):
        data = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
        self.assertIn("$schema", data)
        self.assertIn("draft-07", data["$schema"])

    def test_handoff_schema_has_required_fields(self):
        """Spec §10.1 schema: phase, scope_applied, hotspot_modules,
        findings_summary, top_issues, next_phase_hint, artifacts."""
        data = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
        props = set(data["properties"].keys())
        required_spec_fields = {
            "phase",
            "scope_applied",
            "hotspot_modules",
            "findings_summary",
            "top_issues",
            "next_phase_hint",
            "artifacts",
        }
        missing = required_spec_fields - props
        self.assertFalse(missing, f"missing spec §10.1 fields: {missing}")

    def test_handoff_schema_required_keys_align_with_spec(self):
        data = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
        required = set(data["required"])
        # Spec §10.1 implicitly requires phase + findings_summary + next_phase_hint
        self.assertIn("phase", required)
        self.assertIn("findings_summary", required)
        self.assertIn("next_phase_hint", required)

    def test_handoff_findings_summary_severity_buckets(self):
        data = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
        buckets = set(data["properties"]["findings_summary"]["properties"].keys())
        self.assertEqual(buckets, {"critical", "important", "minor"})


class TestGoGoldenTraceCoverage(unittest.TestCase):
    """Meta-check: golden-traces cover all 5 explicit acceptance criteria in §15."""

    def test_all_acceptance_criteria_have_traces(self):
        acceptance_refs = {
            "review-full-pipeline.json": "spec §15.1",
            "web-qa-parallel.json": "spec §15.2",
            "single-pr-review.json": "spec §15.3",
            "cross-family-mix.json": "spec §15.4",
            "low-confidence-clarify.json": "spec §15.5",
        }
        for name, ref in acceptance_refs.items():
            self.assertTrue((GOLDEN_DIR / name).exists(), f"{name} ({ref}) is missing")
            data = _load(name)
            self.assertIn("acceptance_criteria_ref", data, f"{name} must declare acceptance_criteria_ref")

    def test_spec_decision_8_acknowledges_parallel_investigation_exception(self):
        """User decision B (2026-07-02): parallel_investigation is allowed fan-out
        alongside web_qa as a documented exception in spec §3 decision 8."""
        if not SPEC_FILE.exists():
            if _REQUIRE_SPECS:
                self.fail(f"spec required but not found: {_EXTERNAL_SPEC} or {_LOCAL_SPEC}")
            self.skipTest(
                f"spec not available at external ({_EXTERNAL_SPEC}) or local ({_LOCAL_SPEC}) cache; "
                "set LOOPENGINE_REQUIRE_SPECS=1 to fail instead of skip"
            )
        text = SPEC_FILE.read_text(encoding="utf-8")
        # Decision 8 table row should mention parallel_investigation now
        self.assertIn("parallel_investigation", text)
        # The row mentions an exception phrase
        decision_row_marker = "| 8 | 并行策略"
        self.assertIn(decision_row_marker, text)
        # Locate the row and verify it mentions parallel_investigation
        for line in text.splitlines():
            if line.startswith("| 8 | 并行策略"):
                self.assertIn("parallel_investigation", line, f"decision 8 row must mention parallel_investigation: {line!r}")
                break
        else:
            self.fail("could not locate spec §3 decision 8 row")


if __name__ == "__main__":
    unittest.main(verbosity=2)
---
execution_path: go
---

# orch v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current type-based `orch` model with a natural-language-first, family-first, rule-first multi-skill orchestrator that delegates execution to existing `loop` and `go` layers.

**Architecture:** The implementation is prompt-and-reference driven rather than service-runtime driven. `skills/orch/SKILL.md` and the session-start hooks become the behavioral contract, while new registry/rule assets under `skills/orch/references/` provide a canonical source of truth for scenario families, intent schema, capability mapping, DAG rules, and golden traces. Existing `loop` and `go` Python scripts remain the execution backplane; the implementation updates docs/prompts/hooks and adds validation tests instead of inventing a new executor.

**Tech Stack:** Markdown skill files, Bash/CMD hook bootstrap, JSON/YAML reference assets, Python `unittest` validation tests, existing `loop`/`go` Python orchestration scripts.

---

## File Structure

**Create**
- `skills/orch/references/intent-schema.json`
- `skills/orch/references/capability-registry.yaml`
- `skills/orch/references/dag-rules.yaml`
- `skills/orch/references/families/review.yaml`
- `skills/orch/references/families/debug_fix.yaml`
- `skills/orch/references/families/design_build.yaml`
- `skills/orch/references/families/research_compare.yaml`
- `skills/orch/references/families/web_qa.yaml`
- `skills/orch/references/golden-traces/review-full-plan.json`
- `skills/orch/references/golden-traces/web-qa-report.json`
- `tests/test_orch_v2_assets.py`
- `.workflow/orch-v2-c-lite/10-implementation-plan.md`

**Modify**
- `skills/orch/SKILL.md`
- `hooks/_lib.sh`
- `hooks/session-start`
- `skills/orch/hooks/orch-bootstrap.sh`
- `skills/orch/hooks/orch-bootstrap.cmd`
- `README.md`
- `skills/using-loopengine/SKILL.md`

**Why these files**
- `skills/orch/SKILL.md` is the actual orchestration behavior spec injected into sessions.
- `hooks/*` and `skills/orch/hooks/*` control how `orch` is surfaced to Cursor/Claude/Copilot/CMD environments at session start.
- `skills/orch/references/*` becomes the stable, machine-readable source of truth for family/action/rule definitions.
- `README.md` and `skills/using-loopengine/SKILL.md` must stop teaching `/orch 1..6`.
- `tests/test_orch_v2_assets.py` guards against drift between the spec and the new reference assets.

### Task 1: Add canonical orch v2 reference assets

**Files:**
- Create: `skills/orch/references/intent-schema.json`
- Create: `skills/orch/references/capability-registry.yaml`
- Create: `skills/orch/references/dag-rules.yaml`
- Create: `skills/orch/references/families/review.yaml`
- Create: `skills/orch/references/families/debug_fix.yaml`
- Create: `skills/orch/references/families/design_build.yaml`
- Create: `skills/orch/references/families/research_compare.yaml`
- Create: `skills/orch/references/families/web_qa.yaml`
- Create: `skills/orch/references/golden-traces/review-full-plan.json`
- Create: `skills/orch/references/golden-traces/web-qa-report.json`

- [ ] **Step 1: Write the failing asset-validation test**

```python
def test_reference_asset_paths_exist():
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_reference_asset_paths_exist -v`  
Expected: `FAIL` because the new `skills/orch/references/*` files do not exist yet.

- [ ] **Step 3: Create the minimal reference assets**

```json
{
  "$schema": "orch-v2-intent-schema",
  "task_shape": ["single_skill", "multi_skill"],
  "scenario_family": [
    "review",
    "debug_fix",
    "design_build",
    "research_compare",
    "web_qa",
    "parallel_investigation"
  ],
  "goal": ["report", "plan", "fix", "execute"],
  "confidence_bands": {
    "auto_execute_min": 0.85,
    "confirm_min": 0.70
  }
}
```

```yaml
system_review:
  capability: system_consistency_review
  executor_kind: direct_skill
  skill: system-review
  side_effects: none
  compatible_families: [review]

fix_issue:
  capability: targeted_fix
  executor_kind: loop
  skill: null
  side_effects: write
  compatible_families: [debug_fix, design_build]

execute_plan:
  capability: plan_execution
  executor_kind: go
  skill: null
  side_effects: write
  compatible_families: [design_build]
```

```yaml
global:
  multi_family: clarify
  single_skill: exit_orch
  executor_policy: side_effect_first
review:
  order: [system_review, code_review, code_quality_simplify]
  append:
    report: [synthesize_findings]
    plan: [synthesize_findings, plan_execution]
web_qa:
  bootstrap: [browser_explore]
  parallel: [
    browser_regression_test,
    browser_visual_diff,
    browser_accessibility_audit,
    browser_perf_audit
  ]
  append:
    report: [synthesize_findings]
```

```json
{
  "input": "帮我全面审查这个项目，看看架构、代码问题和可精简点，然后出计划",
  "scenario_family": "review",
  "actions": [
    "system_review",
    "code_review",
    "code_quality_simplify",
    "synthesize_findings",
    "plan_execution"
  ],
  "expected_dag": [
    "system-review",
    "code-reviewer",
    "clean-code",
    "brainstorming",
    "writing-plans"
  ]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_reference_asset_paths_exist -v`  
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/orch/references tests/test_orch_v2_assets.py
git commit -m "feat(orch): add v2 intent schema and rule assets"
```

### Task 2: Rewrite `skills/orch/SKILL.md` to natural-language-first orchestration

**Files:**
- Modify: `skills/orch/SKILL.md`
- Test: `tests/test_orch_v2_assets.py`

- [ ] **Step 1: Write the failing behavior test**

```python
def test_skill_md_drops_type_language():
    text = (ROOT / "skills/orch/SKILL.md").read_text(encoding="utf-8")
    self.assertNotIn("/orch 1", text)
    self.assertNotIn("type 1-6", text)
    self.assertIn("自然语言优先", text)
    self.assertIn("family-first", text)
    self.assertIn("rule-first", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_skill_md_drops_type_language -v`  
Expected: `FAIL` because the current skill still documents `/orch <type>`.

- [ ] **Step 3: Rewrite the skill to match the approved spec**

```md
## 职责（v2.0）

当用户目标需要 **2 个或以上技能** 才能完成时，orch 负责：

- 判断是否需要多技能编排
- 识别主 `scenario family`
- 在该 family 内抽取 `actions[]`
- 按 `rule-first` 规则组装串行/并行 DAG
- 按 `side-effect-first` 把节点委托给 `direct_skill` / `loop` / `go`

## 入口

- **自然语言优先**：用户直接说目标，系统自动判断是否进入 orch
- **`/orch` 仍保留**：仅作为“强制走编排判断”的显式入口
- **不再使用**：`/orch 1..6`、`type 1-6`

## 第一版边界

- `family-first`
- 单一主 family
- 默认串行
- 仅 `web_qa` 允许 fan-out 并行
- `confidence >= 0.85` 自动执行
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_skill_md_drops_type_language -v`  
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/orch/SKILL.md tests/test_orch_v2_assets.py
git commit -m "refactor(orch): switch skill docs to v2 intent-driven model"
```

### Task 3: Align session-start hooks with orch v2 behavior

**Files:**
- Modify: `hooks/_lib.sh`
- Modify: `hooks/session-start`
- Modify: `skills/orch/hooks/orch-bootstrap.sh`
- Modify: `skills/orch/hooks/orch-bootstrap.cmd`
- Test: `tests/test_orch_v2_assets.py`

- [ ] **Step 1: Write the failing hook-copy test**

```python
def test_hook_context_mentions_natural_language_first_orch():
    text = (ROOT / "hooks/_lib.sh").read_text(encoding="utf-8")
    self.assertIn("natural-language-first", text)
    self.assertIn("family-first", text)
    self.assertNotIn("user must explicitly type /orch", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_hook_context_mentions_natural_language_first_orch -v`  
Expected: `FAIL` because the current hook still says multi-skill tasks require explicit `/orch`.

- [ ] **Step 3: Update the shared hook messaging and platform bootstraps**

```bash
build_session_context() {
    local orch_content="$1"
    local orch_escaped
    orch_escaped=$(escape_for_json "$orch_content")
    printf '<EXTREMELY_IMPORTANT>\nYou have LoopEngine installed.\n\norch v2 is a natural-language-first, family-first, rule-first multi-skill orchestrator.\nUse it when the user goal requires multiple skills; keep single-skill tasks on native description matching.\n\n%s\n</EXTREMELY_IMPORTANT>' "$orch_escaped"
}
```

```cmd
echo {"additionalContext": "orch v2 installed. Natural-language-first multi-skill orchestration is available. Use native description matching for single-skill tasks; use orch when the goal clearly spans multiple complementary skills."}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_hook_context_mentions_natural_language_first_orch -v`  
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add hooks/_lib.sh hooks/session-start skills/orch/hooks/orch-bootstrap.sh skills/orch/hooks/orch-bootstrap.cmd tests/test_orch_v2_assets.py
git commit -m "refactor(hooks): inject orch v2 natural-language-first context"
```

### Task 4: Update user-facing docs to remove `/orch type` teaching

**Files:**
- Modify: `README.md`
- Modify: `skills/using-loopengine/SKILL.md`
- Test: `tests/test_orch_v2_assets.py`

- [ ] **Step 1: Write the failing docs test**

```python
def test_user_docs_stop_teaching_type_numbers():
    for rel in ["README.md", "skills/using-loopengine/SKILL.md"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        self.assertNotIn("/orch 1", text, rel)
        self.assertNotIn("/orch 2", text, rel)
        self.assertIn("自然语言优先", text, rel)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_user_docs_stop_teaching_type_numbers -v`  
Expected: `FAIL` because both files still teach `/orch 1..5`.

- [ ] **Step 3: Rewrite the docs examples**

```md
### `orch` — 多技能编排器

- **自然语言优先**：用户直接说目标，系统自动判断是否需要多技能编排
- **显式入口仍保留**：`/orch` 仅用于强制要求系统走编排判断

| 你说 | 系统行为 |
|------|---------|
| "帮我全面审查这个项目并给计划" | 自动识别为 `review` family，多技能串行编排 |
| "帮我自动化测试这个网站" | 自动识别为 `web_qa` family，fan-out 测试矩阵 |
| "帮我排查并修复这个错误" | 自动识别为 `debug_fix` family，委托 `loop` 修复 |
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_orch_v2_assets.TestOrchV2Assets.test_user_docs_stop_teaching_type_numbers -v`  
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add README.md skills/using-loopengine/SKILL.md tests/test_orch_v2_assets.py
git commit -m "docs(orch): replace type-based examples with natural language flows"
```

### Task 5: Add end-to-end asset validation tests and save the tracked plan copy

**Files:**
- Create: `tests/test_orch_v2_assets.py`
- Create: `.workflow/orch-v2-c-lite/10-implementation-plan.md`
- Test: `tests/test_orch_v2_assets.py`

- [ ] **Step 1: Write the full validation suite**

```python
class TestOrchV2Assets(unittest.TestCase):
    def test_reference_asset_paths_exist(self): ...
    def test_skill_md_drops_type_language(self): ...
    def test_hook_context_mentions_natural_language_first_orch(self): ...
    def test_user_docs_stop_teaching_type_numbers(self): ...

    def test_review_golden_trace_matches_family_rule(self):
        trace = json.loads((ROOT / "skills/orch/references/golden-traces/review-full-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(trace["scenario_family"], "review")
        self.assertEqual(trace["expected_dag"][:3], ["system-review", "code-reviewer", "clean-code"])
```

- [ ] **Step 2: Run the full suite and verify the final state**

Run: `python -m unittest tests.test_orch_v2_assets -v`  
Expected: all tests `OK`

- [ ] **Step 3: Save the tracked copy of this plan**

```bash
mkdir -p .workflow/orch-v2-c-lite
cp docs/superpowers/plans/2026-07-02-orch-v2-implementation.md .workflow/orch-v2-c-lite/10-implementation-plan.md
```

- [ ] **Step 4: Verify the tracked plan exists**

Run: `python - <<'PY'
from pathlib import Path
assert Path('.workflow/orch-v2-c-lite/10-implementation-plan.md').exists()
print('OK')
PY`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add tests/test_orch_v2_assets.py .workflow/orch-v2-c-lite/10-implementation-plan.md
git commit -m "test(orch): add v2 asset validation coverage"
```

## Self-Review

- **Spec coverage:** The tasks cover all approved design decisions: no user-facing type, family-first recognition, single-family v1, rule-first DAGs, side-effect-first executor delegation, confidence bands, family-default append, and `web_qa` fan-out.
- **Placeholder scan:** No task uses TBD/TODO or hand-wavy “add tests” language; each task includes concrete file paths, commands, and code snippets.
- **Type consistency:** The same family/action names are used across assets, docs, and tests: `review`, `debug_fix`, `design_build`, `research_compare`, `web_qa`; `system_review`, `code_review`, `code_quality_simplify`, `plan_execution`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-02-orch-v2-implementation.md`. Three execution options:

**1. Subagent-Driven (recommended for simple plans)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**2. Inline Execution (for single-session work)** - Execute tasks in this session using executing-plans, batch execution with checkpoints
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
- Batch execution with checkpoints for review

**3. /go Engineering Mode (recommended for engineering-level plans, v4.0+)** - 工程化执行：worktree 隔离 + 自动拆分 + 降级兜底 + G10 系统审查
- **适用场景**：跨模块 / 多文件 / 需要并发 / 复杂任务
- **执行命令**：`/go 按照 .workflow/orch-v2-c-lite/10-implementation-plan.md 实现 orch v2`
- **不适用**：单文件修改 / 简单重构 / 教学示例
- **与本 plan 的关系**：本计划明确了文件边界、测试和提交粒度；`/go` 应按本计划拆任务，而不是重新发散设计

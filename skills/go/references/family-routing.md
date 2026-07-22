# Family Routing（v2.0 · family-first · D4.1）

> go Step 0 的 family 识别能力真源。
> 运行时真源：`skills/go/references/dag-rules.yaml` + `intent-schema.json` + `families/*.yaml`

## 8 场景家族

| family | 典型目标 | 默认执行形态 |
|---|---|---|
| `review` | 审查、评估、给改进建议 | 串行审查链 |
| `debug_fix` | 排查、修复、验证 | 串行修复链 |
| `design_build` | 设计并实现 | 串行设计 + 计划 + 执行 |
| `research_compare` | 调研、对比、选型 | 串行研究链 |
| `web_qa` | 浏览器自动化测试、视觉回归、性能审计 | `browser_explore` 后 fan-out 并行 |
| `parallel_investigation` | 同时调研多个对象 | 受控并行探查 |
| `refactor` 🆕 | 重构、保持行为不变、消除技术债 | 串行重构链（loop 执行） |
| `test` 🆕 | 补测试、提升覆盖、回归保障 | 串行测试链（loop 执行） |

## 各 family 的默认 actions[]（来自原 dag-rules.yaml）

| family | 默认 actions[] 序列 |
|---|---|
| `review` | `system_review` → `code_review` → `code_quality_simplify` （append: `synthesize_findings` / + `plan_execution`） |
| `debug_fix` | `debug_root_cause` → `fix_issue` → `verify_result` |
| `design_build` | `design_solution` → `plan_execution` → `execute_plan` |
| `research_compare` | `research_evidence` → `compare_options`（append: `synthesize_findings` / + `plan_execution`） |
| `web_qa` | bootstrap: `browser_explore`；parallel: `browser_regression_test`, `browser_visual_diff`, `browser_accessibility_audit`, `browser_perf_audit` |
| `parallel_investigation` | bootstrap: `parallel_probe`（append: `synthesize_findings`） |
| `refactor` | `assess_refactor_scope` → `refactor_apply` → `verify_behavior_preserved` |
| `test` | `assess_test_gaps` → `write_tests` → `run_and_verify` |

## family-first 识别流程

1. 用户目标进入 → 识别是否需要多技能
2. 识别主 family（8 类之一）
3. 多 family → AskUserQuestion 澄清（不混编，除非落在白名单组合）
4. 单 family → 抽取 `actions[]` + `scope` + `goal`
5. 委托路由（见下"执行器边界"）

## 组合白名单（v2.1 · 允许的高频组合）

来自原 `dag-rules.yaml > global.allowed_combinations`：

| 组合 | 串接语义 | handoff 桥接字段 |
|---|---|---|
| `refactor` ⊕ `test` | 重构后补测试 | `handoff.refactored_modules` |
| `review` ⊕ `refactor` | 审查后重构 | `handoff.review_findings` |
| `debug_fix` ⊕ `test` | 修复后加回归测试 | `handoff.fixed_modules` |
| `design_build` ⊕ `test` | 新功能带测试 | `handoff.built_modules` |
| `web_qa` ⊕ `debug_fix` | web 审计发现 bug → 修复 | `handoff.web_qa_findings` |
| `web_qa` ⊕ `refactor` | web 审计后重构改进 | `handoff.review_findings` |

未列入的组合仍触发澄清（不自由混编）。

## 执行器边界（side-effect-first）

| 节点特征 | 执行器 |
|---|---|
| 只读分析 / 审查 / 调研 | `direct_skill` |
| 单任务写代码 / 修复 | `loop` |
| 跨模块 / 多子任务实施 | `go` + supervisor |

go Step 0 只负责 **"意图 → 执行图"**，不重复：
- loop 的门禁 / 自愈 / G9
- go 的 worktree / 并发 / G10 / 集成回归

## 典型编排（family → actions → 执行图）

### review

```text
system-review → code-reviewer → clean-code → brainstorming → spec-driven-development
```

### debug_fix

```text
systematic-debugging → loop(fix) → verification-before-completion
```

### web_qa

```text
browser_explore
    ├─→ web-regression-e2e
    ├─→ web-visual-diff
    ├─→ web-audit-a11y
    └─→ web-perf-budget
             ↓
        brainstorming(synthesize)
```

## 设计原则（family-first · v2.0）

1. **Family-first**：先识别场景家族，再在家族内抽取动作
2. **Action, not skill**：用户意图先落到稳定 action，而不是直连技能名
3. **Rule-first**：LLM 理解意图，规则表决定拓扑
4. **Side-effect-first**：按副作用委托执行器
5. **Single family（或白名单组合）**：默认 1 个主 family；仅允许白名单内组合，其他触发澄清
6. **Confidence gate**：见 `dag-assembly.md`

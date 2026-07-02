# orch v2 — C-lite 意图驱动多技能编排器 设计规格

> **状态**: 待用户审阅  
> **日期**: 2026-07-02  
> **版本**: orch v2.0.0（设计稿）  
> **取代**: orch v1.1.0 的 type 1-6 模板入口模型  
> **关联技能**: `loop`（单任务闭环执行）、`go`（工程级 DAG/并发执行）

---

## 1. 背景与问题

### 1.1 现状（orch v1.1.0）

- 用户通过 `/orch <type> <query>` 或省略 type 的语义兜底触发编排
- 6 条预设任务链（type 1-6），每条是写死的技能序列
- 省略 type 时，系统倾向于按单技能 description 互斥匹配，只选 1 个技能
- 用户真实意图「系统审查 + 代码审查 + 代码质量精简」被压缩为仅 `system-review`

### 1.2 根因

| 层 | 问题 |
|---|---|
| 入口 | `type` 是内部模板编号，不是用户语言 |
| 识别 | 无多动作并列解析；技能 description 互斥声明伤害互补组合 |
| 编排 | 预设链粒度过粗（type 2 仅 `system-review → brainstorming`） |
| 执行 | 未内建 `loop/go` 为默认执行器 |

### 1.3 目标

将 `orch` 升级为**意图驱动的多技能编排器**：

- 用户只说目标，不学 `type`
- 自动识别是否需要多技能编排
- 支持 review / web_qa / debug_fix / design_build / research_compare 等多场景
- 默认复用 `loop` / `go` 作为执行层
- 高置信度自动执行，低置信度才确认

---

## 2. 设计原则

1. **No user-facing type** — 不再暴露或依赖 `orch type` 编号
2. **Family first** — 先识别场景家族，再在家族内抽取动作
3. **Action, not skill** — 用户意图落到稳定 action 枚举，不直连技能名
4. **Rule-first DAG** — LLM 理解意图，规则表决定拓扑
5. **Side-effect-first execution** — 按副作用选择 `direct_skill` / `loop` / `go`
6. **Single family v1** — 第一版只允许 1 个主 family，跨 family 不混编
7. **Confidence gate** — 高置信直执行，歧义时澄清或确认
8. **Orch plans, loop/go execute** — orch 不重复门禁、worktree、自愈能力

---

## 3. 已确认架构决策

| # | 决策点 | 选择 |
|---|---|---|
| 1 | 入口方式 | 自然语言优先；`/orch` 仅作显式强制编排入口 |
| 2 | 意图识别主轴 | `family_first` |
| 3 | family 边界 | 第一版只允许 1 个主 family；多 family 命中 → 澄清 |
| 4 | DAG 组装 | `rule_first` |
| 5 | 执行器选择 | `side_effect_first` |
| 6 | 置信度闸门 | ≥0.85 自动执行；0.70–0.84 Plan Preview 确认；<0.70 澄清 |
| 7 | 后置步骤 | `family_default_append`（按 family + goal 自动追加） |
| 8 | 并行策略 | 默认串行；仅 `web_qa` family 允许 fan-out 并行 |

---

## 4. 总体架构

```
用户自然语言（或显式 /orch）
        │
        ▼
┌──────────────────────────────┐
│ L1 · Intent Understanding    │  单/多技能 · family · actions · goal
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ L2 · Orchestration Planner   │  capability 映射 · rule-first DAG
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ L3 · Confidence Gate         │  自动执行 / 确认 / 澄清
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ L4 · Execution Bridge        │  direct_skill / loop / go
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ L5 · Handoff + Trace         │  结构化上下文传递 · 执行追溯
└──────────────────────────────┘
```

### 4.1 与现有分层的关系

```
用户 query
    │
    ├─ 单技能 ──────────────────→ 原生 description 匹配（orch 退出）
    │
    └─ 多技能 / 显式 /orch ─────→ orch v2（L1–L5）
                                      │
                         ┌────────────┼────────────┐
                         ▼            ▼            ▼
                    direct_skill    loop          go
                   (只读分析)    (单任务写)   (多子任务写)
```

**边界定义**: orch v2 是**多技能意图编排层**，不是单技能路由器，不是执行器，不是万能 planner。

---

## 5. L1 · Intent Understanding

### 5.1 Scenario Family（场景家族）

| family | 典型用户表达 | 默认 goal 倾向 |
|---|---|---|
| `review` | 审查、评估、看看问题、给建议 | report / plan |
| `debug_fix` | 报错、排查、修复、定位 | fix |
| `design_build` | 设计并实现、规划开发 | execute |
| `research_compare` | 调研、对比、选型 | plan |
| `web_qa` | 测试网站、自动化测试、视觉回归 | report |
| `parallel_investigation` | 同时调研多个对象 | report |

第一版：检测到多个主 family → **不混编**，`AskUserQuestion` 澄清。

### 5.2 Intent Schema

```json
{
  "task_shape": "single_skill | multi_skill",
  "scenario_family": "review",
  "actions": ["system_review", "code_review", "code_quality_simplify"],
  "scope": {
    "level": "full_project | diff_only | module | file | external_url",
    "targets": []
  },
  "goal": "report | plan | fix | execute",
  "execution_preference": "serial | parallel | auto",
  "risk_level": "low | medium | high",
  "confidence": 0.87,
  "reasoning_trace": ["..."]
}
```

- `task_shape = single_skill` → orch 退出，原生匹配
- `actions[]` 为固定枚举（12–20 个），不是技能名

### 5.3 Action 枚举（第一版）

| action | 语义 |
|---|---|
| `system_review` | 系统/架构/一致性审查 |
| `code_review` | 代码层审查 |
| `code_quality_simplify` | 可读性/精简机会 |
| `debug_root_cause` | 根因定位 |
| `fix_issue` | 修复 |
| `verify_result` | 验证 |
| `research_evidence` | 事实收集 |
| `compare_options` | 方案对比 |
| `design_solution` | 需求/方案设计 |
| `plan_execution` | 生成实现计划 |
| `execute_plan` | 执行计划 |
| `browser_explore` | 浏览器探查 |
| `browser_regression_test` | 回归测试 |
| `browser_visual_diff` | 视觉对比 |
| `browser_accessibility_audit` | 无障碍审计 |
| `browser_perf_audit` | 性能审计 |
| `synthesize_findings` | 汇总多路结果 |
| `parallel_probe` | 并行独立探查 |

### 5.4 识别级联

```
L0: 显式 /orch → 强制进入编排路径
L1: 多动作检测（「A + B + C」、并列动词）
L2: family 关键词规则（零 token）
L3: LLM 结构化输出（仅 L1/L2 不完整时）
L4: confidence 闸门
```

---

## 6. L2 · Capability Registry

存放于 `skills/orch/references/capability-registry.yaml`。

### 6.1 结构示例

```yaml
system_review:
  capability: system_consistency_review
  executor_kind: direct_skill
  skill: system-review
  side_effects: none
  provides: [hotspot_modules, architecture_findings]
  compatible_families: [review]

fix_issue:
  capability: targeted_fix
  executor_kind: loop
  skill: null
  side_effects: write
  provides: [code_changes, gate_result]
  compatible_families: [debug_fix, design_build]

execute_plan:
  capability: plan_execution
  executor_kind: go
  skill: null
  side_effects: write
  provides: [subtask_results, integration_report]
  compatible_families: [design_build]
```

### 6.2 Executor Kind

| kind | 含义 | 典型场景 |
|---|---|---|
| `direct_skill` | 直接加载技能 | 只读分析/调研/审查 |
| `loop` | 委托 loop | 单任务写代码 + 门禁 |
| `go` | 委托 go | 跨模块/多子任务实施 |
| `parallel_agent` | 并行 worker | 独立调研（未来） |

---

## 7. L2 · DAG 规则表（rule_first）

### 7.1 全局规则

| 规则 | 内容 |
|---|---|
| G0 | 多主 family → 澄清，不混编 |
| G1 | single_skill → orch 退出 |
| G2 | side_effects=none → direct_skill |
| G3 | write + 单任务 → loop |
| G4 | write + 多子任务/跨模块 → go |
| G5–G7 | confidence 闸门（见 §3） |

### 7.2 review family

| 规则 | 内容 |
|---|---|
| R1 | actions 按粒度排序：system_review → code_review → code_quality_simplify |
| R2 | scope 递进收缩：全项目 → hotspot_modules → style_debt |
| R3 | goal=report → 追加 synthesize_findings |
| R4 | goal=plan → 追加 synthesize_findings → plan_execution |
| R5 | 全部串行，direct_skill |

**典型 DAG（全面审查 + 计划）**:

```
system-review → code-reviewer → clean-code → brainstorming → writing-plans
```

### 7.3 web_qa family

| 规则 | 内容 |
|---|---|
| W1 | browser_explore 先行 |
| W2 | 测试维度 fan-out 并行（唯一允许并行的 family） |
| W3 | fan-in → synthesize_findings |
| W4–W5 | 按 goal 决定是否追加 plan_execution |

**典型 DAG**:

```
browser_explore
    ├─→ web-regression-e2e ─┐
    ├─→ web-visual-diff ────┤
    ├─→ web-audit-a11y ─────┼─→ synthesize → (writing-plans if goal=plan)
    └─→ web-perf-budget ────┘
```

### 7.4 debug_fix family

```
systematic-debugging → loop(fix) → verification-before-completion
```
严格串行。

### 7.5 design_build family

```
brainstorming → writing-plans → go(execute)
```
严格串行。

### 7.6 research_compare family

```
evidence-first → (brainstorming) → writing-plans (if goal=plan)
```
默认串行。

---

## 8. L3 · Confidence Gate

| 置信度 | 行为 |
|---|---|
| ≥ 0.85 | 自动执行 DAG |
| 0.70 – 0.84 | 展示 Plan Preview，用户确认后执行 |
| < 0.70 | `AskUserQuestion` 澄清（Top-2 解释） |

Plan Preview 必须包含：理解到的 family、actions、scope、goal、DAG 拓扑、预计步数、是否只读。

---

## 9. L4 · Execution Bridge

### 9.1 委托规则（side_effect_first）

| 节点特征 | 委托 |
|---|---|
| side_effects=none | direct_skill |
| side_effects=write，单任务边界 | loop（注入 handoff + 验收条件） |
| side_effects=write，跨模块/多子任务 | go（注入 handoff + 功能描述 + 验收条件） |
| web_qa fan-out 节点 | 各节点 direct_skill，orch 协调 fan-in |

### 9.2 orch 不重复实现

- loop 的门禁矩阵 / 自愈 / G9
- go 的 worktree / 拓扑拆分 / G10 / 全局回归
- AGENTS.md 红线纪律

---

## 10. L5 · Handoff + Trace

### 10.1 Handoff Schema（扩展 go handoff-protocol）

```json
{
  "phase": "system-review",
  "scope_applied": "full_project",
  "hotspot_modules": ["skills/orch/"],
  "findings_summary": { "critical": 2, "important": 5, "minor": 8 },
  "top_issues": ["..."],
  "next_phase_hint": "重点审查 hotspot_modules",
  "artifacts": "human-readable summary"
}
```

### 10.2 Trace

每步记录：intent 解析结果、选用的 family/actions、最终 DAG、confidence、执行器、handoff 摘要、耗时。

---

## 11. 文件结构（实现时）

```
skills/orch/
├── SKILL.md                          # 升级为 v2.0
├── references/
│   ├── intent-schema.json
│   ├── capability-registry.yaml
│   ├── dag-rules.yaml
│   ├── executor-contracts/
│   │   ├── direct-skill.json
│   │   ├── loop.json
│   │   └── go.json
│   ├── families/
│   │   ├── review.yaml
│   │   ├── web_qa.yaml
│   │   ├── debug_fix.yaml
│   │   ├── design_build.yaml
│   │   └── research_compare.yaml
│   ├── handoff-orch-schema.json
│   └── golden-traces/
│       ├── review-full-pipeline.json
│       └── web-qa-parallel.json
```

---

## 12. 能力边界

### 12.1 v2.0 负责

- 判断是否需要多技能编排
- family-first 意图识别 + action 抽取
- rule-first DAG 组装
- confidence 闸门
- 委托 direct_skill / loop / go
- 结构化 handoff 传递

### 12.2 v2.0 不负责

- 单技能路由
- 跨 family 混编（第一版）
- 任意拓扑 DAG（环、条件分支、动态 re-plan）
- 替代 loop/go 执行细节
- 未经确认的自动修复（goal=fix 且 confidence 不足时澄清）
- 跨 session 持久化 checkpoint DB

### 12.3 v2.1 候选扩展

- 主 family + 次 family 受控扩展
- review 类只读节点有限并行
- 条件路由（ERROR → 中断）
- `/orch --yes` 跳过确认（高级用户）

---

## 13. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 意图误判 | family_first + confidence 闸门 + golden trace |
| 高置信误路由成本大 | 0.85 阈值 + Plan Preview 中段 |
| action/family 枚举膨胀 | 稳定业务动作原则，禁止技能别名膨胀 |
| handoff 质量不稳 | schema 校验 + 不合格降级全文摘要 |
| 与 go 职责重叠 | 明确 orch=技能级 DAG，go=工程级 DAG |
| 重蹈 skill-hub alpha mock | rule-first + golden trace 测试，禁止 LLM 自由画 DAG |

---

## 14. 迁移与兼容

- **删除**: 用户面向的 `type 1-6` 入口与文档
- **保留**: `/orch` 作为显式强制编排入口
- **type 1-6 技能链**: 降级为 `families/*.yaml` 内的规则配置，不对用户暴露编号
- **未使用 /orch 的单技能场景**: 行为不变
- **install.sh**: 同步 `skills/orch/` 到用户技能目录

---

## 15. 验收标准（设计完成后的实现验收）

1. 输入「全面审查项目并给计划」→ family=review，DAG 含 5 步，不遗漏 code-reviewer/clean-code
2. 输入「自动化测试这个网站」→ family=web_qa，fan-out 并行 4 个 web-* 技能
3. 输入「帮我审查这个 PR」→ task_shape=single_skill，orch 不介入
4. 输入跨 family 混合请求 → 触发澄清，不自动混编
5. confidence < 0.70 → AskUserQuestion，不静默执行
6. fix 类节点 → 委托 loop；跨模块 execute → 委托 go
7. golden-traces 全部通过

---

## 16. 下一步

用户审阅本 spec 通过后 → 调用 `writing-plans` 技能生成实现计划。

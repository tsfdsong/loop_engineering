---
name: orch
description: Use when a user goal requires 2+ complementary skills. orch v2 is a natural-language-first, family-first, rule-first multi-skill orchestrator. Keep single-skill tasks on native description matching.
metadata:
  version: "2.0.0"
  purpose: intent-driven multi-skill orchestration only
  replaces: [orch-v1, skill-hub]
  related_executors: [go, loop, subagent-driven-development, dispatching-parallel-agents]
---

# orch — 意图驱动多技能编排器

## 职责（v2.0）

当用户目标需要 **2 个或以上技能** 才能完成时，orch 负责：

- 判断是否需要多技能编排
- 识别主 `scenario family`
- 在该 family 内抽取 `actions[]`
- 按 `rule-first` 规则组装串行 / 并行 DAG
- 按 `side-effect-first` 把节点委托给 `direct_skill` / `loop` / `go`

orch **不** 接管单技能路由，**不** 重复 `go` / `loop` 的执行能力，**不** 自由发明 DAG。

## 入口

- **自然语言优先**：用户直接说目标，系统自动判断是否进入 orch
- **`/orch` 仍保留**：仅作为“强制走编排判断”的显式入口
- **单技能任务**：仍走原生 description 匹配，不需要 orch

## 设计原则

1. **Family-first**：先识别场景家族，再在家族内抽取动作
2. **Action, not skill**：用户意图先落到稳定 action，而不是直连技能名
3. **Rule-first**：LLM 理解意图，规则表决定拓扑
4. **Side-effect-first**：按副作用委托执行器
5. **Single family v1**：第一版只允许 1 个主 family
6. **Confidence gate**：高置信自动执行，低置信确认或澄清

## 第一版场景家族

| family | 典型目标 | 默认执行形态 |
|---|---|---|
| `review` | 审查、评估、给改进建议 | 串行审查链 |
| `debug_fix` | 排查、修复、验证 | 串行修复链 |
| `design_build` | 设计并实现 | 串行设计 + 计划 + 执行 |
| `research_compare` | 调研、对比、选型 | 串行研究链 |
| `web_qa` | 浏览器自动化测试、视觉回归、性能审计 | `browser_explore` 后 fan-out 并行 |
| `parallel_investigation` | 同时调研多个对象 | 受控并行探查 |

## 执行流程

```text
用户自然语言（或显式 /orch）
        │
        ▼
是否需要多技能编排？
  否 → 原生单技能匹配
  是 ↓
family-first 识别主 family
  多 family → 澄清，不混编
  单 family ↓
抽取 actions[] + scope + goal
        │
        ▼
rule-first DAG 组装
        │
        ▼
confidence 闸门
  < 0.70  → AskQuestion 澄清
  0.70-0.84 → 展示 Plan Preview 并确认
  ≥ 0.85  → 自动执行
        │
        ▼
side-effect-first 委托执行
  none → direct_skill
  write 单任务 → loop
  write 多子任务 → go
```

## 典型编排

### review

```text
system-review → code-reviewer → clean-code → brainstorming → writing-plans
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

## 执行器边界

| 节点特征 | 执行器 |
|---|---|
| 只读分析 / 审查 / 调研 | `direct_skill` |
| 单任务写代码 / 修复 | `loop` |
| 跨模块 / 多子任务实施 | `go` |

orch 只负责 **“意图 → 执行图”**，不重复：

- loop 的门禁 / 自愈 / G9
- go 的 worktree / 并发 / G10 / 集成回归

## 不做什么

- ❌ 不再暴露编号式 `/orch` 用法
- ❌ 不支持第一版跨 family 混编
- ❌ 不把单技能任务强行升级成多技能编排
- ❌ 不让 LLM 自由规划任意 DAG
- ❌ 不替代 `go` / `loop` 的执行细节

## 参考真源

- `skills/orch/references/intent-schema.json`
- `skills/orch/references/capability-registry.yaml`
- `skills/orch/references/dag-rules.yaml`
- `skills/orch/references/handoff-orch-schema.json`
- `skills/orch/references/families/*.yaml`
- `skills/orch/references/golden-traces/*.json`
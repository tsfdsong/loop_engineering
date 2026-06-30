---
title: skill-hub 复杂度感知调度器 v0.1
date: 2026-06-30
author: tsfdsong
status: ✅ 用户批准（v0.1）
skill: brainstorming → writing-plans → refactoring → verification
location: docs/2026-06-30-skillhub-complexity-aware-design.md
parent_design: docs/2026-06-29-skill-hub-v6-design.md
---

# skill-hub 复杂度感知调度器 v0.1

> **核心目标**：在不破坏 v5.4 baseline + v6.0 Orchestrator 的前提下，叠加"复杂度评分器"层，使 skill-hub 能**根据任务复杂度**自动决策单技能调用 / 双技能串行 / 多技能并行路径——直接回应用户原话"更好的根据任务复杂度调度两个技能"。

---

## 1. 上下文与动机

### 1.1 现状事实（[F]）

| # | 事实 | 来源 |
|---|------|------|
| 1 | skill-hub 当前形态：`SKILL.md`（605 行，v6.4 真正融合后版）+ `references/` 子目录 | `ls -la skills/skill-hub/` |
| 2 | 项目版本：`loopengine v1.0.2`，node 模块，主入口 `.opencode/plugins/loopengine.js` | `package.json` |
| 3 | 最近 10 次提交全部围绕 v6.3/v6.4 重构 | `git log --oneline -10` |
| 4 | 最近 3 个月 95 次提交 → 项目极活跃 | `git log --since="3 months ago" \| wc -l` |
| 5 | v6.0 Orchestrator 当前是 alpha mock —— 真实编排引擎未实现，5 类复合任务为规则模拟 | skill-hub/SKILL.md "🆕 v6.0" 段 |
| 6 | `.workflow/loopengine-skillhub-scheduling/INDEX.md` 列出 10% 缺口 = "端到端试跑 + 性能实测" | `.workflow/.../INDEX.md` 第 7-8 段 |

### 1.2 用户原话意图（直接引用）

> "更好的根据任务复杂度调度两个技能"

**典型场景**：当用户 query 同时命中 `deep-research` 与 `brainstorming` 两个技能时（共同关键词如"调研"、"分析"），当前 skill-hub 走关键词字典 + 6 步兜底，不显式评估"任务复杂度"。

### 1.3 问题陈述

当前调度路径：
```
query → 关键词字典(v5.4) → semantic 兜底 → v6.0 5 类表(规则模拟)
       ↓                    ↓
       命中 1 个技能        命中 2+ 个技能时回退顺序模糊
```

**根本问题**：缺少"任务复杂度"作为显式决策维度。

---

## 2. 设计目标（SMART）

| 维度 | 目标 |
|------|------|
| **Specific** | 复杂度评分器在 4 维度都能独立测试 |
| **Measurable** | 40 unit case 全通过 + v5.4 baseline 27 条 100% 通过 + 端到端准确度 ≥ 85% |
| **Achievable** | 单次 PR 可完成（动 3 个文件、新增 2 个文件）|
| **Relevant** | 直接对应用户原话"按任务复杂度调度" |
| **Time-bound** | 单次 sprint 范围（≤ 2 周）|

---

## 3. 详细设计

### 3.1 架构（4 层 + 1 评分器）

```
┌─────────────────────────────────────────────────────┐
│ Layer 4 · trace + token 收集（已有 · v6.1）        │
├─────────────────────────────────────────────────────┤
│ Layer 3 · 实际调用（已有 · v5.4/v6.0/v6.1 三路）   │
├─────────────────────────────────────────────────────┤
│ Layer 2 · 分支路由（扩展示 · 新增复杂度门）        │
│   ├─ score ≤ 2 → single_skill                    │
│   ├─ score 3-4 → composite_router (v6.0 5 类表)  │
│   └─ score = 5 → parallel_decomposer (go 派发)   │
├─────────────────────────────────────────────────────┤
│ Layer 1 · complexity_scorer(★ 本次新增)            │
│   ├─ dim1_intent_clarity                          │
│   ├─ dim2_candidate_count                         │
│   ├─ dim3_tool_dependency                         │
│   └─ dim4_token_budget                            │
├─────────────────────────────────────────────────────┤
│ Layer 0 · 用户 query（自然语言）                    │
└─────────────────────────────────────────────────────┘
```

### 3.2 组件与变更范围

| 组件 | 状态 | 文件 | 行数估算 |
|------|------|------|---------:|
| `complexity_scorer(query)` 协议 | **新增** | `skills/skill-hub/references/complexity-scorer-spec.md` | ~200 |
| 复杂度评分调度段 | **新增** | `skills/skill-hub/SKILL.md` 插入"v6.5 复杂度感知路由"段 | +80 |
| 测试用例集 | **新增** | `tests/golden-traces/complexity-scorer-baseline.json` | 40 cases |
| Orchestrator alpha mock | 现状不动 | `skills/skill-hub/SKILL.md` v6.0 段 | 0 |
| v5.4 baseline | 现状不动 | `tests/golden-traces/v54-baseline.json` | 0 |
| v6.1 三技能协同 | 现状不动 | `skills/skill-hub/SKILL.md` v6.1 段 | 0 |

**变更范围**：改 1 个文件、新增 2 个文件。

### 3.3 数据流

```
input: query (str)
  ↓
[1] tokenizer: 提取关键词 / 实体 / token 数
  ↓
[2] match_skills(query) → candidates: List[str]   // 复用 v5.4 关键词表
  ↓
[3] compute_4_dim(query, candidates):
    ├─ dim1_intent_clarity   = |matched_keywords| / |total_keywords|
    ├─ dim2_candidate_count  = |candidates|
    ├─ dim3_tool_dependency  = 1 if 'MCP/jcodemunch/WebFetch/Search' in query else 0
    └─ dim4_token_budget     = tokens(query) // 50
  ↓
[4] score = weighted_sum(dim1..dim4)   // 初始各 25% 等权
  ↓
[5] branch_router(score):
    ├─ score ≤ 2     → single_skill(candidates[0])
    ├─ 3 ≤ score ≤ 4 → composite_router(query)    // v6.0 5 类表
    └─ score = 5     → parallel_decomposer(query) // go / subagent-dd
  ↓
output: {
  skill_chain: [...],
  mode: 'single' | 'serial' | 'parallel',
  complexity_score: int,
  dim_breakdown: {dim1..dim4}
}
```

### 3.4 错误处理

| 异常 | 触发条件 | Fallback 优先级 |
|------|----------|----------------|
| `NoSkillMatched` | `match_skills()` 返回空 | 1) v5.4 关键词兜底  2) 提示用户重新表述 |
| `ScorerInternal` | `compute_4_dim` 内部异常 | 1) v6.0 5 类表  2) v5.4 兜底 |
| `ScoreOutOfRange` | `score ∉ [1, 5]` | clamp + log warning |
| `CompositeNotFound` | score 3 时 v6.0 不命中 | v5.4 兜底 |
| `DimensionAllZero` | 4 维全部 0 | score=2 → single_skill 默认路径 |

**铁律**：所有异常必须有 fallback；fallback 优先级 = v5.4 baseline > v6.0 5 类表 > 强制单技能。**绝不让 task 卡住**。

### 3.5 测试策略

#### 3.5.1 单元测试（4 维度 × 10 用例 = 40）

| 维度 | 关键 case |
|------|----------|
| ① 意图清晰度 | "重构 X" / "为什么 Y" / "对比 A B" / "创建 Z" — 10 个 |
| ② 候选技能数 | 1 个命中 / 2 个命中 / 3+ 个命中 — 10 个 |
| ③ 跨工具依赖 | 含 `jcodemunch` / `WebFetch` / `MCP` / 都不含 — 10 个 |
| ④ token 预算 | `< 10` / `10-50` / `50-200` / `> 200` token — 10 个 |

#### 3.5.2 回归测试

- v5.4 baseline `tests/golden-traces/v54-baseline.json` 27 条**全部通过**
- v6.1 协同契约 — 跑通 `subagent-driven-development/bridges/contract.py` 6 个桥接契约

#### 3.5.3 端到端

**复用** `.workflow/loopengine-skillhub-scheduling/96-scheduling-accuracy-test.md` 模板。

#### 3.5.4 性能

- `complexity_scorer` P99 耗时 **< 200ms**
- 不超过 `total_tokens` 字段采样时延（已有）

#### 3.5.5 验收准则

| 维度 | 通过标准 |
|------|----------|
| 行为不变 | v5.4 baseline 27 条全过；v6.1 协同契约 6 个全过 |
| 新能力 | complexity-scorer-baseline.json 40 条全过；端到端调度准确度 ≥ 85% |
| 可读性 | SKILL.md 总行数控制在 ≤ 700 行（当前 605 + 新增 80）|
| 可维护性 | 复杂度评分器本体 ≤ 200 行；4 维度权重集中在一处 |
| 性能 | scorer P99 < 200ms |

---

## 4. 边界与限制

### 4.1 不做什么

- ❌ **不重写 v5.4 baseline**（保留 100% 兼容）
- ❌ **不实现完整 DAG 引擎**（等 Orchestrator 真实现）
- ❌ **不引入外部 LLM API**（保持 $0 成本）
- ❌ **不改 install.sh / update.sh**（MCP 重启问题另案处理）

### 4.2 [H] 假设（未经验证）

- [H] 复杂度阈值 ≤2 / 3-4 / =5 是基于经验的初始权重
- [H] 4 维度各 25% 等权是初始值，未来基于 trace 数据再调
- [H] 端到端调度准确度 ≥ 85% 是参照已有 `96-scheduling-accuracy-test.md` 反推的目标

### 4.3 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 复杂度评分器引入额外延迟 | 用户体验下降 | 设置 timeout fallback 到 v5.4 |
| 评分器权重不准确 | 调度错误 | 所有异常 fall back 到 v5.4 兜底 |
| 没有训练数据集 | 长期不可优化 | 把 trace 数据攒到 `tests/training/` 后续学习 |
| SKILL.md 突破 700 行 | 可读性下降 | 超长则把"v6.5"段外提为 `references/v65-complexity-aware.md` |

---

## 5. 实施前置条件

进入 writing-plans 之前的必要条件：

- [x] v0.1 设计稿用户批准（2026-06-30）
- [ ] Spec 自审通过（占位符/一致性/范围/歧义 4 项）
- [ ] 用户复审已写入 spec 文件
- [ ] `package.json` 验证脚本可跑（读 `scripts/verify-*.sh` 列表）

---

## 6. 变更历史

| 版本 | 日期 | 状态 | 变更 |
|------|------|------|------|
| v0.1 | 2026-06-30 | ✅ 用户批准 | 初稿，方案 B「复杂度感知调度器」|

---

## 7. 关联文档

- **父设计**：`docs/2026-06-29-skill-hub-v6-design.md`（v6.0/v6.1 基础架构）
- **现有 deep-research 调研产物**：`.workflow/loopengine-skillhub-scheduling/`
- **既有测试模板**：`tests/golden-traces/v54-baseline.json`
- **调度准确度测试模板**：`.workflow/loopengine-skillhub-scheduling/96-scheduling-accuracy-test.md`

---

## 8. 自检 4 问（evidence-first 强制）

| # | 问题 | 答案 |
|---|------|------|
| 1 | 有 [F] 依据吗？ | ✅ 5 项事实全部从 git/file/docs 验证 |
| 2 | [H] 假设明确标注了吗？ | ✅ 阈值 2/3-4/5、25% 等权、85% 准确度全部标 [H] |
| 3 | 错了损失大吗？ | 低 — 所有异常 fallback 到 v5.4 baseline |
| 4 | 能说"我不清楚"吗？ | ✅ 没有训练数据集这点已坦承 |

---

> **下一步**：调 `writing-plans` 技能生成详细实施计划（本 spec 不含实施步骤）。

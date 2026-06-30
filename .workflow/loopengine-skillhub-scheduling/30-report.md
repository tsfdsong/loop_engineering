# 调研报告：LoopEngine skill-hub 的自动调度算法

> 🔴 **版本声明**：基于 v6.1（2026-06-29）；Plan Orchestrator 仍是 alpha mock
> 📅 **调研日期**：2026-06-29
> 🔍 **调研方法**：直接读 `skill-hub/SKILL.md` 全文 + 4 个 references 子文档

---

## 摘要

LoopEngine skill-hub 的自动调度算法是**"v5.4 兼容 + v6.0 复合编排（alpha mock）+ v6.1 三技能协同"** 三层架构。核心入口是 `SKILL.md` 的 53 技能关键词表 + 12 类别冲突裁决表 + 6 步语义兜底；扩展层是 5 类预设复合任务，由"规则判定 + LLM 验证"混合策略触发；协同层定义了 go / loop / subagent-dd 三个不可替代技能的调用边界和决策树。

**最反直觉的事实**：L1 Plan Orchestrator 文档完整但**真实引擎未实现**（alpha mock），5 类复合任务实际跑的是 LLM 验证路径。

---

## 演进时间线（理解 3 层架构的前置）

| 版本 | 关键变化 | 状态 |
|------|---------|------|
| **v5.4** | 53 技能关键词表 + 冲突裁决 + 6 步兜底 | 🟢 **生产可用**（100% 兼容）|
| **v6.0** | 5 类复合任务 + 规则判定 + LLM 验证 | 🟡 **alpha mock**（真实引擎未实现）|
| **v6.1** | go / loop / subagent-dd 三技能协同 + 桥接（opt-in）| 🟢 生产可用 |

> 设计哲学：**v5.4 兼容永远是底线**——v6.0/v6.1 都通过"黄金轨迹回归测试"保证不破坏 v5.4 行为（`tests/golden-traces/v54-baseline.json` 不动）。

---

## 第 1 层：核心调度（v5.4 兼容）

调度算法最基础的形态。**当用户输入不命中复合任务时，走这一层**。

### 1.1 关键词表

`skill-hub/SKILL.md` 维护了一张 53 技能 × 12 类别的映射表。每条记录形如：

```
技能名 | 触发关键词 | 适用场景
```

例如：
- `brainstorming` | 创意、设计、头脑风暴、想法、方案 | 编码前的需求探索
- `systematic-debugging` | 调试、报错、Bug、不工作、排查 | 遇到任何 bug 或测试失败
- `evidence-first` | 分析、比较、评估、为什么、有什么用 | 项目分析前必查 5 项事实

**关键设计 [F 来自 SKILL.md]**：
- 同一技能可能被多个类别引用（如 `brainstorming` 同时出现在"规划与执行"和"产品管理"）
- description 字段是 AI 自动调度的核心依据

### 1.2 冲突裁决

当多个技能都匹配时，按"类别级冲突裁决"选 1 个。每个类别下都有显式裁决句式：

| 用户说 | 命中技能 | 裁决 |
|--------|---------|------|
| "代码太乱" | clean-code / code-complete | → **clean-code**（v6.1.1 三源合并）|
| "审查这段代码" | code-reviewer / system-review | → code-reviewer（单文件）/ system-review（项目级）|
| "写个测试" | testing-patterns / TDD | → testing-patterns / 明确 TDD 时切换 |
| "调试/报错" | systematic-debugging + 其他 | → **systematic-debugging**（优先）|

**5 条核心指令**（SKILL.md 末尾）：
1. 每次只加载一个技能（除非 `/composite`）
2. 多种技能适用时按"冲突裁决"选 1 个
3. Bug/报错 → 优先 `systematic-debugging`
4. 完成前必须验证 → 调 `verification-before-completion`
5. 优先精准技能（`api-security` 优先于更宽泛的安全技能）

### 1.3 6 步语义兜底

关键词表无匹配时，按以下优先级二次判断：

1. 含"审查系统/审查架构/检查矛盾/系统审计" → `system-review`
2. 含"调研/对比/选型" → `brainstorming`（发散探索）
   含"分析/探索/研究/评估" → `evidence-first`（事实优先）
3. 含"修/改/更新/优化/改进" + 具体对象 → `refactoring`
4. 含"怎么/如何/为什么" → `brainstorming`（探索性问题）
5. 含"能不能/可不可以/是否" → `brainstorming`（可行性分析）
6. 以上都不匹配 → **直接执行，不强行调用**

### 🔴 反直觉点（第 1 层）

**优先级 6 显式放弃**——"直接执行，不强行调用"是反 AI 过度代理的设计。AI 在没把握时**承认不知道**，比强行选个错的技能更安全。

---

## 第 2 层：复合编排（v6.0 alpha）

当用户输入命中 ≥ 2 个技能且属于"互补关系"时，触发复合任务编排。

> ⚠️ **alpha 阶段警告**：Plan Orchestrator 真实引擎**未实现**，5 类复合任务的"默认技能链"是**规则模拟**。实际跑的是"LLM 验证路径"——AI 列出 Top-2 候选让你选。

### 2.1 5 类预设复合任务

来自 `references/composite-task-types.md`：

| # | 类型 | 默认技能链 | 编排方式 | 触发关键词 |
|---|------|----------|:--:|----------|
| 1 | 调研+决策 | `brainstorming → system-review → writing-plans` | 串行 | 调研 + 决策/选型/对比 |
| 2 | 分析+建议 | `system-review → brainstorming` | 串行 | 审查/分析 + 改进/建议 |
| 3 | 诊断+修复 | `systematic-debugging → verification-before-completion` | 串行 | 报错/Bug + 修复 |
| 4 | 设计+实现 | `brainstorming → writing-plans → executing-plans` | 串行 | 设计 + 实现/开发 |
| 5 | 规划+并行 | `subagent-driven-development` | **并行** | 并行/多任务 + 调研 |

### 2.2 触发判定（混合策略）

**第一层：规则判定**（零 token）
- 关键词扫描（复用 v5.4 关键词表）
- 复合任务触发条件：意图数 ≥ 2 + 命中 ≥ 2 个不同技能 + 属于同一复合模式

**第二层：LLM 验证**（仅在规则冲突时启用）
- 列出 **Top-2 候选**让用户选（**硬约束**）
- 不允许 LLM 单独决定

### 2.3 不可触发场景

- 关键词命中 1 个 → 走 v5.4 单技能
- 命中 ≥ 2 但属于"竞争关系" → 走 v5.4 冲突裁决
- 触发词仅命中"Bug/报错" → 优先 `systematic-debugging`

### 🔴 反直觉点（第 2 层）

**LLM 验证的硬约束是"防御 AI 自评盲点"**——这个安全设计在大多数 agent 系统中**不常见**。它承认了 AI 不能可靠地自评，所以强制人类介入。

---

## 第 3 层：三技能协同（v6.1）

当任务"超出一个技能的能力范围"时，调度算法会进入第 3 层——go / loop / subagent-dd 三个**不可替代**的技能按决策树协同。

### 3.1 三个技能定位

| 技能 | 抽象层 | 核心能力 | 不可替代点 |
|------|--------|---------|----------|
| **`go`** v4.0 | 编排层（Orchestrator） | 多任务拆分 + DAG + worktree 真并发 + 全局回归 | 唯一具备真并发 + 跨模块集成 |
| **`loop`** v4.1 | 执行层（Closer） | 单任务闭环 + 自动化门禁 + 自愈 A/B/C/🎨 | 唯一带自动自愈分级 + 经验库 |
| **`subagent-driven-development`** | 平行执行范式 | 多任务串行 + 人工子代理双阶段审查 | 唯一具备"spec ✅ → code quality"强顺序 + TDD 强制 |

### 3.2 决策树（v6.1 新增）

```
收到任务
  │
  ├─ 有现成 writing-plans 计划？
  │   ├─ 是 → subagent-driven-development
  │   └─ 否 ↓
  │
  ├─ 跨模块/需要 DAG/需要 worktree 真并发？
  │   ├─ 是 → go
  │   └─ 否 ↓
  │
  ├─ 端到端单任务闭环 + 自动化门禁 + 自愈？
  │   ├─ 是 → loop
  │   └─ 否 ↓
  │
  └─ 临时多问题域并行调研（无 plan）？
      └─ 是 → dispatching-parallel-agents
```

### 3.3 调用关系（硬约束）

- **`go` → `loop` 单向调用**：`go` Step ⑤ 调度子任务 → 每个 worktree 内调 `loop --auto`
- **`subagent-dd` 仅在主会话层级调用**：派发的 subagent **不**再触发 Orchestrator 路径
- **`subagent-dd` 与 `dispatching-parallel-agents` 互斥**：有 plan → subagent-dd；临时多问题 → dispatching-parallel-agents

### 3.4 桥接（opt-in · v6.1 新增）

```bash
# 默认（不启用）
LOOPENGINE_BRIDGES=disabled    # 默认值

# 启用桥接（alpha）
LOOPENGINE_BRIDGES=alpha       # 加载 bridges/contract.py
```

桥接契约有 6 个核心组件（`dispatch_implementer` / `dispatch_spec_reviewer` / `dispatch_code_quality_reviewer` / `model_select` / `handle_implementer_status` / `review_gate`），可被 go/loop 复用。

### 🔴 反直觉点（第 3 层）

**go → loop 单向调用是硬约束，不是优化建议**。违反这条规则（loop 内部调 system-review）会触发 skill-hub 的"边界违规检测"——自动降级 + 警告。这意味着协同不是"自由组合"，而是"严格单向 + opt-in 桥接"。

---

## 关键发现汇总

### 1. 核心调度算法本质
**关键词表 + 冲突裁决 + 6 步兜底**——是个**确定性 + 简单**的设计（不像一些 agent 框架用 ML 模型决定调度）。

### 2. 复合编排的"半成品"状态
v6.0 文档完整但 alpha mock，意味着：
- ✅ 5 类预设的"模式识别"是真实的
- ⚠️ "自动串行执行"是模拟的（实际走 LLM 验证）
- ❌ **没有"自动根据 plan 推断 execution_path"**（v6.1 修复点：未来方向）

### 3. 协同的"严格分层"哲学
go / loop / subagent-dd **不互相替代**，但有单向调用（go → loop）和 opt-in 桥接。这与"微服务架构"的"独立 + 接口"哲学一致。

### 4. 性能与兼容性
- v5.4 黄金轨迹 27 条必须 100% 兼容（`tests/golden-traces/v54-baseline.json` 不动）
- 性能预算：相对 v5.4 增加 < 5%（**设计目标，未实际测量**）
- 桥接默认关闭（避免引入新风险）

---

## 决策建议（基于本调研）

### 场景 1：你要写一个 1-2 步的小功能
**走第 1 层**：直接用关键词表 + 冲突裁决
**典型工具**：`brainstorming` → `loop`

### 场景 2：你要做"调研+决策"复合任务
**走第 2 层**：明确说"调研 + 选型"
**典型工具**：`brainstorming → system-review → writing-plans`
**注意**：Plan Orchestrator 是 alpha mock，实际靠 LLM 验证路径

### 场景 3：你要做跨模块的大型功能
**走第 3 层**：`/go <一句话需求>`
**典型工具**：`go` 编排 + `loop` 闭环

### 场景 4：你要做并行调研多个框架
**走第 3 层**：`/composite 5 ...` 或 `dispatching-parallel-agents`
**注意**：有现成 plan → subagent-dd；临时 → dispatching-parallel-agents

---

## 局限与未解之谜

### 局限 1：本文档未抓的 references
- `trace-format.md` — trace 格式（可能影响调度决策可观测性）
- `orchestrator-protocol.md` — 向后兼容的 orchestrator 协议（可能影响 alpha mock 失败时的降级行为）

### 局限 2：实测性能数据缺失
- "相对 v5.4 增加 < 5%"是**设计目标**，未实际测量
- 真实性能可能因 LLM 验证频繁触发而**显著高于 5%**

### 局限 3：未验证 v5.4 → v6.0 → v6.1 的版本迁移影响
- 历史决策细节未追溯
- v5.4 黄金轨迹的"27 条"具体内容未查

### 局限 4：未做"实际跑 5 类复合任务"的端到端验证
- 文档说"alpha mock"——但 mock 在哪些场景会失败，未实测
- 如果用户生产环境依赖复合任务，需要**先小规模试跑**

### 局限 5：未涉及环境变量 `LOOPENGINE_ORCHESTRATOR` / `LOOPENGINE_BRIDGES` 的影响
- alpha / disabled / off 三种模式的具体行为差异
- 真实生产部署中应该选哪个？

---

## 引用清单

### T1（直接读 SKILL.md / references/）
1. `skill-hub/SKILL.md`（27446 字节）— 主入口 + 53 技能关键词表 + 5 条核心指令
2. `skill-hub/references/composite-task-types.md`（6478 字节）— 5 类复合任务定义
3. `skill-hub/references/complexity-evaluator.md`（2126 字节）— 复杂度评估 + LLM 验证触发
4. `skill-hub/references/plan-orchestrator-protocol.md`（3047 字节）— Plan Orchestrator 协议
5. `skill-hub/references/skill-relationships.md`（9485 字节）— 三技能协同契约

### T2（间接 / 文档说明）
- 无（本次全部从一手代码/文档获取）

### Reject
- 无

---

## 一句话结论

> skill-hub 的调度算法是"**关键词表 + 冲突裁决 + 6 步兜底**"（v5.4 基础）+ "**5 类复合编排**"（v6.0 alpha mock）+ "**3 技能协同 + 桥接**"（v6.1）三层架构。**生产可用层**是 v5.4 和 v6.1；**alpha 阶段**是 v6.0 复合编排（真实引擎未实现，靠 LLM 验证路径）。

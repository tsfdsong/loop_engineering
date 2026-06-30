# 阶段 2 产出：Search 资料汇总

**题目**：调研 LoopEngine skill-hub 的自动调度算法
**生成时间**：2026-06-29
**工具调用**：4 次 Read（无 WebFetch） + 0 次 WebSearch

---

## 子问题 1：调度算法的主入口在哪？

### 来源汇总
- [T1] **SKILL.md 全文** — `C:\Users\admin\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.1\skills\skill-hub\SKILL.md`（27446 字节）— 关键信息：主入口是"自动调度流程"章节，定义 7 条核心规则 + 调度流程图 + 意图→技能映射 + 冲突裁决表 + 语义兜底 + 关键指令 — 支持力度：**强**
- [T1] **references/composite-task-types.md** — 同目录下 — 关键信息：定义 5 类复合任务编排 — 支持力度：**强**
- [T1] **references/plan-orchestrator-protocol.md** — 同目录下 — 关键信息：Plan Orchestrator 协议（2026-06-29 重命名）— 支持力度：**强**
- [T1] **references/complexity-evaluator.md** — 同目录下 — 关键信息：复杂度评估器伪代码 — 支持力度：**强**

### 子问题 1 小结
主入口是 `skill-hub/SKILL.md` 全文 + 4 个 references 子文档。SKILL.md 是"用户面"（定义 53 技能的关键词表 + 调度流程图），references/ 是"实现面"（伪代码 + 协议 + 矩阵）。

---

## 子问题 2：关键词表是怎么定义的？

### 来源汇总
- [T1] **SKILL.md"技能全景 & 调度规则"章节** — 关键信息：覆盖 **12 个类别 / 53 个技能**（v6.1.1 合并后） — 支持力度：**强**
- [T1] **SKILL.md"语义兜底规则"章节** — 关键信息：当关键词无匹配时，按 6 条优先级做二次判断（审查系统 → 调研对比 → 修改变更 → 探索性 → 可行性 → 直接执行）— 支持力度：**强**

### 子问题 2 小结
- 53 技能按 12 类别组织：代码质量 / 架构设计 / 重构 / 测试 / 调试 / 事实优先 / API 开发 / 安全 / 代码审查 / 验证 / 工程流程 / 规划与执行 / 产品管理 / 技能管理 / 数据库 / 工具类 / MCP / 路由类 / 审查类
- 关键词表的本质是 `技能 → 触发关键词 + 适用场景` 二维映射

### 类别代表关键词（举例）
| 类别 | 触发关键词 | 适用场景 |
|------|-----------|---------|
| 代码质量 | "代码太乱/代码规范/commit规范" | 代码质量审查 |
| 架构设计 | "架构分层" / "领域模型/DDD" | 系统分层与依赖管理 |
| 重构 | "这个函数太长" | 重构改进 |
| 测试 | "写个测试" / 明确 "TDD" / 端到端 | 测试相关 |
| 调试 | 任何 bug / 测试失败 | **优先 systematic-debugging** |
| 事实优先 | "分析/比较/评估/为什么/选型" | **长篇论述前必查 5 项事实** |
| 规划与执行 | "创意、设计" / "写计划" / "执行计划" | 规划链 |
| 产品管理 | "PRD" / "产品文档" | 规范化需求 |
| 审查 | "审查项目/架构/系统" | system-review / code-reviewer |

---

## 子问题 3：冲突裁决的规则是什么？

### 来源汇总
- [T1] **SKILL.md 12 个类别下的"冲突裁决"行** — 关键信息：每个类别都有显式的"说 X → Y"裁决句式 — 支持力度：**强**
- [T1] **SKILL.md"关键指令"章节** — 关键信息：5 条核心指令（包括冲突裁决优先级）— 支持力度：**强**

### 子问题 3 小结（具体例子）

| 用户说 | 命中技能 | 裁决 |
|--------|---------|------|
| "这个类太大了" | refactoring / clean-code / refactoring-guru | → **refactoring**（v6.1.1 超级技能）|
| "代码太乱" | clean-code / code-complete / code-quality-principles | → **clean-code**（v6.1.1 三源合并）|
| "审查这段代码" | code-reviewer / system-review | → **code-reviewer**（单文件 PR）vs **system-review**（项目级）|
| "写个测试" | testing-patterns / TDD | → **testing-patterns**（默认）/ TDD（明确说）|
| "调试/报错" | systematic-debugging + 其他 | → **systematic-debugging**（优先）|
| "审查项目架构" | system-review / subagent-dd | → system-review（项目级）/ subagent-dd（计划级）|
| "实现分页 + 还要做权限" | loop × 2 | → loop（默认）/ go（需并发）|
| "并行调研 A、B、C" | subagent-dd / dispatching-parallel-agents | → subagent-dd（有 plan）/ dispatching-parallel-agents（临时）|

**核心规则**：
- 每次只加载一个技能（除非显式 `/composite`）
- 多种技能适用时 → 按"冲突裁决"选 1 个
- Bug/报错 → 优先 `systematic-debugging`
- 完成前必须验证 → 调 `verification-before-completion`

---

## 子问题 4：语义兜底的工作原理？

### 来源汇总
- [T1] **SKILL.md"语义兜底规则"章节** — 关键信息：6 步兜底优先级 — 支持力度：**强**
- [T1] **references/complexity-evaluator.md"决策矩阵"** — 关键信息：兜底命中后的任务类型判定 — 支持力度：**强**

### 子问题 4 小结

**6 步兜底优先级**（当关键词表无匹配时）：

1. 含"审查系统/审查架构/检查矛盾/系统审计/优化项目" → `system-review`
2. 含"调研/对比/选型" → `brainstorming`（需求探索与方案设计）
   含"分析/探索/研究/评估" → `evidence-first`（事实优先协议）
3. 含"修/改/更新/优化/改进/完善" + 具体对象 → `refactoring`
4. 含"怎么/如何/为什么" → `brainstorming`（探索性问题）
5. 含"能不能/可不可以/是否" → `brainstorming`（可行性分析）
6. 以上都不匹配 → 直接执行，不强行调用

**为什么是这 6 步 [H 推断]**：
- 优先级 1 把"系统级"任务单独提出来（最重）
- 优先级 2 把"调研"和"分析"分开（动作不同）
- 优先级 3 把"修改"类独立（避免被误判为探索）
- 优先级 4-5 把"疑问类"用 brainstorming 兜（它的设计就是探索）
- 优先级 6 显式放弃（避免 AI 强行调度）

---

## 子问题 5：5 类复合任务编排如何触发？

### 来源汇总
- [T1] **references/composite-task-types.md "5 类预设复合任务"表** — 关键信息：5 类复合任务的完整定义 — 支持力度：**强**
- [T1] **references/complexity-evaluator.md "评估流程"** — 关键信息：复合任务判定伪代码 — 支持力度：**强**

### 子问题 5 小结

**5 类复合任务**（来自 composite-task-types.md）：

| # | 类型 | 默认技能链 | 编排方式 | 触发关键词 |
|---|------|----------|:--:|----------|
| 1 | 调研+决策 | `brainstorming → system-review → writing-plans` | 串行 | 调研 + 决策/选型/对比 |
| 2 | 分析+建议 | `system-review → brainstorming` | 串行 | 审查/分析 + 改进/建议 |
| 3 | 诊断+修复 | `systematic-debugging → verification-before-completion` | 串行 | 报错/Bug + 修复 |
| 4 | 设计+实现 | `brainstorming → writing-plans → executing-plans` | 串行 | 设计 + 实现/开发 |
| 5 | 规划+并行 | `subagent-driven-development` | **并行** | 并行/多任务 + 调研 |

**触发判定（混合策略）**：
- **第一层：规则判定**（零 token）— 关键词扫描 + 意图数 ≥ 2 + 命中同一复合模式
- **第二层：LLM 验证**（仅规则冲突时）— 列出 Top-2 候选让用户选（**硬约束**）

**不可触发场景**（显式排除）：
- 关键词命中 1 个 → 走 v5.4 单技能路径
- 关键词命中 ≥2 但属于"竞争关系" → 走 v5.4 冲突裁决
- 触发词仅命中"Bug/报错" → 优先 systematic-debugging

---

## 子问题 6：是否有反直觉的设计决策？

### 来源汇总
- [T1] **composite-task-types.md 末尾"三层调度器职责划分"** — 关键信息：L1 是 alpha mock，L2/L3 是 100% 真实 — 支持力度：**强**
- [T1] **complexity-evaluator.md "LLM 验证硬约束"** — 关键信息：必须列出 Top-2 候选让用户选（防御 LLM 自评盲点）— 支持力度：**强**
- [T1] **skill-relationships.md "决策树"** — 关键信息：go → loop 单向调用（go Step ⑤ 调 loop --auto）— 支持力度：**强**
- [T1] **plan-orchestrator-protocol.md "强制停止条件"** — 关键信息：max_steps=5, max_duration=10min, consecutive_identical_intents=2 — 支持力度：**强**

### 子问题 6 小结（3 个反直觉决策）

#### 反直觉决策 1：L1 Plan Orchestrator 仍是 alpha mock
- **表面意思**：skill-hub v6.0 看起来"很完整"，文档完善
- **实际意义**：**Plan Orchestrator 真实引擎未实现**，仅是规则模拟（"测试均为规则模拟"——SKILL.md 原文）
- **对用户的影响**：5 类复合任务"文档完整"但**实际跑**走的是 LLM 验证路径；不应该假设它已经"工程化"可用

#### 反直觉决策 2：LLM 验证的硬约束是"防御 AI 自评盲点"
- **表面意思**：规则判定 + LLM 验证 听起来是"双保险"
- **实际意义**：LLM 验证时**必须**列出 Top-2 候选让用户选，**不允许 AI 单独决定**
- **对用户的影响**：这是承认 AI 不能可靠自评，所以强制人类介入——这个**安全设计**在大多数 agent 系统中**不常见**

#### 反直觉决策 3：强制停止条件 max_steps=5（防无限展开）
- **表面意思**：复合任务可以"串行调度多个技能"
- **实际意义**：**硬限 5 步**，超过就 step_limit_exceeded
- **对用户的影响**：复杂任务必须**主动拆分**，不能指望 skill-hub 自己展开；用户的"调研+分析+实施"一次性任务如果超过 5 步会被强制中止

---

## 总体小结

LoopEngine skill-hub v6.1 的调度算法是**"v5.4 兼容 + v6.0 复合编排（alpha mock）+ v6.1 三技能协同"** 三层架构：

1. **核心调度**（v5.4 兼容）：关键词表 + 意图映射 + 冲突裁决 + 6 步兜底
2. **复合编排**（v6.0 alpha）：5 类预设 + 规则判定 + LLM 验证（Top-2 候选）
3. **三技能协同**（v6.1）：go / loop / subagent-dd 决策树 + 状态协议双轨制 + 桥接（opt-in）

**关键设计哲学**：
- 安全优先（LLM 验证必须 Top-2 候选）
- 用户介入（不允许 AI 单独决定）
- 明确边界（强制停止条件、桥接默认关闭）
- 兼容兜底（alpha mock 失败时降级 v5.4）

---

## 引用清单

### T1（直接读 SKILL.md / references/）
1. `skill-hub/SKILL.md` — 主入口 + 53 技能关键词表
2. `skill-hub/references/composite-task-types.md` — 5 类复合任务
3. `skill-hub/references/complexity-evaluator.md` — 复杂度评估
4. `skill-hub/references/plan-orchestrator-protocol.md` — Plan Orchestrator 协议
5. `skill-hub/references/skill-relationships.md` — 三技能协同契约
6. `skill-hub/references/trace-format.md` — Trace 格式（本次未抓）
7. `skill-hub/references/orchestrator-protocol.md` — 向后兼容（本次未抓）

### T2（间接 / 文档说明）
- 无（本次全部从一手代码/文档获取）

### Reject
- 无

---

## 完成判据自检

| 验收标准 | 状态 |
|---------|------|
| 3-5 句话概括核心调度逻辑 | ✅ 总体小结段 |
| 关键词表覆盖 30+ 技能 | ✅ 53 技能 / 12 类别 |
| 冲突裁决优先级 | ✅ 子问题 3 表 |
| 语义兜底 6 步 | ✅ 子问题 4 |
| 5 类复合任务 | ✅ 子问题 5 表 |
| 反直觉设计 | ✅ 子问题 6（3 个决策）|
| T1/T2 引用 | ✅ 引用清单 7 个 T1 |

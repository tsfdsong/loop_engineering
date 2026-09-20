---
name: spec-driven-development
description: |
  TRIGGER: 有批准的设计需要拆任务 / 写实施计划 / "spec → plan → task" / 实施计划 / 任务清单（不用于：从零探索设计用 brainstorming，单 PR 代码审查用 code-reviewer）
  RULE: V6 一致性 — 架构级改动后必查需求↔实现一致性
  DETAIL: 本 SKILL.md（OpenSpec 三段式）+ AGENTS.md §V6
---

# spec-driven-development — 规格驱动开发（v2.0 · writing-plans 升级）

> v2.0 升级自 writing-plans，引入 OpenSpec 三段式（requirements → design → tasks）+ 跨工具 handoff 提示

## 概述

撰写详尽的实施计划，假设执行的工程师对我们的代码库零上下文、品味存疑。把他们需要知道的一切写进文档：每个任务改哪些文件、代码、测试、可能要查的文档、怎么测。以小步任务的形式给出完整计划。DRY。YAGNI。TDD。频繁 commit。

假设他们是熟练开发者，但对我们的工具链和问题域几乎一无所知。假设他们不太擅长好的测试设计。

**开始时声明：** "我正在使用 spec-driven-development 技能撰写实施计划。"

**上下文：** 若在隔离 worktree 中工作，worktree 应在执行时通过 `superpowers:using-git-worktrees` 技能创建。

**计划保存至：** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- （用户的计划位置偏好覆盖此默认值）

## OpenSpec 三段式（核心方法论）

OpenSpec 三段式把规格驱动工作组织为三个逐级流动的产物。写逐任务计划之前，确保上游两段已存在（来自 brainstorming 或既有设计工作）；若只有需求已知，先补设计缺口再拆任务。

### 1. requirements.md（需求规格）
- 用户目标 + 约束 + 验收标准
- 不含技术实现

### 2. design.md（设计决策）
- 架构选型 + 关键决策 + trade-off
- 含反选项清单（v2.0 工程实践红线 R1.1 · 已回归到 brainstorming skill）

### 3. tasks.md（任务清单）
- 拆分为可独立执行的任务（bite-sized · 2-5 分钟）
- 每任务含验收条件 + commit 指令
- **继承 spec 的 Loop Execution Contract**；plan 级补充 Verification / Termination / Escalation（见下文）

## Loop Execution Contract（plan 级 · 与 brainstorming 衔接）

> 单点真源：`skills/shared/references/loop-execution-contract.md`
> brainstorming spec 提供 Goal + Acceptance + Non-goals + Stop Escalation；本 skill 在 plan **头部写一次**下列三块，**禁止**在每个 task 重复 Termination 矩阵。

| Plan 级块 | 内容 |
|-----------|------|
| **Verification Contract** | 验收条目 → 验证命令/动作 → 预期结果 |
| **Termination Contract** | 仅 `done` / `blocked` / `degraded` / `handoff-required` |
| **Escalation Mapping** | 何时 `/loop`、`/goal`、`/go`；何时 handoff 回上游 |

**硬规则**：
- Verification 表必须覆盖 spec 中全部 Acceptance Contract 条目
- Termination 术语与 `go` handoff、`goal-first` 降级枚举对齐，不发明新终态名
- **不复制** `loop` 的 G0–G9 / self-healing 全文；执行器细节见 `skills/loop/references/gate-matrix.md`

Task 内引用 Verification ID（如 `V1`），不重复写终态四表。

## Scope Check（范围检查）

若 spec 覆盖多个独立子系统，应在 brainstorming 阶段拆成子项目 spec。若没拆，建议拆为多个计划——每个子系统一个。每个计划应能独立产出可运行、可测试的软件。

## 文件结构

定义任务之前，先规划要创建/修改哪些文件、各自职责。分解决策在这里锁定。

- 设计单元边界清晰、接口明确。每个文件一个明确职责。
- 你对能整个装进上下文的代码推理最好，对聚焦文件的编辑也更可靠。宁小而聚焦，不做大而杂。
- 一起变的文件放一起。按职责拆，不按技术分层拆。
- 在既有代码库中遵循既有模式。若代码库用大文件，不要单方面重构——但你正在改的文件已失控时，把拆分纳入计划是合理的。

此结构决定任务分解。每个任务应产出独立成立、可独立理解的改动。

## 小步任务粒度

**每步一个动作（2-5 分钟）：**
- "写失败的测试" —— 一步
- "跑它确认失败" —— 一步
- "写最小实现让测试通过" —— 一步
- "跑测试确认通过" —— 一步
- "commit" —— 一步

## 计划文档头部

**每个计划必须以此头部开始：**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

## Global Constraints

> **逐字复制，禁止改写或摘要**（2026-09-20 引入，源自 superpowers v6.0.0）— 约束不进计划 = 下游 implementer/reviewer 收不到。subagent 不继承会话上下文，这个块是它们收到全局约束的唯一保证。

- [逐字粘贴适用约束：红线摘要（C1-C5）/ 编码规范 / 禁用模式 / PR 行数上限 / 提交规范 …]

## Verification Contract

| ID | 来源验收 | 命令/动作 | 预期 |
|----|----------|-----------|------|
| V1 | … | … | … |

## Termination Contract

**Done when:** …
**Blocked when:** …
**Degraded when:** …（无则写「本轮不适用」）
**Handoff-required when:** …

## Escalation Mapping

- 执行路径：`/loop` | `/goal` | `/go` — …
- Goal→loop 降级：见 `docs/2026-07-21-goal-first-executor-routing-design.md`（plan 只写本任务触发条件）

## Non-goals

[继承 spec · 本轮不做 …]

---
```

## 任务结构

````markdown
### Task N: [Component Name]

**Verifies:** V1, V2（引用 Verification Contract ID，不重复终态矩阵）

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**（2026-09-20 引入，源自 superpowers v6.0.0）
- Consumes: [本任务依赖的上游产出 — 符号 / 文件 / API，含来源任务号]
- Produces: [本任务产出、下游任务会消费的符号 / 文件 / API]

- [ ] **Step 1: 写失败的测试**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: 写最小实现**

```python
def function(input):
    return expected
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## 禁止占位符

每步必须包含工程师需要的实际内容。以下都是**计划缺陷**——绝不写：
- "TBD"、"TODO"、"以后实现"、"细节待填"
- "加适当的错误处理" / "加校验" / "处理边界情况"
- "给上面的内容写测试"（不带实际测试代码）
- "类似 Task N"（重复代码——工程师可能乱序读任务）
- 只说做什么不说怎么做的步骤（代码步骤必须有代码块）
- 引用任何任务中都没定义的类型、函数、方法

## Remember（要点）
- 永远用精确文件路径
- 每步代码完整——步骤改代码就展示代码
- 精确命令 + 预期输出
- DRY、YAGNI、TDD、频繁 commit

## 与其他 skill 的衔接

### 上游：brainstorming
- brainstorming 产出 spec（含 Goal / Acceptance / Non-goals / Stop Escalation）→ 本 skill 接收并写入 plan 头部契约块

### 下游：executing-plans / subagent-driven-development / loop / go
- 本 skill 产出 plan → executing-plans 或 subagent-driven-development 按 task 执行
- 单任务、验收齐全 → `/loop` 或宿主 `/goal`（见 Escalation Mapping）
- 多 task / 跨模块 → `/go`（thin-loop 任务包须带齐 goal + acceptance）

## §N. 跨工具 handoff 提示（v2.0 借鉴 ECC/ORCH · 深度 1.5）

### 何时建议切换工具
| 场景 | 目标工具 | 触发信号 |
|---|---|---|
| UI 视觉验证 | Cursor | 涉及 .tsx/.vue 改动 |
| 深度推理 | Claude Code | 架构问题卡住 / 复杂 debug |
| 中文场景 | TRAE | 需求含大量中文上下文 |
| 终端批处理 | ZCode | 多文件脚本化改动 |

### handoff 协议（深度 1.5 · 用户手动复制）
生成简短"上下文摘要 JSON"（goal / completed / pending / key_files / decisions / blockers），用户复制到目标工具首条消息。

完整跨工具协议设计（含双向回传 + 冲突检测）见 spec-D（v2.0 完成后启动）。

## Self-Review（自审）

写完计划后，以新鲜视角对照 spec 检查计划。这是你自己跑的清单——不是派遣 subagent。

**1. Spec 覆盖：** 逐条过 spec 的每节/每需求。能指出实现它的任务吗？列出缺口。

**2. 占位符扫描：** 在计划中搜上方"禁止占位符"的红旗模式。发现就修。

**3. 类型一致性：** 后续任务用的类型、方法签名、属性名与前文定义的一致吗？Task 3 叫 `clearLayers()`、Task 7 叫 `clearFullLayers()` 就是 bug。

**4. Loop execution contract：** Verification 覆盖 spec 每条 Acceptance？Termination 只用 done/blocked/degraded/handoff-required？Escalation 指对了执行器（loop/goal/go）？计划里没有 G0–G9 复制粘贴？

**5. Pre-flight conflict check：**（2026-09-20 引入，源自 superpowers v6.0.0）任务之间有互相矛盾的指令吗（同一文件被多个任务改但顺序约束缺失、命名冲突、Global Constraints 与某任务要求互斥）？计划本身要求了会被 reviewer 标记的缺陷吗（放宽测试阈值掩盖失败、吞异常、绕过验证 Gate）？发现 = 现在修，不要等执行中途撞上。

发现问题就地修。不必重审——修完继续。spec 需求没任务覆盖就补任务。

## Execution Handoff（执行交接）

保存计划后，给出执行选择：

**"计划完成，已保存至 `docs/superpowers/plans/<filename>.md`。三种执行选项：**

**1. Subagent-Driven（简单计划推荐）** —— 每任务派全新 subagent，任务间评审，迭代快
- **REQUIRED SUB-SKILL:** 使用 superpowers:subagent-driven-development
- 每任务全新 subagent + 两阶段评审

**2. Inline Execution（单会话工作）** —— 本会话内用 executing-plans 执行，带检查点批执行
- **REQUIRED SUB-SKILL:** 使用 superpowers:executing-plans
- 带检查点的批执行

**3. /go 工程模式（工程级计划推荐，v4.0+）** —— 工程化执行：worktree 隔离 + 自动拆分 + 降级兜底 + G10 系统审查
- **适用场景**：跨模块 / 多文件 / 需要并发 / 复杂任务
- **执行命令**：`/go <一句话需求>`（无需提前写 plan，go 会自动拆分）
- **不适用**：单文件修改 / 简单重构 / 教学示例
- **与本 plan 的关系**：可选择忽略本 plan，直接用 /go 重新拆任务

**选哪种？"**

**选择判断标准：**
- 计划 ≤ 3 个任务 + 单文件 → 选项 1 或 2
- 计划 ≥ 4 个任务 / 跨文件 / 需要并发 → **选项 3（/go）**
- 不确定 → 选项 1（推荐）

**Plan frontmatter 字段（写完后自动添加）：**

```markdown
---
execution_path: subagent-driven  # 写完后让用户填 / inline / go
---
```

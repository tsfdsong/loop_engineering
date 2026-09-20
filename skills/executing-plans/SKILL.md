---
name: executing-plans
description: |
  TRIGGER: 有书面实施计划需要在独立 session 执行（含审查检查点）（不用于：session 内 subagent 执行用 subagent-driven-development，写计划用 spec-driven-development）
  RULE: no specific rule（方法论 skill · 计划执行方法论）
  DETAIL: 本 SKILL.md（计划执行 + 审查检查点）
---

# Executing Plans（计划执行）

## 概述

加载计划，批判性审查，执行全部任务，完成后汇报。

**开始时声明：** "我正在使用 executing-plans 技能执行此计划。"

**Note：** 告知你的 human partner：本引擎在有 subagent 支持的平台上（如 Claude Code、Codex、ZCode）工作质量显著更高。若 subagent 可用，改用 superpowers:subagent-driven-development 而非本技能。

## 流程

### Step 1: 加载并审查计划
1. 读取计划文件
2. 批判性审查——识别任何疑问或顾虑
3. 有顾虑：开始前向 human partner 提出
4. 无顾虑：创建 TodoWrite 并继续

### Step 2: 执行任务

每个任务：
1. 标记为 in_progress
2. 严格按步骤执行（计划已拆为小步）
3. 按计划运行验证
4. 标记为 completed

### Step 3: 完成开发

全部任务完成并验证后：
- 声明："我正在使用 finishing-a-development-branch 技能收尾本次开发。"
- **REQUIRED SUB-SKILL:** 使用 superpowers:finishing-a-development-branch
- 按该技能验证测试、给出选项、执行所选

## 冲突分级：停下 vs 记录后继续（2026-09-20 引入 · 源自 superpowers v6.3.0）

> 并非所有冲突都值得停下问人。superpowers v6.3.0 曾记录：agent 因非灾难性计划冲突反复停下等待，累计阻塞 9 小时。分级处理：

**立即停下（破坏性 / 不可逆 / 关键缺口）：**
- 冲突会导致破坏性或不可逆后果（删数据、force-push、schema 不可回滚）
- 计划存在关键缺口，无法开始或继续（缺依赖、指令不可理解）
- 验证反复失败，修复尝试 ≥ 3 次仍不过

**记录后继续（非灾难性冲突，仅限执行细节级）：**
- 适用：命名不一致、步骤顺序可调整、文档与代码轻微不符、任务间接口描述过时
- **不适用**：涉及方案选择 / 范围变更 / 取舍（trade-off）的冲突——这些是用户决策点，仍走红线 3（AskUserQuestion），不得自裁
- 处理：在执行记录中写下「冲突内容 + 你的裁决 + 理由」→ **继续执行** → 完成报告中列出全部裁决供人工复核
- 禁止：因非灾难性冲突停下发问（"Should I continue?" 类提问浪费执行窗口）

**宁可问清也不要瞎猜** —— 但先问自己：这真是灾难性的吗？不是就裁决并继续。

## 执行期韧性（2026-09-20 引入）

**微任务批处理：** 计划含多个同形微任务（同模式、各改一处，如 11 个文件加同一条 exclusion 子句）时，合并为一批执行，不逐个走全流程。批完成后必须验证：批内**每一个**文件都确实出现在改动中（漏一个是批处理的经典失败模式）。异形任务（模式不同 / 有依赖）不合并。

**证据重读优先：** 验证或审查发现"证据不可读 / 对不上"时，先重读证据本身（重跑那一条命令、重看那一个 diff），不要直接重跑整个测试套件 —— 全套件重跑慢，且常掩盖真实问题（单测污染、桩泄漏会在全量重跑中变形）。仍不可读再升级。

## 何时回到早期步骤

**以下情况回到 Step 1 审查：**
- partner 根据你的反馈更新了计划
- 根本思路需要重想

**不要硬闯阻塞** —— 该停就停（按上方冲突分级判断）。

## Remember（要点）
- 先批判性审查计划
- 严格按计划步骤执行
- 不跳过验证
- 计划要求时引用对应技能
- 冲突分级：灾难性 → 停下问人；非灾难性 → 记录裁决继续
- 未经用户明确同意不得在 main/master 分支上开始实现

## Integration（衔接）

**必需工作流技能：**
- **superpowers:using-git-worktrees** —— 确保隔离工作区（创建或验证）
- **spec-driven-development** —— 产出本技能执行的计划
- **superpowers:finishing-a-development-branch** —— 全部任务后收尾开发

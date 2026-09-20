---
name: grilling
description: |
  TRIGGER: 对已存在的方案 / 计划 / 设计 / spec 做穷尽式压力测试（触发词：grill / 拷问 / 审讯 / 压力测试 / 挑战这个方案 / 逐条追问）（不用于：从零生成新设计用 brainstorming，术语/词汇表/ADR 维护用 domain-modeling，PRD/用户故事等文档工件用 product-manager，通用文档写作用 writing-skills）
  RULE: no specific rule（方法论 skill · 需求对抗审讯方法论）
  DETAIL: 本 SKILL.md（frontier 决策树审讯协议）
---

# Grilling — 对已有方案的穷尽式审讯

把「双方以为达成共识」变成「逐分支验证过的共识」，消灭静默假设。这是"需求不清 → 实现不完整 / 冲突 / BUG"的结构性防线：brainstorming 生成 spec，本技能对 spec 做对抗性审讯。

## 审讯协议：frontier 决策树

把方案映射为一棵**决策树**：每个决策分叉出依赖它的子决策。按**轮次**工作，**frontier** = 所有前置条件已定、现在就能问的问题集合。

1. 每轮把整个 frontier 通过 **AskUserQuestion** 提出：单次调用 ≤ 4 个 question（工具上限，多于 4 个拆多次调用）；每个 question 2-4 个选项，推荐项放第一个并在描述中说明理由——遵循红线 3 / C2，禁止 markdown 文字列选项
2. 用户回答后**重算 frontier**：已定的决策把边界向外推、解锁依赖它们的问题；一个问题的答案依赖本轮仍未决的另一个问题，则它属于**下一轮**
3. **终止条件**：frontier 为空——决策树每条分支都被访问过，没有静默假设。此时向用户确认已达共识；用户确认前不得实施任何动作

## 事实与决策的分工（红线 7 对齐）

- **事实是你的职责，永远不是用户的**：frontier 问题需要环境事实（文件系统 / 代码 / 工具）时，派 sub-agent 去查（按红线 7 传 5 类输入：scope / goal / constraints / format / context）。探索不阻塞其余提问：只有该事实下游的问题等待 sub-agent 报告，frontier 其余问题照常问
- **决策是用户的**：每个决策通过 AskUserQuestion 交给用户，不代答

## 与需求澄清链的关系

- **上游**：brainstorming 产出 spec 后，高风险 / 领域密集 / 多方冲突 spec 触发本技能对抗审讯
- **下游**：审讯发现的修订写回原 spec 文件，由原流程（brainstorming 自查 → 用户审阅门）承载；本技能自身**不产出 spec**
- 术语歧义密集场景与 **domain-modeling** 组合使用：审讯过程同步沉淀 CONTEXT.md 词汇表与 ADR

## 边界

| 场景 | 去处 |
|---|---|
| 从零生成设计（还不确定要什么） | brainstorming |
| PRD / 优先级 / 用户故事文档 | product-manager |
| 术语冲突 / 词汇表 / ADR 单独维护 | domain-modeling |
| 通用文档写作 | writing-skills |

## 审讯示例（1 轮 frontier 提问）

方案「用户注销功能」的首轮 frontier（顶层未决决策，3 个问题一次 AskUserQuestion 提出）：

1. "注销后数据保留多久？" — 30 天可恢复 (推荐，误注销可自救) / 立即硬删 / 仅日志保留
2. "注销入口放在哪？" — 设置-账户页 (推荐，路径最短) / 独立页面 / 客服人工
3. "进行中的订阅如何处理？" — 按比例自动退款 (推荐，合规风险最低) / 到期不续 / 阻止注销直到取消

用户选 1=30 天可恢复 → 解锁下一轮问题 **"30 天内恢复的入口给谁？"**（自助 / 客服验证身份）——该问题依赖 Q1 的答案，首轮不可问（不属于当时的 frontier）。两轮后 frontier 为空 = 决策树走完，静默假设清零。

---

## 论源（工程实践红线对接 · AGENTS.md §9）

- **R1.1 反选项清单** — 每轮提问强制"每题 2-4 个选项 + 推荐项 + 理由"，审讯即反选项的对话化
- **红线 3 / C2** — 决策类提问的 AskUserQuestion 强制约束在本技能内落实为轮次格式
- **红线 7 / V3** — 事实查证 sub-agent 的 5 类必接输入与独立验证义务

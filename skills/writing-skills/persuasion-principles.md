# 技能设计中的说服原则

## Overview（概述）

LLM 对说服原则的反应与人类相同。理解这套心理学帮你设计更有效的技能——不是为了操纵，而是确保关键实践在压力下仍被遵循。

**研究基础：** Meincke et al. (2025) 以 N=28,000 次 AI 对话测试了 7 条说服原则。说服技术让遵守率翻倍以上（33% → 72%，p < .001）。

## 七条原则

### 1. 权威（Authority）
**是什么：** 对专业性、资质或官方来源的服从。

**在技能中如何起效：**
- 命令式语言："YOU MUST"、"Never"、"Always"
- 不可协商的框架："No exceptions"
- 消除决策疲劳与合理化

**何时用：**
- 纪律执行类技能（TDD、验证要求）
- 安全关键实践
- 成熟的最佳实践

**示例：**
```markdown
✅ Write code before test? Delete it. Start over. No exceptions.
❌ Consider writing tests first when feasible.
```

### 2. 承诺（Commitment）
**是什么：** 与先前行动、声明或公开宣告保持一致。

**在技能中如何起效：**
- 要求宣布："Announce skill usage"
- 强制显式选择："Choose A, B, or C"
- 用跟踪：TodoWrite 做清单

**何时用：**
- 确保技能真被遵循
- 多步流程
- 问责机制

**示例：**
```markdown
✅ When you find a skill, you MUST announce: "I'm using [Skill Name]"
❌ Consider letting your partner know which skill you're using.
```

### 3. 稀缺（Scarcity）
**是什么：** 来自时限或限量供应的紧迫感。

**在技能中如何起效：**
- 时限要求："Before proceeding"
- 顺序依赖："Immediately after X"
- 防拖延

**何时用：**
- 即时验证要求
- 时间敏感工作流
- 防"稍后再做"

**示例：**
```markdown
✅ After completing a task, IMMEDIATELY request code review before proceeding.
❌ You can review code when convenient.
```

### 4. 社会认同（Social Proof）
**是什么：** 从众于他人所为或所谓常态。

**在技能中如何起效：**
- 普遍模式："Every time"、"Always"
- 失败模式："X without Y = failure"
- 建立规范

**何时用：**
- 记录普遍实践
- 警示常见失败
- 强化标准

**示例：**
```markdown
✅ Checklists without TodoWrite tracking = steps get skipped. Every time.
❌ Some people find TodoWrite helpful for checklists.
```

### 5. 归属（Unity）
**是什么：** 共享身份、"我们感"、圈内归属。

**在技能中如何起效：**
- 协作语言："our codebase"、"we're colleagues"
- 共同目标："we both want quality"

**何时用：**
- 协作式工作流
- 建立团队文化
- 非等级实践

**示例：**
```markdown
✅ We're colleagues working together. I need your honest technical judgment.
❌ You should probably tell me if I'm wrong.
```

### 6. 互惠（Reciprocity）
**是什么：** 回报所受恩惠的义务感。

**如何起效：**
- 少用——会有操纵感
- 技能里很少需要

**何时避免：**
- 几乎总是（其他原则更有效）

### 7. 喜好（Liking）
**是什么：** 偏好与自己喜欢的人合作。

**如何起效：**
- **不用于合规目的**
- 与坦诚反馈文化冲突
- 制造谄媚

**何时避免：**
- 纪律执行场景永远避免

## 按技能类型组合原则

| 技能类型 | 用 | 避免 |
|------------|-----|-------|
| 纪律执行 | 权威 + 承诺 + 社会认同 | 喜好、互惠 |
| 指引/技术 | 适度权威 + 归属 | 重度权威 |
| 协作 | 归属 + 承诺 | 权威、喜好 |
| 参考 | 仅清晰 | 全部说服手段 |

## 为什么有效：心理学机制

**明亮线规则减少合理化：**
- "YOU MUST" 消除决策疲劳
- 绝对语言消灭"这算例外吗？"之问
- 显式反合理化封堵具体漏洞

**执行意图创造自动行为：**
- 清晰触发 + 必需动作 = 自动执行
- "When X, do Y" 比 "generally do Y" 有效
- 降低合规的认知负载

**LLM 是类人的（parahuman）：**
- 训练语料含这些人类模式
- 训练数据中权威语言先于遵从出现
- 承诺序列（声明 → 行动）被频繁建模
- 社会认同模式（大家都做 X）建立规范

## 伦理使用

**正当：**
- 确保关键实践被遵循
- 创造有效文档
- 预防可预见的失败

**不正当：**
- 为私利操纵
- 制造虚假紧迫
- 基于内疚的合规

**检验标准：** 若用户完全理解这个技术，它仍服务于用户的真实利益吗？

## 研究引用

**Cialdini, R. B. (2021).** *Influence: The Psychology of Persuasion (New and Expanded).* Harper Business.
- 说服七原则
- 影响力研究的实证基础

**Meincke, L., Shapiro, D., Duckworth, A. L., Mollick, E., Mollick, L., & Cialdini, R. (2025).** Call Me A Jerk: Persuading AI to Comply with Objectionable Requests. University of Pennsylvania.
- 以 N=28,000 次 LLM 对话测试 7 原则
- 遵守率经说服技术从 33% 提升到 72%
- 权威、承诺、稀缺最有效
- 验证 LLM 行为的类人模型

## Quick Reference

设计技能时自问：

1. **这是什么类型？**（纪律 vs 指引 vs 参考）
2. **我想改变什么行为？**
3. **哪些原则适用？**（纪律类通常是权威 + 承诺）
4. **组合是否过多？**（不要七条全上）
5. **伦理吗？**（服务于用户真实利益？）

---
name: domain-modeling
description: |
  TRIGGER: 领域术语歧义 / 维护 CONTEXT.md / 记录 ADR / 领域模型讨论 / 与 grilling 组合做"审讯+沉淀"（触发词：CONTEXT.md / 词汇表 / 术语表 / glossary / ADR / 领域模型）（不用于：通用文档写作用 writing-skills，从零生成设计用 brainstorming，纯方案审讯用 grilling）
  RULE: no specific rule（方法论 skill · 领域建模与术语执法方法论）
  DETAIL: 本 SKILL.md + CONTEXT-FORMAT.md + ADR-FORMAT.md
---

# Domain Modeling — 领域建模与术语执法

设计过程中**主动**构建和锐化项目的领域模型：挑战术语、发明边界场景、在共识结晶的瞬间写下词汇表和决策。（只"读" CONTEXT.md 学词汇不算本技能——那是任何技能都能做的一行习惯。本技能用于**改变模型**时，而非消费模型。）

## 文件结构

多数仓库只有一个 context：

```
/
├── CONTEXT.md
├── docs/superpowers/adr/          ← 本项目 ADR 路径（R6.2 约定，覆盖上游默认 docs/adr/）
│   ├── 2026-07-01-event-sourced-orders.md
│   └── 2026-07-02-postgres-for-write-model.md
└── src/
```

若根目录存在 `CONTEXT-MAP.md`，则仓库有多个 context，map 指向各处：

```
/
├── CONTEXT-MAP.md
├── docs/superpowers/adr/             ← 系统级决策
├── src/
│   ├── ordering/
│   │   └── CONTEXT.md
│   └── billing/
│       └── CONTEXT.md
```

**懒创建**：有东西可写时才建文件。首个术语敲定时创建 CONTEXT.md；首个 ADR 需要时创建 ADR 目录。

## 会话中的执法动作

### 对照词汇表挑战

用户用词与 CONTEXT.md 现有语言冲突时，当场叫停："你的词汇表定义『取消』是 X，你现在指的是 Y，到底是哪个？"

### 锐化模糊语言

用户用词含糊或一词多义时，提出精确的规范术语："你说『账户』——指 Customer 还是 User？这是两个东西。"

### 用具体场景压力测试

讨论领域关系时，发明探测边界情况的具体场景，迫使用户对概念间的边界给出精确定义。

### 与代码交叉验证

用户陈述"系统如何工作"时，核对代码是否同意。发现矛盾当场摆出："代码是整单取消，你刚说支持部分取消，哪个对？"

### 即时更新 CONTEXT.md

术语敲定时立刻写入 CONTEXT.md，不攒批。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。

CONTEXT.md **完全不含实现细节**：不是 spec、不是草稿纸、不是实现决策仓库。它只是词汇表。

### ADR 节制提供

只在三条**全部**满足时才提议写 ADR：

1. **难以逆转**：日后改主意的代价是有意义的
2. **无上下文会费解**：未来读者会问"为什么当初这么做？"
3. **真实权衡的结果**：确有备选项，且因具体理由选了这个

任一条不满足就不写。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。ADR 存放路径遵循本项目 R6.2 红线：`docs/superpowers/adr/YYYY-MM-DD-<topic>.md`（覆盖上游默认 `docs/adr/`）。

## 与 grilling 的组合（审讯 + 沉淀）

grilling 审讯已有方案时，术语冲突执法、断言↔代码交叉验证、词汇表/ADR 沉淀由本技能并行承担——审讯发现的概念分歧当场落为 CONTEXT.md 条目，关键取舍落为 ADR。

---

## 论源（工程实践红线对接 · AGENTS.md §9）

- **R6.2 ADR 红线** — 本技能提供"ADR 三条件准入 + 格式"的方法论落地；路径约定以 R6.2 为单点真源
- **R3.1 根因分析** — "断言↔代码交叉验证"是用事实反驳错误假设的机制化，防止症状级共识
- **红线 3 / C2** — 术语冲突叫停、二选一敲定均通过 AskUserQuestion 承载

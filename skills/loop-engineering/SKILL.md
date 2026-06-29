---
name: loop-engineering
description: "循环工程超级技能 —— /loop 闭环编码命令 + loop-library 循环设计模式二合一。涵盖闭环开发、门禁矩阵、自愈分级、自定义循环模式。"
metadata:
  version: "2.0"
  type: skill
  sources:
    - self (loop)
    - superpowers (loop-library)
  merged_from:
    - loop
    - loop-library
  merge_date: "2026-06-29"
  merge_reason: "2 个循环工程技能（闭环执行 + 循环设计）整合为单一入口"
---

# Loop Engineering 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

整合 2 个循环工程技能：
- **loop**（self）—— /loop 闭环编码命令（v4.1）
- **loop-library**（superpowers）—— 循环设计模式库

## 触发关键词（合并后）

/loop、loop:、循环工程、闭环开发、循环设计、自定义循环、反馈循环、经验库

## 使用方式

| 任务 | 读哪一章 |
|------|---------|
| 执行循环工程 | /loop 命令 |
| 设计循环模式 | loop-library 模式库 |
| 自定义循环 | 循环设计 + 闭环执行 |
| 集成 go 编排 | --auto 模式 |

## /loop 命令（loop · self · v4.1）

### 命令格式

```
/loop [--auto|--lite|--standard|--full] 功能描述，验收条件1，验收条件2，...
/loop --auto 功能描述                  # 纯自动模式（go 调用目标）
/loop --lite 修复分页Bug               # 强制轻量
/loop --full 重构用户模块               # 强制完整
```

### 模式分发

```
--auto → 🤖 纯自动模式
  全程审计闸门 · 不等用户确认 · 门禁全绿自动合并
  go 调用 loop 时固定走此模式

默认 → 🟢🟡🔴 自适应
  复杂度评估 → 按级别裁剪全流程
```

### 核心原则

1. **断点续跑**：状态文件持久化
2. **门禁矩阵不可跳过**：G0-G9, F1-F5, G10
3. **不降级红线**：禁止静默删减功能
4. **Git 隔离**：遵循 using-git-worktrees
5. **验证证据标准化**：可复现、有数据、有对比
6. **G9 代码审查**：commit 前必过
7. **🆕 v6.1 桥接模式**：`LOOPENGINE_BRIDGES=alpha` 启用 subagent-dd G9/G10 增强
8. **G10 系统审查**：go 中执行，loop 不重复触发
9. **MCP 红线**：理解代码必须先用 MCP 工具

### 门禁矩阵

- **G0**：环境预检
- **G1-G5**：功能性验证
- **G6-G8**：质量验证
- **G9**：代码审查（commit 前）
- **G10**：系统审查（特性分支交付前）
- **F1-F5**：前端验证

> 完整 loop 命令规范：`references/loop-full.md`（即将从 loop 迁移）

## 循环设计模式（loop-library · superpowers · 208 行）

### 循环的本质

**反馈循环** = 任何重复执行 + 从结果学习的流程

### 核心循环模式

1. **生成-测试-修复循环**：代码生成 → 自动化测试 → 自愈修复
2. **观察-假设-验证循环**：从数据 → 假设 → 实验
3. **计划-执行-反思循环**：PDCA + 总结
4. **抽取-转换-加载循环**（ETL）
5. **编译-测试-部署循环**（CI/CD）

### 设计循环的关键

- **明确目标**：每个循环应有清晰的成功标准
- **快速反馈**：循环周期应短（分钟级而非天）
- **可观察性**：每个循环节点都应可监控
- **可中断性**：循环应支持断点续跑
- **可重入**：失败后能从失败点恢复

> 完整 208 行内容：[references/loop-library-full.md](references/loop-library-full.md)

## 整合使用流程

```
执行循环工程
├─ 步骤 1: 设计循环（loop-library）
├─ 步骤 2: 配置 /loop 命令
├─ 步骤 3: 门禁检查
├─ 步骤 4: 自动修复
└─ 步骤 5: 验证交付

设计新循环
├─ 步骤 1: 识别反馈点
├─ 步骤 2: 设计循环结构
├─ 步骤 3: 定义成功标准
├─ 步骤 4: 实现循环命令
└─ 步骤 5: 验证循环
```

## Resources

- `references/loop-full.md`（即将从 loop 迁移完整内容）—— 完整 /loop 命令规范
- `references/loop-library-full.md`（来自 loop-library）—— 完整 208 行
- `references/mode-auto.md`（来自 loop）—— 纯自动模式
- `references/mode-default.md`（来自 loop）—— 自适应模式

## 限制

- 循环不是银弹：需明确反馈点
- G9/G10 桥接 alpha 阶段：仅 opt-in
- 完整内容在 references/，按需查阅

---

## 迁移说明

- v6.2 合并前：loop + loop-library 两个独立技能
- v6.2 合并后：loop-engineering 一个超级技能
- /loop 命令规范保留完整（来自 loop v4.1）
- 循环设计模式保留完整（来自 loop-library）
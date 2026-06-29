---
name: clean-code
description: "代码质量超级技能 —— 日常编码 + McConnell 全过程 + 自家工程规范三合一。涵盖 Clean Code（Martin）+ Code Complete（McConnell）+ 自家代码质量原则。"
metadata:
  version: "2.0"
  type: skill
  sources:
    - ciembor/agent-rules-books (2 books)
    - self (1 code-quality-principles)
  books:
    - Clean Code by Robert C. Martin
    - Code Complete by Steve McConnell
  merged_from:
    - clean-code
    - code-complete
    - code-quality-principles
    - pragmatic-programmer
  merge_date_v2: "2026-06-29"
  merge_date_v2_1: "2026-06-29"
  merge_reason: "v6.1.1 合并 code-complete + code-quality-principles；v6.2 扩展 pragmatic-programmer"
---

# Clean Code 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

当进行日常编码实现、代码审查、重构，或需要软件构造全过程指导，或需要代码级工程规范（异常/契约/commit/测试金字塔）时使用此技能。

## 使用方式

加载此技能后，**必须**根据需要读取对应规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\clean-code\clean-code.mini.md           # Martin 日常编码
C:\Users\admin\.agents\skills\agent-rules-books\code-complete\code-complete.mini.md     # McConnell 全过程
```

code-quality-principles（self 源）的内容已直接写入本 SKILL.md（见下方"代码质量原则"章节）。

## 来源与定位

| 部分 | 来源 | 用途 |
|------|------|------|
| **clean-code**（Martin 日常编码） | Robert C. Martin《Clean Code》 | 可读性、局部推理、可维护代码形态 |
| **code-complete**（McConnell 全过程） | Steve McConnell《Code Complete》 | 软件构造全过程（需求→设计→编码→调试→测试） |
| **code-quality-principles**（self 规范） | self | 异常三分、契约测试、commit 规范、测试金字塔、防御式编程 |

## 触发关键词（合并后）

干净代码、可读性、命名、函数拆分、代码规范、代码原则、异常处理、commit规范、防御式编程、软件构造、全套流程、代码审查、复杂度、深模块、抽象、信息隐藏、DRY、正交

## 规则概览

### 风格说明（前置）

| 源 | 风格 | 适用场景 |
|---|------|---------|
| **clean-code**（Martin 日常编码） | 原则式 | 设计哲学 / 微观代码形态 |
| **code-complete**（McConnell 全过程） | 要点式 | 全过程速查 / 教科书式 |
| **code-quality-principles**（self 规范） | 表格式 | 工程规范 / 检查清单 |

> 三种风格互补：原则告诉你"为什么"，要点告诉你"是什么"，清单告诉你"做什么"。

### 来自 clean-code（Martin 日常编码）

- 将整洁视为交付的一部分
- 为局部推理而写代码
- 使用精确命名，一个概念一个词
- 函数保持短小、专注、单一抽象层级
- 参数少而有意义；避免布尔标志和输出参数
- 命令与查询分离，消除隐藏副作用
- 清晰路径可读；隔离错误处理
- 暴露行为而非原始表示
- 将构造、框架、持久化等细节排除在业务行为之外
- 公共 API 小而显式，难以误用
- 注释仅用于理由、约束、警告或外部契约
- 测试作为生产代码对待

### 来自 code-complete（McConnell 全过程）

- 为变化而设计，为理解而编码
- 管理复杂度是软件开发的核心
- 选用合适的数据结构和算法
- 高质量的子程序：内聚、命名清晰、参数合理
- 防御式编程：检查输入、断言前置条件
- 变量命名反映用途和作用域
- 控制流的结构和可读性
- 代码调优要在测量后针对热点

### 来自 code-quality-principles（self · 已内联）

**异常三分**

| 类型 | 特征 | 处理 |
|------|------|------|
| **可恢复** | 重试可能成功（网络超时） | 重试+退避，warning |
| **不可恢复** | 重试无意义（参数错误） | 快速失败，error |
| **需人工** | 需运维介入（资源耗尽） | 报警+降级，critical |

**契约测试**
- API 响应字段白名单检查
- 函数签名兼容性检查
- DB schema diff 检查

**Commit 规范**
- 原子：一个 commit 只做一件事
- 语义化：`feat:` / `fix:` / `refactor:` / `test:` / `docs:`
- diff < 200 行

**防御式编程**
- 输入在边界处校验
- 空/零/null/超大值 四类边界必有测试
- 外部依赖不可用时优雅降级

**测试金字塔**
```
    ╱ E2E ╲      ~10%
   ╱ 集成 ╲     ~20%
  ╱  单测   ╲  ~70%
```
- 单测覆盖：正常 + 边界 + 异常
- 集成测试：真实依赖，不 mock DB
- E2E：只测核心流程

### 来自 pragmatic-programmer（v6.2 扩展）

工程实践与决策原则：
- **DRY**：Don't Repeat Yourself（知识单一来源）
- **正交**：组件之间互不依赖
- **可逆性**：决策保留回退余地
- **曳光弹**：用最小可行产品快速验证
- **估算**：先做粗略估算，再细化
- **原型**：用原型学习，不靠猜测
- **领域语言**：用业务术语命名

> 完整 34 行内容：[references/pragmatic-programmer-full.md](references/pragmatic-programmer-full.md)

## v6.2 扩展整合

```
clean-code 超级技能 = Martin + McConnell + self 规范 + pragmatic-programmer
├─ 何时用 Martin：日常编码/可读性
├─ 何时用 McConnell：软件构造全过程
├─ 何时用 self：异常/commit 规范
└─ 何时用 pragmatic-programmer：工程决策/估算
```

## 选择哪个源？

| 场景 | 推荐源 |
|------|--------|
| **日常编码 / 代码可读性 / 局部推理** | clean-code（Martin） |
| **软件构造全过程指导** | code-complete（McConnell） |
| **代码级工程规范 / 异常 / commit** | code-quality-principles（self） |

---

## 迁移说明

- v6.1.1 合并前：clean-code + code-complete + code-quality-principles 三个独立技能
- v6.1.1 合并后：clean-code 一个超级技能（含 2 个 ciembor 规则文件引用 + self 工程规范内联）
- skill-hub 调度表已同步：code-complete / code-quality-principles 行已移除
- 黄金轨迹：v54-baseline 中"code-complete"等关键词已映射到 clean-code
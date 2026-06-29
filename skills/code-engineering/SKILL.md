---
name: code-engineering
description: "软件工程超级技能 —— 软件设计哲学（Ousterhout）+ Python 异步模式二合一。涵盖复杂度管理、深模块、信息隐藏、asyncio、协程。"
metadata:
  version: "2.0"
  type: skill
  sources:
    - ciembor/agent-rules-books (philosophy-of-software-design)
    - community (async-python-patterns)
  merged_from:
    - philosophy-of-software-design
    - async-python-patterns
  merge_date: "2026-06-29"
  merge_reason: "2 个软件工程技能（设计哲学 + Python 异步）整合为单一入口"
---

# Code Engineering 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

整合 2 个软件工程技能：
- **philosophy-of-software-design**（ciembor）—— Ousterhout《A Philosophy of Software Design》
- **async-python-patterns**（community）—— Python asyncio 异步编程

## 触发关键词（合并后）

复杂度、深模块、抽象、信息隐藏、异步、asyncio、协程、并发、aiohttp、FastAPI

## 使用方式

| 任务 | 读哪一章 |
|------|---------|
| 设计复杂系统 | 软件设计哲学 |
| 降低模块复杂度 | 深模块 + 信息隐藏 |
| Python 异步开发 | asyncio 模式 |
| 并发性能优化 | 协程 + 异步 I/O |

## 软件设计哲学（philosophy-of-software-design · ciembor · 32 行）

### 核心原则

- **复杂度是渐增的**：每次设计决策都可能增加复杂度
- **深模块 > 浅模块**：少量复杂接口 > 大量简单接口
- **信息隐藏**：模块不暴露实现细节
- **分层抽象**：每层只关注自己职责
- **小接口、大实现**：减少调用方负担

### 复杂度来源

- **依赖**：模块间不必要的耦合
- **晦涩**：代码意图不清晰
- **重复**：相同逻辑多处出现
- **复杂性累积**：每个小决策叠加

### 设计策略

- **正交性**：模块互不依赖
- **深模块**：用小接口封装复杂实现
- **信息隐藏**：不暴露不必要的信息
- **战术编程 vs 战略编程**：平衡短期与长期

> 完整 32 行内容：[references/philosophy-of-software-design-full.md](references/philosophy-of-software-design-full.md)

## Python 异步编程（async-python-patterns · community · 47 行）

### 适用场景

- 异步 Web API（FastAPI、aiohttp、Sanic）
- 并发 I/O 操作（数据库、文件、网络）
- Web 爬虫并发请求
- 实时应用（WebSocket、聊天系统）
- 处理多个独立任务并行
- 构建微服务异步通信
- 优化 I/O 密集型工作负载
- 实现异步后台任务和队列

### 核心模式

- **async/await**：协程语法
- **asyncio.gather**：并发执行多个协程
- **asyncio.Queue**：异步队列
- **asyncio.Semaphore**：并发限制
- **aiohttp.ClientSession**：异步 HTTP 客户端
- **asyncpg**：异步 PostgreSQL
- **aiomcache**：异步缓存

### 注意事项

- **不要在 async 中阻塞**：避免 time.sleep、requests
- **异常处理**：async 异常需小心
- **资源管理**：使用 async with
- **性能权衡**：异步不一定更快（CPU 密集型任务无收益）

> 完整 47 行内容：[references/async-python-full.md](references/async-python-full.md)

## 整合使用流程

```
设计新系统
├─ 步骤 1: 软件设计哲学（深模块 + 信息隐藏）
├─ 步骤 2: 接口设计（小接口、大实现）
├─ 步骤 3: 异步 vs 同步决策
├─ 步骤 4: 异步模式（如果选异步）
└─ 步骤 5: 性能测试

优化现有系统
├─ 步骤 1: 识别复杂度来源
├─ 步骤 2: 深模块重构
├─ 步骤 3: 异步 I/O 优化（I/O 密集场景）
└─ 步骤 4: 监控 + 度量
```

## Resources

- `references/philosophy-of-software-design-full.md`（来自 philosophy-of-software-design）—— 完整 32 行
- `references/async-python-full.md`（来自 async-python-patterns）—— 完整 47 行
- `resources/async-playbook.md`（来自 async-python-patterns）—— 实施手册

## 限制

- 异步不是银弹：CPU 密集型任务无收益
- 完整内容在 references/，按需查阅

---

## 迁移说明

- v6.2 合并前：philosophy-of-software-design + async-python-patterns 两个独立技能
- v6.2 合并后：code-engineering 一个超级技能
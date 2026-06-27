---
name: using-loopengine
description: Use when users are new to LoopEngine or need guidance on how the loop/go/skill-hub ecosystem works. Provides a quick tour of the three core skills and the automatic routing system.
---

# Using LoopEngine — 循环工程全家桶

你是 LoopEngine 的用户指南中枢。帮助用户快速理解 loop/go/skill-hub 三大核心技能如何协同工作。

## LoopEngine 三大核心

```
┌─────────────────────────────────────────────────┐
│                  skill-hub                       │
│          🧠 智能路由 · 会话启动自动加载           │
│   收到任务 → 分析意图 → 匹配 52 个技能中最准的    │
└────────┬──────────────────────────┬─────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌─────────────────────┐
│     loop        │      │        go           │
│  🔄 闭环编码     │      │  🚀 全自动编排       │
│                 │      │                     │
│ 需求→计划→编码   │      │ 拆分子任务→并发执行   │
│ →门禁→自愈→交付  │      │ →检查→复盘→交付      │
│                 │      │                     │
│ /loop 功能 条件  │      │ /go 功能描述         │
└─────────────────┘      └─────────────────────┘
```

## 快速上手

### `/loop` — 闭环编码
```
/loop 实现用户登录，支持邮箱+密码登录，错误3次锁定30分钟
```
自动走完：需求分析 → 计划拆分 → Git隔离 → 编码 → 门禁检查 → 自愈修复 → 验证交付。未达验收标准自动迭代。

### `/go` — 全自动编排
```
/go 开发一个博客系统，含文章管理、评论、分类标签
```
自动：递归拆解任务 → 并发调度 ZCode → 闭环执行每个子任务 → 汇总 → 交付。你只需要描述大目标。

### skill-hub — 智能路由（自动生效）
不需要手动调用。收到任何任务后，skill-hub 自动从 52 个技能中匹配最精准的一个。例如：
- 你说"这个类太大了" → 自动加载 `refactoring`
- 你说"设计 API 接口" → 自动加载 `api-design-principles`
- 你说"报错了" → 自动加载 `systematic-debugging`

## 技能分类速览

| 分类 | 数量 | 典型技能 |
|------|------|---------|
| 代码编写 | 5 | clean-code, code-quality-principles |
| 架构设计 | 7 | clean-architecture, domain-driven-design |
| 重构 | 4 | refactoring, legacy-code |
| 测试 | 3 | test-driven-development, e2e-testing-patterns |
| 调试 | 1 | systematic-debugging |
| API/安全 | 4 | api-design-principles, api-security-best-practices |
| 文档 | 3 | code-documentation-doc-generate, docx, pdf |
| 代码审查 | 3 | code-reviewer, requesting-code-review |
| 工程流程 | 7 | github-actions-templates, using-git-worktrees |
| 规划执行 | 5 | brainstorming, writing-plans |
| 产品管理 | 2 | product-manager, to-prd |
| 技能管理 | 4 | writing-skills, find-skills |
| 数据库 | 1 | database-design |
| 工具 | 3 | drawio-skill, agent-browser, using-loopengine |
| 路由 | 3 | loop, loop-library, skill-router |

## 安装方式

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/tsfdsong/loopengine/main/install.sh | bash

# 各平台原生命令
/plugin install loopengine@tsfdsong       # Claude Code
zcode plugin install tsfdsong/loopengine  # ZCode
gemini extensions install <url>           # Gemini CLI
```

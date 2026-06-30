---
name: using-loopengine
description: Use when users are new to LoopEngine or need guidance on how the loop/go/orch ecosystem works. Provides a quick tour of the three core skills and the multi-skill orchestration system.
---

# Using LoopEngine — 循环工程全家桶

你是 LoopEngine 的用户指南中枢。帮助用户快速理解 loop/go/orch 三大核心技能如何协同工作。

## LoopEngine 三大核心

```
┌─────────────────────────────────────────────────┐
│                     orch                        │
│         🧠 多技能编排器 · 显式 /orch 触发         │
│   单技能(80%)走原生 · 多技能(20%)走 5 类任务链     │
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

### `/orch` — 多技能编排（显式触发）
单技能任务（80%）由原生 description 匹配自动处理。多技能任务（20%）需显式 `/orch`：

| 你说 | 该用 |
|------|------|
| "对比 A 和 B 选型" | `/orch 1 ...`（调研+决策） |
| "帮我审查并改进" | `/orch 2 ...`（分析+建议） |
| "报错了帮我修" | `/orch 3 ...`（诊断+修复） |
| "设计并实现 X 功能" | `/orch 4 ...`（设计+实现） |
| "同时调研 A/B/C" | `/orch 5 ...`（并行调研） |

## 技能分类速览

| 分类 | 数量 | 典型技能 |
|------|------|---------|
| 代码质量 | 1 | clean-code（v6.4 4 维度） |
| 架构设计 | 2 | software-architecture, domain-driven-design |
| 重构 | 1 | refactoring（v6.4 4 源合一） |
| 测试 | 1 | testing（v6.4 3 源合一） |
| 调试 | 1 | systematic-debugging |
| 事实优先 | 1 | evidence-first |
| Python 后端 | 1 | python-web-development（v6.4 5 源合一） |
| 代码审查 | 1 | code-reviewer, system-review |
| 验证 | 1 | verification-before-completion |
| 工程流程 | 5 | github-actions-templates, production-readiness, using-git-worktrees |
| 规划执行 | 5 | brainstorming, writing-plans, executing-plans, subagent-driven-development, dispatching-parallel-agents |
| 产品管理 | 2 | product-manager, to-prd |
| 技能管理 | 3 | agent-skill-architecture, writing-skills, skill-creator |
| 数据库 | 1 | database-design |
| 工具 | 3 | drawio-skill, agent-browser, using-loopengine |
| 自研闭环 | 3 | loop, go, orch（v6.7 改名自 skill-hub，单职责化） |

## 安装方式

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/tsfdsong/loopengine/main/install.sh | bash

# 各平台原生命令
/plugin install loopengine@tsfdsong       # Claude Code
zcode plugin install tsfdsong/loopengine  # ZCode
gemini extensions install <url>           # Gemini CLI
```

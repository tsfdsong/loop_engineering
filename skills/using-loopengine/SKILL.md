---
name: using-loopengine
description: |
  TRIGGER: 用户初次接触 LoopEngine / 需要 loop/go/orch 生态指引 / 多 skill 编排系统导览
  RULE: no specific rule（方法论 skill · 入门导览）
  DETAIL: 本 SKILL.md（三大核心 skill + 编排系统导览）
---

# Using LoopEngine — 循环工程全家桶

你是 LoopEngine 的用户指南中枢。帮助用户快速理解 loop/go/orch 三大核心技能如何协同工作。

## LoopEngine 三大核心

```
┌─────────────────────────────────────────────────┐
│                     orch                        │
│   🧠 多技能编排器 · 自然语言优先 · /orch 可强制   │
│ 单技能走原生 · 多技能自动判定是否进入 orchestrator │
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

### `orch` — 多技能编排（自然语言优先）
单技能任务（80%）由原生 description 匹配自动处理。多技能目标由系统自动判断是否进入 orch；`/orch` 只用于显式强制编排：

| 你说 | 系统行为 |
|------|------|
| "对比 A 和 B 选型" | 自动识别 `research_compare` family |
| "帮我审查并改进" | 自动识别 `review` family |
| "报错了帮我修" | 自动识别 `debug_fix` family |
| "设计并实现 X 功能" | 自动识别 `design_build` family |
| "测试这个 web 应用" | 自动识别 `web_qa` family |

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

---
name: using-loopengine
description: |
  TRIGGER: 用户初次接触 LoopEngine / 需要 loop/go 生态指引 / 多 skill 编排系统导览
  RULE: no specific rule（方法论 skill · 入门导览）
  DETAIL: 本 SKILL.md（核心 skill + 编排系统导览）
---

# Using LoopEngine — 循环工程全家桶

你是 LoopEngine 的用户指南中枢。帮助用户快速理解 **loop / go / supervisor** 如何协同工作。

> **v2.0**：跨模块编排请用 `/go`（go Step 0 负责 family 识别 + DAG 组装）。  
> **薄 loop**：`/loop` = 编码↔门禁↔自愈↔交付；模糊需求走 brainstorming，多模块走 `/go`。

## LoopEngine 核心架构

```
┌───────────────────────────────────────────────────┐
│                      go                           │
│  🚀 全自动编排 · family-first · worktree 并发      │
│  （8 场景家族识别 + DAG 并行前沿）                   │
└──────────┬──────────────────────┬─────────────────┘
           │                      │
           ▼                      ▼
┌───────────────────┐   ┌──────────────────────────┐
│      loop         │   │      supervisor          │
│  🔄 薄闭环执行器   │   │   👁 并发子任务监控       │
│ 编码↔门禁↔自愈↔交付 │   │  R1-R4 干预链             │
└───────────────────┘   └──────────────────────────┘
```

**分层（上游 → 执行）**：

```text
brainstorming     未定型：探索 / 选型 / 设计草稿
       ↓（可选）
go                大活：项目分析 / DAG / 并行 / 汇合
       ↓ 任务包（goal + 验收已可执行）
loop              编码 ↔ 门禁 ↔ 自愈 ↔ 交付
```

## 职责表

| Skill | 做什么 | 不做什么 | 典型触发 |
|-------|--------|----------|----------|
| **brainstorming** | 未定型探索、选型、设计草稿 | 编码落地、门禁闭环、多模块编排 | 「要不要做 X」「A vs B」「先帮我想清楚」 |
| **spec-driven-development** | 产出书面实施计划 + **Verification/Termination/Escalation 契约** | 运行时 DAG/worktree 编排 | 「写实施计划」「spec → plan」 |
| **go** | family 路由、DAG 组装、worktree 并发、派发/汇合 | 替代单任务薄执行环；不做产品级 brainstorm | 「开发整站 / 多模块」「跨模块编排」`/go …` |
| **loop** | 已有可执行目标+验收 → 编码↔门禁↔自愈↔交付 | 需求分析、plan 级拆分、长确认流 | 「实现/修复 X，验收…」`/loop …` |
| **supervisor** | 多子任务并发监控、R1–R4 干预链 | 自己写码或替代 go 调度 | go 派发后看门狗 / 子任务卡住 |

**上游契约**：brainstorming spec 与 spec-driven-development plan 共享 `skills/shared/references/loop-execution-contract.md`（验收 + 终止 + 升级路径），供 `/goal` / `/loop` / `/go` 消费。

可选一句话：

- **product-manager** — PRD / 优先级 / 用户故事（产品规格，非执行环）。
- **executing-plans** — 在独立 session 按已有书面计划逐步执行（含审查检查点）。

### go ↔ spec-driven-development

**go** = 运行时 DAG / worktree 编排；**spec-driven-development** = 书面计划产物 + 执行契约 / 独立 session 规划——**二者互不替代**。

### 加速路径（非角色产品）

墙钟加速靠 **DAG 并行前沿**（可并行节点一次派齐）+ **机械脚本门禁**（测 / audit / smart_commit 等）。**不做** Subagent 角色注册表（不把 loop/CR 等品牌化为固定角色 ID）。

## 快速上手

### `/loop` — 薄闭环执行器

```
/loop 实现用户登录，支持邮箱+密码登录，错误3次锁定30分钟
```

已有可执行目标 + 验收 → **编码 ↔ 门禁/验证 ↔ 自愈 → 交付**。  
模糊/未定型需求 → 先 **brainstorming**；多模块/跨模块 → 用 **`/go`**（勿把 loop 当迷你编排器）。

### `/go` — 全自动编排（含 family 路由）

```
/go 开发一个博客系统，含文章管理、评论、分类标签
```

自动：意图识别（8 family）→ 项目上下文分析 → 拆分子任务 → DAG 并行前沿 + worktree → 回归 → 交付。

### `/git-commit` — 智能提交（防漏 untracked）

```
/git-commit -m "feat: ..."
# 或: python3 scripts/smart_commit.py -m "feat: ..." [--dry-run] [--push]
```

本地脚本按规则+启发式过滤后 `git add` + `commit`（不靠模型选文件）。详见 `docs/2026-07-21-smart-git-commit-design.md`。

### 自然语言 family 路由（v2.0 · 由 go 承担）

| 你说 | 系统行为 |
|------|---------|
| "对比 A 和 B 选型" | `research_compare` family |
| "帮我审查并改进" | `review` family |
| "报错了帮我修" | `debug_fix` family |
| "设计并实现 X 功能" | `design_build` family |
| "测试这个 web 应用" | `web_qa` family |

单技能任务（80%）由原生 description 匹配自动处理，无需 `/go`。

## 技能分类速览

| 分类 | 典型技能 |
|------|---------|
| 自研闭环 | `loop`, `go`, `supervisor` |
| 上游规划 | `brainstorming`, `writing-plans`, `product-manager`, `executing-plans` |
| 代码质量 | `clean-code`, `code-reviewer`, `refactoring` |
| 架构/审查 | `software-architecture`, `system-review`, `evidence-first` |
| 测试/调试 | `testing`, `systematic-debugging`, `web-quality` |
| 工程流程 | `using-git-worktrees`, `subagent-driven-development`, `verification-officer` |

> 完整列表见仓库 `skills/` 目录（**32** 个内置 SKILL.md）。

## 安装方式

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
```

详见 `docs/INSTALL.md`。

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

## LoopEngine 核心架构

```
┌───────────────────────────────────────────────────┐
│                      go                           │
│  🚀 全自动编排 · family-first · worktree 并发      │
│  （8 场景家族识别 + DAG 组装）                      │
└──────────┬──────────────────────┬─────────────────┘
           │                      │
           ▼                      ▼
┌───────────────────┐   ┌──────────────────────────┐
│      loop         │   │      supervisor          │
│   🔄 闭环编码      │   │   👁 并发子任务监控       │
│  单任务门禁+自愈   │   │  R1-R4 干预链             │
└───────────────────┘   └──────────────────────────┘
```

## 快速上手

### `/loop` — 闭环编码
```
/loop 实现用户登录，支持邮箱+密码登录，错误3次锁定30分钟
```
自动走完：需求分析 → 计划拆分 → Git 隔离 → 编码 → 门禁检查 → 自愈修复 → 验证交付。

### `/go` — 全自动编排（含 family 路由）
```
/go 开发一个博客系统，含文章管理、评论、分类标签
```
自动：意图识别（8 family）→ 深度需求分析 → 拆分子任务 → worktree 并发 → 回归 → 交付。

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

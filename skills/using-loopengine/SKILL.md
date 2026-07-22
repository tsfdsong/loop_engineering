---
name: using-loopengine
description: |
  TRIGGER: 用户初次接触 LoopEngine / 需要 loop/go 生态指引 / 多 skill 编排系统导览
  RULE: no specific rule（方法论 skill · 入门导览）
  DETAIL: 本 SKILL.md（核心 skill + 编排系统导览）
---

# Using LoopEngine — 怎么选技能

帮用户分清 **loop / go / supervisor** 和上游规划技能，别把执行器当聊天室。

```
brainstorming     未定型：探索 / 选型 / 设计
       ↓
/go               大活：分析 / DAG / 并行 / 汇合
       ↓ 任务包（goal + 验收）
/loop             单任务：编码 ↔ 门禁 ↔ 自愈 ↔ 交付
```

## 职责表

| Skill | 做什么 | 不做什么 | 典型说法 |
|-------|--------|----------|----------|
| **brainstorming** | 探索、选型、设计草稿 | 编码、门禁、多模块编排 | 「要不要做 X」「A vs B」 |
| **spec-driven-development** | 写实施计划 + 验收/终止契约 | 运行时 DAG / worktree | 「写实施计划」 |
| **go** | family 路由、拆任务、并行、汇合 | 替代单任务薄执行 | `/go 做整站/多模块` |
| **loop** | 目标+验收齐全 → 编码闭环 | 需求分析、长确认流 | `/loop 实现 X，验收…` |
| **supervisor** | 盯多子任务、R1–R4 干预 | 自己写码、替代 go 调度 | go 派发后卡住 |

上游契约（验收 / 终止 / 升级）：`skills/shared/references/loop-execution-contract.md`。

补充：
- **product-manager** — PRD / 优先级（不做执行环）
- **executing-plans** — 按已有书面计划逐步执行

**go** 管运行时编排；**spec-driven-development** 管书面计划 —— 互不替代。

## 快速上手

```
/loop 实现登录，邮箱密码，错 3 次锁 30 分钟
/go 博客系统：文章、评论、标签
/git-commit -m "feat: ..."
```

| 你说 | 大致路由 |
|------|----------|
| 「对比 A 和 B」 | `research_compare` |
| 「审查并改进」 | `review` |
| 「报错了帮我修」 | `debug_fix` → 常落到 `loop` |
| 「设计并实现」 | `design_build` |
| 「测这个网站」 | `web_qa` |

单技能小活（约八成）靠 description 自动匹配，不必强行 `/go`。

## 技能速览

| 分类 | 例子 |
|------|------|
| 闭环 | `loop` · `go` · `supervisor` |
| 规划 | `brainstorming` · `spec-driven-development` · `product-manager` |
| 质量 | `clean-code` · `code-reviewer` · `refactoring` |
| 审查 | `system-review` · `evidence-first` |
| 测试 | `testing` · `systematic-debugging` · `web-quality` |
| 工程 | `using-git-worktrees` · `verification-officer` · `subagent-driven-development` |

完整列表：`skills/`（32 个）。

## 安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
```

详见 `docs/INSTALL.md`。智能提交：`docs/2026-07-21-smart-git-commit-design.md`。

---
description: 兼容别名 — 多技能编排已合并进 /go（family-first · v2.0）
allowed-tools: Skill, Read, Bash, TodoWrite, WebFetch, WebSearch
---

> **v2.0 变更**：`orch` 独立技能已删除，family 识别 + DAG 组装已合并进 **go Step 0**。
> 本命令保留为兼容入口，行为等同于加载 `go` 技能。

使用 `go` 技能进行多技能 / 跨模块编排。

加载 `skills/go/SKILL.md` 获取完整方法论；family 路由见 `skills/go/references/family-routing.md`。

## 触发词

`/orch`（兼容）、`/go`、多技能编排、2+ 技能组合、family 路由

## 不适用

- 单任务闭环（用 `/loop`）
- 纯只读调研（用 `deep-research` 或 `/go` 的 `research_compare` family）

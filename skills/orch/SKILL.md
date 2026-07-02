---
name: orch
description: Use when a task requires composing 2+ skills in sequence or parallel (multi-skill orchestration). Do NOT use for single-skill tasks (call that skill directly via native description matching). Do NOT use for skill discovery or routing (handled natively by LLM description matching).
metadata:
  version: "1.1.0"
  purpose: multi-skill orchestration only
  replaces: skill-hub (v6.7.0-alpha and earlier)
  related_executors: [go, loop, subagent-driven-development, dispatching-parallel-agents]
  added_in_v1_1_0: [type-6-web-test-orchestration, web-regression-e2e, web-visual-diff, web-audit-a11y, web-perf-budget]
---

# orch — 多技能编排器

## 职责（单一）

当一个任务需要 **2 个或以上技能** 按顺序/并行组合时，orch 决定：

- **调哪些技能**
- **按什么顺序**（串行链 / 并行分支）
- **如何把前序输出传给后序**

orch **不** 重新做技能发现（由原生 description 匹配接管），**不** 强制流程纪律（由 `AGENTS.md` 接管），**不** 重复执行能力（由 `go` / `loop` / `subagent-dd` 接管）。

## 不做什么

- ❌ 不维护关键词表 / 冲突裁决 / 复杂度评分
- ❌ 不强制 P0 流程（设计 / 调试 / 分析类）
- ❌ 不重复 MCP 红线（已在 `AGENTS.md`）
- ❌ 不执行单技能任务（让原生 description 匹配）
- ❌ 不替代 `go` / `loop` / `subagent-dd` 的执行能力

## 调用方式（仅显式）

```bash
/orch <type> <query>     # 显式指定复合任务类型（编号 1-5）
/orch <关键词> <query>    # 显式指定关键词（如 "调研+决策"）
/orch <query>             # 省略 type / 关键词，语义兜底
```

### 5 类复合任务（核心）

| type | 名称 | 技能链 | 适用场景 |
|:---:|------|--------|----------|
| **1** | 调研 + 决策 | `brainstorming` → `evidence-first` → `writing-plans` | "对比 A 和 B 选型"、"评估技术方案" |
| **2** | 分析 + 建议 | `system-review` → `brainstorming` | "审查这个项目并改进"、"评估架构" |
| **3** | 诊断 + 修复 | `systematic-debugging` → `refactoring` → `verification-before-completion` | "报错了帮我修"、"测试挂了" |
| **4** | 设计 + 实现 | `brainstorming` → `writing-plans` → `executing-plans` | "设计并实现 X 功能"、"从 0 到 1 做一个特性" |
| **5** | 并行调研 | `dispatching-parallel-agents`（或 `subagent-driven-development`） | "同时调研 A/B/C 三个库" |
| **6** | **Web 测试编排**（v1.1.0 新增） | `agent-browser/dogfood` + `web-regression-e2e` + `web-visual-diff` + `web-audit-a11y` + `web-perf-budget` | "测试这个 web 应用"、"audit 网站"、"web QA"、"前端回归测试" |

### 调用示例

```bash
/orch 1 对比 FastAPI 和 Django 哪个更适合本项目       # 调研 + 决策
/orch 调研+决策 对比 FastAPI 和 Django                # 同上，关键词也行
/orch 3 线上报 500 帮我定位并修复                     # 诊断 + 修复
/orch 4 设计并实现用户认证功能                         # 设计 + 实现
/orch 5 同时调研 fastapi / django / flask             # 并行调研
/orch 6 全面 audit https://my-app.com，重点测登录和上传       # Web 测试编排
/orch web-test 全面 audit https://my-app.com                   # 同上，关键词也行
/orch 帮我审查这个项目并给改进建议                     # 省略 type → 语义兜底
```

## 反例（不要用 orch）

| query | 该用 | 为什么 |
|---|---|---|
| "帮我重构这个函数" | `refactoring` | 单技能 |
| "为什么报 500" | `systematic-debugging` | 单技能 |
| "对比 A 和 B 选型" | `evidence-first` | 单技能（除非你明确想要 brainstorm + plan） |
| "审查这个 PR" | `code-reviewer` | 单技能 |

> **判断口诀**：任务**只**需要 1 个技能 → 不打 `/orch`；需要 **2+ 技能**且**有顺序依赖** → 打 `/orch`。

## 与 /go / /loop / subagent-dd 的关系（分层架构）

```
              用户 query
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
   单技能 (80%)          多技能 (20%)
       │                     │
       ▼                     ▼
   原生 description      用户显式 /orch
   自动匹配                │
                          ▼
                    ┌─────────────┐
                    │  orch       │  ← 本技能（规划层）
                    │  5 类任务链 │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌────────────┐
         │  go    │  │  loop  │  │ subagent-dd│
         │ DAG    │  │ 单任务 │  │ / dispatch │
         │ 执行   │  │ 闭环   │  │ -parallel  │
         └────────┘  └────────┘  └────────────┘
                  (执行层 · 已存在 · orch 不重复实现)

              ┌────────────┼────────────┐
              ▼            ▼            ▼            ▼            ▼
         web-regression-e2e web-visual-diff   web-audit-a11y  web-perf-budget
              (Playwright 回归)  (像素对比)      (axe-core WCAG)  (lighthouse)
                  (v1.1.0 新增 · Web 测试能力矩阵 · 4 sub-skill)
```

- **orch** = "调哪些技能 + 顺序"（**规划层**）
- **go / loop / subagent-dd** = "如何真正执行"（**执行层**）
- 5 类链中如需执行能力，orch **委托**给对应执行器，不重复实现

## 一键回滚

不使用 `/orch` = orch 不介入 = 100% 兼容原生单技能发现。

无需环境变量、无需配置。删除 `skills/orch/` 即可彻底移除。

## 升级 / 迁移说明

- v1.0.0 取代 `skill-hub` v6.7.0-alpha 及更早版本
- 移除内容：关键词表 / 冲突裁决 / P0 纪律 / MCP 红线 / 复杂度评分 / 性能基准
- 新增内容：无（仅保留 5 类复合任务链 + 分层架构说明）
- 兼容性：未使用 `/orch` 前缀的场景，行为 100% 等价于不加载本技能

## v1.1.0 升级（2026-07-02 · Web 测试编排）

**新增**：第 6 类任务链「Web 测试编排」
- 入口：在 `/orch 6` 或 `/orch web-test` 触发
- 子技能：4 个新增 `web-*` 技能（位于 `skills/web-*/`）
- 复用：仍可单独调用 4 个 sub-skill，绕过 orch
- 兼容：现有 5 类任务链（type 1-5）行为不变
- 同步：仅修改 `skills/`，用户跑 `install.sh` 同步到 `~/.agents/skills/`

**新增的 4 个 sub-skill**（详见各 SKILL.md）：
- `web-regression-e2e` — Playwright 回归 + CI 集成
- `web-visual-diff` — 像素对比视觉回归
- `web-audit-a11y` — axe-core WCAG 审计
- `web-perf-budget` — lighthouse Web Vitals 守门
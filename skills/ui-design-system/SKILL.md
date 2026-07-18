---
name: ui-design-system
description: |
  TRIGGER: 前端 UI 改动 / 重构组件 / 设计交互 / "前端反复纠正" / 创建 design token / 组件库 / 视觉规范
  RULE: V7 视觉上下文 — UI 改动前必须截图当前页面 + 改后对比验证
  DETAIL: 本 SKILL.md + references/{design-tokens,component-spec-template}.md + 与 agent-browser 配合
---

# ui-design-system — UI 设计系统 skill（v2.0 · 痛点 3 专治）

> 痛点：前端重构反复纠正（交互设计效果不佳）
> 根因：无视觉上下文契约（设计 token / 组件 spec）+ AI 看不见 UI
> 解法：设计 token 规范 + 组件 spec 模板 + UI 重构闭环（截图→改→对比→迭代）

## 核心方法论

### 1. 设计 token 规范（color/spacing/typography/shadow）
单一真源的设计变量 · 见 references/design-tokens.md

### 2. 组件 spec 模板（props / states / variants）
新组件必须先写 spec · 见 references/component-spec-template.md

### 3. UI 重构闭环（关键 · 痛点 3 直接解法）
- 改动前：截当前页面图（agent-browser snapshot）
- 改动：实施 UI 改动
- 改动后：截同一页面图
- 对比：用 web-quality/references/visual-diff.md 做 diff
- 验证：间距 / 响应式 / 视觉一致性

禁止纯靠 code review 判断 UI 效果（肉眼不可见的像素回归 / 布局偏移 / z-index 层级）。

## 与其他 skill 协作

- `agent-browser`：提供截图能力（baseline + after）
- `web-quality/references/visual-diff.md`：提供 diff 工具
- `brainstorming`：UI 重构的设计探索前置
- `spec-driven-development`：UI 改动需要 spec 时

## 决策树（何时用 ui-design-system）

| 触发 | 动作 |
|---|---|
| 创建新组件 | 先写 component spec → 实施 → 截图验证 |
| 重构现有组件样式 | 先截 baseline → 改 → 截 after → diff |
| 改设计 token | 改 token → 全组件回归截图 |
| 调响应式/暗色模式 | 多 viewport 截图对比 |

## 触发场景

- "改这个按钮的样式" / "重构卡片组件"
- "前端反复纠正"（用户痛点信号）
- "建立设计系统" / "design token"
- 涉及 CSS/Tailwind/styled-components/CSS Module 改动

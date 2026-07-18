---
name: web-quality
description: |
  TRIGGER: web 质量测试 / E2E 回归 / 视觉 diff / a11y 审计 / 性能预算 / Lighthouse / Web Vitals / WCAG / "无障碍"
  RULE: V7 辅承载 — 前端改动后按需跑 4 子能力之一（a11y/perf/regression/visual-diff）
  DETAIL: 本 SKILL.md 路由 + references/{a11y,perf,regression-e2e,visual-diff}.md
metadata:
  version: "2.0.0"
  merged_from:
    - web-audit-a11y@1.0.0
    - web-perf-budget@1.0.0
    - web-regression-e2e@1.0.0
    - web-visual-diff@1.0.0
---

# web-quality — Web 质量测试套件（4 合 1 · v2.0）

> v2.0 合并自 web-audit-a11y + web-perf-budget + web-regression-e2e + web-visual-diff
> 单一入口路由到 4 子能力，references/ 按子能力分文件

## 决策树（路由 4 子能力）

| 触发关键词 | 子能力 | reference（主入口） | 主用工具 | 子参考目录 |
|---|---|---|---|---|
| 无障碍 / WCAG / ARIA / 屏幕阅读器 / a11y | a11y | references/a11y.md | @axe-core/playwright | references/a11y/ |
| 性能预算 / Lighthouse / Web Vitals / LCP / CLS / INP / 首屏 | perf | references/perf.md | Lighthouse + Web Vitals API | references/perf/ |
| E2E 回归 / Playwright / 端到端测试 / 跨浏览器 | regression-e2e | references/regression-e2e.md | Playwright | references/regression-e2e/ |
| 视觉回归 / UI 回归 / 截图对比 / 像素 diff / pixel diff | visual-diff | references/visual-diff.md | Playwright screenshots + pixelmatch | references/visual-diff/ |

## 决策原则

1. **用户触发关键词路由**：用户说"测 a11y" → 加载 references/a11y.md；说"跑 perf" → 加载 references/perf.md；E2E → regression-e2e.md；视觉 → visual-diff.md
2. **多能力组合**：用户说"全面质量审计" → 串行/并行跑 4 个（按需选）
3. **共享前置**：所有 4 子能力都依赖 Playwright（见 references/shared-setup.md）
4. **config 所有权**：`web-quality` 整体是 `e2e/playwright.config.ts` 的唯一 owner；4 子能力共用同一 config（testDir 分子目录），不新建第二个 config

## 共享前置：Playwright 安装（简版）

详细版见 `references/shared-setup.md`。

```bash
# 项目首次跑（e2e/ 目录尚不存在）
mkdir -p e2e && cd e2e
npm i -D @playwright/test
npx playwright install --with-deps chromium   # Linux 加 --with-deps；macOS 可省

# 子能力可选依赖（按需装）
npm i -D @axe-core/playwright                 # a11y
npm i -D lighthouse playwright-lighthouse     # perf
# visual-diff 无需额外依赖（Playwright toHaveScreenshot 内置像素对比）
```

> 项目无 `e2e/` → 先看 regression-e2e 的 `references/regression-e2e/scaffold-templates.md` 做脚手架。

## 目录约定

```
e2e/
├── playwright.config.ts        # 唯一 owner：web-quality
├── tests/
│   ├── a11y/                   # a11y 测试
│   ├── perf/                   # perf 测试
│   ├── visual/                 # 视觉回归
│   ├── p0/                     # 关键路径 E2E
│   └── ux/                     # UX 细节 E2E
└── __snapshots__/              # 视觉回归基线

web-test-output/                # 报告汇总
├── a11y/                       # a11y HTML/JSON
└── perf/                       # Lighthouse JSON/HTML
```

## 与其他 skill 协作

- `agent-browser`：提供浏览器自动化基础（web-quality 依赖 Playwright，agent-browser 提供探索式浏览）
- `ui-design-system`：设计 token 规范（视觉回归时作为 baseline 对照）
- `loop` / `go`：在闭环编码中按需调用 web-quality 的某个子能力
- `testing`：通用测试方法论（POM、fixture、test pyramid），web-quality 聚焦 web 四能力落地

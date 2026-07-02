---
name: web-visual-diff
description: Use when comparing screenshots across runs to detect unintended UI changes (visual regression). Triggers on "visual diff", "screenshot comparison", "UI 回归", "视觉回归", "pixel diff", "snapshot test". First run captures baseline; subsequent runs diff against baseline. Not for accessibility (use web-audit-a11y) or performance (use web-perf-budget).
metadata:
  version: "1.0.0"
  engine: "playwright + pixelmatch ^6.0.0"
  scope: visual regression only
---

# web-visual-diff

Detect unintended UI changes by comparing screenshots across runs.

## When to use

- Antd / Tailwind 主题切换后验证全局一致
- 改 CSS / 主题 token 后确认无副作用
- 跨浏览器视觉一致性（Chromium / Firefox / WebKit）
- 多语言/多租户的 UI 一致性

## When NOT to use

- 探索性"哪里坏了" → `agent-browser/dogfood`
- 像素级单元测试 → 项目级 `jest-snapshot`
- a11y → `web-audit-a11y`
- 性能 → `web-perf-budget`

## Quick start

```bash
# 首次跑：生成基线（不 fail）
npx playwright test visual.spec.ts --update-snapshots

# 后续跑：对比基线
npx playwright test visual.spec.ts
```

## Workflow

### Phase 1: 配置基线目录

```typescript
// playwright.config.ts (additions)
export default defineConfig({
  expect: {
    toMatchSnapshot: {
      maxDiffPixelRatio: 0.01,        // 1% 像素差异容忍
      threshold: 0.2,                  // 颜色差异阈值 0-1
      animations: "disabled",          // 禁用动画（避免 flicker）
    },
  },
});
```

### Phase 2: 写截图测试

```typescript
// tests/visual/home.spec.ts
import { test, expect } from "@playwright/test";

test("home page desktop", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page).toHaveScreenshot("home-desktop.png", {
    fullPage: true,
  });
});

test("home page mobile", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto("/");
  await expect(page).toHaveScreenshot("home-mobile.png", {
    fullPage: true,
  });
});
```

### Phase 3: 屏蔽动态内容

见 `references/dynamic-content-masking.md`。

### Phase 4: 基线管理

见 `references/visual-baseline-management.md`。

## Inputs

| Input | Required | Default |
|---|---|---|
| 目标 URL | yes | — |
| 视口列表 | no | desktop only |
| 基线目录 | no | `e2e/__snapshots__/` |

## Outputs

| Output | Path |
|---|---|
| 基线截图 | `e2e/__snapshots__/` |
| Diff 图 | `e2e/test-results/.../diff.png` |
| HTML 报告 | `e2e/playwright-report/` |

## references/

- `references/pixelmatch-config.md` — 阈值/抗锯齿/忽略区域
- `references/dynamic-content-masking.md` — 屏蔽时间戳/广告/动画
- `references/visual-baseline-management.md` — 基线更新 + 审批

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Diff 巨大（>5%） | 动态内容未屏蔽 | 见 `dynamic-content-masking.md` |
| CI 跑 fail 本地 pass | 字体差异 | 统一用 `font-family: system-ui` 或嵌入字体 |
| 跨浏览器差异大 | 渲染引擎差异 | 接受 1-2% 容忍（pixelmatch config） |

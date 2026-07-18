# visual-diff 子能力 — 视觉回归 / 截图对比

> 本文件由 web-visual-diff@1.0.0 迁移而来
> 入口：用户触发"视觉回归 / UI 回归 / 截图对比 / 像素 diff / pixel diff"等关键词
> 共享前置见 `shared-setup.md`；本能力**无需额外依赖**（Playwright `toHaveScreenshot` 内置像素对比）

## config 协作

`web-quality` 是 `e2e/playwright.config.ts` 的唯一 owner。
本子能力向同一 config **追加** `expect.toMatchSnapshot` 字段（见下 Phase 1），不新建 config。

## When to use

- Antd / Tailwind 主题切换后验证全局一致
- 改 CSS / 主题 token 后确认无副作用
- 跨浏览器视觉一致性（Chromium / Firefox / WebKit）
- 多语言/多租户的 UI 一致性

## When NOT to use

- 探索性"哪里坏了" → `agent-browser/dogfood`
- 像素级单元测试 → 项目级 `jest-snapshot`
- a11y → `references/a11y.md`
- 性能 → `references/perf.md`
- 交互流程 E2E → `references/regression-e2e.md`

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

见 `visual-diff/dynamic-content-masking.md`。

### Phase 4: 基线管理

见 `visual-diff/visual-baseline-management.md`。

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

## references/visual-diff/（详细参考）

- `visual-diff/pixelmatch-config.md` — 阈值/抗锯齿/忽略区域
- `visual-diff/dynamic-content-masking.md` — 屏蔽时间戳/广告/动画
- `visual-diff/visual-baseline-management.md` — 基线更新 + 审批

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Diff 巨大（>5%） | 动态内容未屏蔽 | 见 `dynamic-content-masking.md` |
| CI 跑 fail 本地 pass | 字体差异 | 统一用 `font-family: system-ui` 或嵌入字体 |
| 跨浏览器差异大 | 渲染引擎差异 | 接受 1-2% 容忍（pixelmatch config） |

# perf 子能力 — 性能预算 / Lighthouse / Web Vitals

> 本文件由 web-perf-budget@1.0.0 迁移而来
> 入口：用户触发"性能预算 / Lighthouse / Web Vitals / LCP / CLS / INP / 首屏"等关键词
> 共享前置见 `shared-setup.md`；本能力额外需 `npm i -D lighthouse playwright-lighthouse`

## config 协作

`web-quality` 是 `e2e/playwright.config.ts` 的唯一 owner。
perf 测试文件放 `e2e/tests/perf/`，共用同一 config，不新建 config。

## When to use

- 上线前性能守门（PR 阻塞）
- 改前端基础设施后确认性能不退化
- 多页面性能横向对比
- 移动端弱网环境验证

## When NOT to use

- 单元/组件级性能 → 项目级 React DevTools Profiler
- 真实用户监控 (RUM) → 需要部署 web-vitals SDK
- 服务端性能 → 后端 APM
- 视觉/交互 → `references/visual-diff.md` / `references/regression-e2e.md`
- 无障碍 → `references/a11y.md`

## Quick start

```bash
# 一次性审计
npx lighthouse https://my-app.com --output=json --output-path=./report.json

# CI 集成（playwright + lighthouse）
npx playwright test perf/
```

## 性能预算配置

`perf-budget.json`:

```json
{
  "thresholds": {
    "lcp": 2500,
    "cls": 0.1,
    "inp": 200,
    "fcp": 1800,
    "tti": 3800,
    "speedIndex": 3400,
    "totalBlockingTime": 200
  },
  "device": "mobile",
  "throttling": "Fast 3G"
}
```

## Playwright 集成

```typescript
// tests/perf/home.spec.ts
import { test, expect } from "@playwright/test";
import { playAudit } from "playwright-lighthouse";

test("home page perf budget", async ({ page }) => {
  await page.goto("/");
  const result = await playAudit({
    page,
    thresholds: {
      lcp: 2500,
      cls: 0.1,
      inp: 200,
    },
    reports: {
      formats: { json: true, html: true },
    },
  });
  // 详见 perf/lighthouse-cli-options.md
});
```

## 严重度判定

| 阈值超 | 判定 |
|---|---|
| ≤ 10% | 通过（噪声内） |
| 10-30% | 警告（CI 不阻塞，本地提示） |
| > 30% | 失败（CI 阻塞） |

## Inputs

| Input | Required | Default |
|---|---|---|
| 目标 URL | yes | — |
| 设备 | no | mobile |
| 预算文件 | no | `perf-budget.json` |
| 网络节流 | no | Fast 3G |

## Outputs

| Output | Path |
|---|---|
| Lighthouse JSON | `web-test-output/perf/perf-report.json` |
| Lighthouse HTML | `web-test-output/perf/perf-report.html` |
| 摘要 | `web-test-output/perf/perf-summary.md` |

## references/perf/（详细参考）

- `perf/web-vitals-thresholds.md` — 项目类型对应合理阈值
- `perf/lighthouse-cli-options.md` — CLI 参数大全
- `perf/perf-regression-investigation.md` — 回归定位指南

## CI 集成

```yaml
- name: Perf audit
  run: |
    npx lighthouse $URL --output=json --output-path=./perf.json
    npx ts-node scripts/check-perf-budget.ts ./perf.json
```

`scripts/check-perf-budget.ts`：对比 `perf.json` 的 metrics 与 `perf-budget.json` 阈值，输出超阈值的项并 exit 1。

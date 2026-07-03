---
name: web-audit-a11y
description: Use when auditing web pages for accessibility (WCAG) compliance. Triggers on "a11y", "accessibility", "无障碍", "WCAG", "axe-core", "ARIA audit", "screen reader test". Uses @axe-core/playwright under the hood. Not for visual regression (use web-visual-diff) or general functional tests (use web-regression-e2e).
metadata:
  version: "1.0.0"
  engine: "@axe-core/playwright ^4.10.0"
  default_level: WCAG 2.1 AA
---

# web-audit-a11y

Audit web pages for accessibility (WCAG) compliance using axe-core.

## Prerequisites（首次使用前必装）

| 依赖 | 安装命令 | 说明 |
|---|---|---|
| Playwright + 浏览器 | 复用 web-regression-e2e 的 `e2e/`；无则 `npm i -D @playwright/test && npx playwright install chromium` | — |
| axe-core | `npm i -D @axe-core/playwright` | WCAG 规则引擎 |

## config 协作

`web-regression-e2e` 是 `e2e/playwright.config.ts` 的唯一 owner。
本 skill 的测试文件放 `e2e/tests/a11y/`，共用同一 config 的 `baseURL` / `projects`，不新建 config。

## When to use

- 上线前 a11y 守门
- 改组件后确认无障碍特性未退化
- 监管要求（金融/医疗/政府类项目 WCAG 2.1 AA 强制）
- 主动改进可访问性

## When NOT to use

- 视觉回归 → `web-visual-diff`
- 交互流程测试 → `web-regression-e2e`
- 探索性 UX 评估 → `agent-browser/dogfood`

## Quick start

```typescript
// tests/a11y/home.spec.ts
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("home page WCAG 2.1 AA", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
```

## 严重度分级

axe-core 返回 4 级：

| 级别 | 含义 | 是否阻塞 PR |
|---|---|---|
| `critical` | 严重（如：按钮无 name） | **是** |
| `serious` | 重要（如：对比度不足） | **是** |
| `moderate` | 中等（如：landmark 缺失） | 建议修 |
| `minor` | 轻微（如：title 过长） | 可选 |

## 报告输出

axe-core 不自带 HTML 报告器。生成 HTML 报告有三种方式（实现见 `references/a11y-report-templates.md`）：

1. **自实现 `generateHtmlReport(results)`**（推荐，无额外依赖）—— utils/a11y-report.ts 提供，输出含严重度分组的 HTML 表格
2. **axe-html-reporter**（第三方，开箱即用交互报告）
3. **axe-cli**（一次性命令行审计）

```typescript
// 方式1 示例（完整实现见 references/a11y-report-templates.md §方式1）
import { generateHtmlReport } from "../../utils/a11y-report";
import { writeFileSync } from "node:fs";

test("生成 a11y 报告", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  writeFileSync("web-test-output/a11y/a11y-report.html", generateHtmlReport(results), "utf-8");
  writeFileSync("web-test-output/a11y/issues.json", JSON.stringify(results.violations, null, 2), "utf-8");
});
```

或用 axe-cli（命令行）：
```bash
npx @axe-core/cli https://my-app.com --tags wcag2a,wcag2aa --save a11y-report.html --exit
```

## Inputs

| Input | Required | Default |
|---|---|---|
| 目标 URL | yes | — |
| WCAG 等级 | no | 2.1 AA |
| 输出格式 | no | JSON + HTML |
| 阻塞严重度 | no | critical + serious |

## Outputs

| Output | Path |
|---|---|
| JSON 报告 | `web-test-output/a11y/issues.json` |
| HTML 报告 | `web-test-output/a11y/a11y-report.html` |

## references/

- `references/wcag-rules-coverage.md` — axe-core 覆盖的 WCAG 规则清单
- `references/antd-a11y-gotchas.md` — Antd 已知 a11y 问题 + 解决方案
- `references/false-positive-handling.md` — 已知误报 + 抑制规则
- `references/a11y-report-templates.md` — generateHtmlReport 实现 + 3 种报告生成方式

## 严重度策略

```typescript
function shouldBlockPR(violations: Result[]): boolean {
  return violations.some((v) =>
    v.impact === "critical" || v.impact === "serious"
  );
}
```

CI 配置：
```yaml
- name: A11y audit
  run: npx playwright test a11y/
- name: Block on critical/serious
  if: failure()
  run: |
    if grep -q '"impact":"critical"\|"impact":"serious"' test-results/a11y/issues.json; then
      echo "❌ Critical/serious a11y issues found"
      exit 1
    fi
```

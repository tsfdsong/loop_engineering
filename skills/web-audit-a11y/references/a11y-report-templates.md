# a11y 报告生成模板

> SKILL.md "报告输出" 段调用 `generateHtmlReport(results)`，本文件提供其实现。
> axe-core 不自带 HTML 报告器；有三种方式生成 HTML 报告。

## 方式 1：自实现 generateHtmlReport（推荐，无额外依赖）

```typescript
// utils/a11y-report.ts
import type { AxeResults, Result } from "axe-core";

export function generateHtmlReport(results: AxeResults): string {
  const violations = results.violations ?? [];
  const summary = summarize(violations);

  const rows = violations
    .map((v) => rowHtml(v))
    .join("\n");

  return `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>a11y Report</title>
<style>
  body{font-family:system-ui,sans-serif;margin:2rem;color:#222}
  table{border-collapse:collapse;width:100%}
  th,td{border:1px solid #ddd;padding:.5rem;text-align:left;vertical-align:top}
  .critical{background:#fde8e8}.serious{background:#fff4e0}
  .moderate{background:#fffbe6}.minor{background:#f0f0f0}
  .summary span{display:inline-block;margin-right:1rem;font-weight:bold}
</style></head><body>
<h1>a11y 审计报告</h1>
<p>URL: <code>${escapeHtml(results.url)}</code> · 规则: ${results.testEngine.name} ${results.testEngine.version}</p>
<div class="summary">
  <span class="critical">critical: ${summary.critical}</span>
  <span class="serious">serious: ${summary.serious}</span>
  <span class="moderate">moderate: ${summary.moderate}</span>
  <span class="minor">minor: ${summary.minor}</span>
</div>
<table>
  <thead><tr><th>严重度</th><th>规则</th><th>描述</th><th>影响元素数</th><th>帮助</th></tr></thead>
  <tbody>${rows || '<tr><td colspan="5">✅ 无违规</td></tr>'}</tbody>
</table>
</body></html>`;
}

function summarize(violations: Result[]) {
  const s = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of violations) {
    const impact = v.impact as keyof typeof s | undefined;
    if (impact && impact in s) s[impact]++;
  }
  return s;
}

function rowHtml(v: Result): string {
  const cls = v.impact ?? "minor";
  const count = v.nodes?.length ?? 0;
  return `<tr class="${cls}">
    <td>${v.impact ?? "n/a"}</td>
    <td><code>${escapeHtml(v.id)}</code></td>
    <td>${escapeHtml(v.description)}</td>
    <td>${count}</td>
    <td><a href="${escapeHtml(v.helpUrl)}" target="_blank">查看</a></td>
  </tr>`;
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string
  );
}
```

用法：

```typescript
// tests/a11y/report.spec.ts
import { writeFileSync } from "node:fs";
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { generateHtmlReport } from "../../utils/a11y-report";

test("生成 a11y 报告", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  writeFileSync(
    "web-test-output/a11y/a11y-report.html",
    generateHtmlReport(results),
    "utf-8"
  );
  // 同时存 JSON 供 CI 解析
  writeFileSync(
    "web-test-output/a11y/issues.json",
    JSON.stringify(results.violations, null, 2),
    "utf-8"
  );
});
```

## 方式 2：用 axe-html-reporter（第三方，功能更全）

```bash
npm i -D axe-html-reporter
```

```typescript
import { createHtmlReport } from "axe-html-reporter";
import AxeBuilder from "@axe-core/playwright";

test("a11y with axe-html-reporter", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).analyze();
  createHtmlReport({
    results,
    options: {
      projectKey: "MY_APP",
      outputDir: "web-test-output/a11y",
      reportFileName: "a11y-report.html",
    },
  });
});
```

## 方式 3：axe-cli（一次性审计，不写代码）

```bash
npx @axe-core/cli https://my-app.com \
  --tags wcag2a,wcag2aa,wcag21a,wcag21aa \
  --save web-test-output/a11y/a11y-report.html \
  --exit
```

`--exit` 让违规时退出码非 0（CI 阻塞用）。

## 选型建议

| 场景 | 推荐 |
|------|------|
| Playwright 测试套件内、自定义样式 | 方式 1（自实现）|
| 要开箱即用的交互式报告 | 方式 2（axe-html-reporter）|
| 一次性/CI 命令行审计 | 方式 3（axe-cli）|

## CI 阻塞判定（结合 shouldBlockPR）

报告生成与 PR 阻塞是两件事。生成报告（方式 1/2/3）只产出 HTML；是否阻塞看 SKILL.md 的 `shouldBlockPR()` 逻辑——critical/serious 存在即 exit 1。

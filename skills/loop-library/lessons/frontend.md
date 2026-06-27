---
id: FE-002
domain: frontend
severity: high
applies_when:
  - task_type: frontend
  - task_type: fullstack
  - has_sample_url: true
source: loop/mcp-plaza-0626
created: 2026-06-26
---

## 给了样本 URL 必须双开对照结构，不能凭脑补布局

**问题**: loop/mcp-plaza-0626 任务中，用户提供了参考截图/页面作为前端样本，但实现 McpHubPage/McpDetailPage/McpAdminPage 时全凭脑补布局，未对照样本。结果页面结构、区块划分、交互方式与预期差距很大，用户不得不反复指出问题。

**根因**: 没有"样本摄入 → 结构对照"机制。看到样本后没有用 Playwright 提取样本的结构化 accessibility tree 作为复刻基准，而是自由发挥。

**规则**:
- Step① 摄入样本时：`browser_navigate(样本URL)` → `browser_snapshot` → 保存基准结构到 `loop-screenshots/sample-<name>.yml` → 识别关键区块清单
- F5（样本对照）维度：实现完成后**双开对照**——同时 snapshot 样本页和自己的页，逐区块比对（存在性/层级/元素类型）
- **客观项**（区块缺失、元素类型错误）→ 自动判定，缺失则进自愈闭环修复
- **主观项**（配色/间距/视觉风格）→ 标记"🎨 设计待确认"，列入报告供用户定夺，不自动改
- 禁止"看了样本一眼就凭记忆写"，必须以 snapshot 结构为准

**关联门禁**: F5

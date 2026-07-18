---
name: agent-browser
description: |
  TRIGGER: 与网站交互 / 浏览器自动化 / 截图 / 填表 / 抓取网页 / 测试 web app / '浏览器' / '网页' / '截图' / '打开' / '登录' / '抓取' / 'open website'（不用于：读项目代码用 Read/MCP，生成文档用 writing-skills）
  RULE: V7 视觉上下文 — UI/前端问题前必须打开页面截图取证，改后对比验证
  DETAIL: 本 SKILL.md（CLI 命令）+ 与 ui-design-system / web-quality 配合
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)
hidden: true
---

# agent-browser

Fast browser automation CLI for AI agents. Chrome/Chromium via CDP with
accessibility-tree snapshots and compact `@eN` element refs.

Install: `npm i -g agent-browser && agent-browser install`

## Start here

This file is a discovery stub, not the usage guide. Before running any
`agent-browser` command, load the actual workflow content from the CLI:

```bash
agent-browser skills get core             # start here — workflows, common patterns, troubleshooting
agent-browser skills get core --full      # include full command reference and templates
```

The CLI serves skill content that always matches the installed version,
so instructions never go stale. The content in this stub cannot change
between releases, which is why it just points at `skills get core`.

## Specialized skills

Load a specialized skill when the task falls outside browser web pages:

```bash
agent-browser skills get electron          # Electron desktop apps (VS Code, Slack, Discord, Figma, ...)
agent-browser skills get slack             # Slack workspace automation
agent-browser skills get dogfood           # Exploratory testing / QA / bug hunts
agent-browser skills get vercel-sandbox    # agent-browser inside Vercel Sandbox microVMs
agent-browser skills get agentcore         # AWS Bedrock AgentCore cloud browsers
```

Run `agent-browser skills list` to see everything available on the
installed version.

## Why agent-browser

- Fast native Rust CLI, not a Node.js wrapper
- Works with any AI agent (Cursor, Claude Code, Codex, Continue, Windsurf, etc.)
- Chrome/Chromium via CDP with no Playwright or Puppeteer dependency
- Accessibility-tree snapshots with element refs for reliable interaction
- Sessions, authentication vault, state persistence, video recording
- Specialized skills for Electron apps, Slack, exploratory testing, cloud providers

## Observability Dashboard

The dashboard runs independently of browser sessions on port 4848 and can also be opened through a proxied or forwarded URL such as `https://dashboard.agent-browser.localhost`. Agents should stay on the dashboard origin: session tabs, status, and stream traffic are proxied internally, so session ports do not need to be exposed.

---

## §N. 前端改动截图对比闭环（v2.0 强化 · V7 主承载）

### 工作流（5 步）
1. **改动前**：截当前页面图（baseline · agent-browser snapshot）
2. **改动**：实施 UI 改动（CSS / 组件 / 路由）
3. **改动后**：截同一页面图（after · 同 viewport）
4. **对比**：用 `web-quality/references/visual-diff.md` 做 diff
5. **验证**：间距 / 响应式 / 视觉一致性 / 暗色模式

### 禁止行为（V7 红线）
- ❌ 纯靠 code review 判断 UI 效果（肉眼不可见的像素回归 / 布局偏移 / z-index 层级）
- ❌ 改完不截图就宣称"已完成"

### 与 ui-design-system 协作
- ui-design-system 提供设计 token 规范（baseline 对照）
- agent-browser 提供截图能力
- web-quality 提供 diff 工具

### 多 viewport 场景
- 桌面（1920x1080）/ 平板（768x1024）/ 手机（375x667）
- 每 viewport 都截 baseline + after
- 响应式问题专用此法发现

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

面向 AI agent 的快速浏览器自动化 CLI。通过 CDP 驱动 Chrome/Chromium，
提供 accessibility-tree 快照与紧凑的 `@eN` 元素引用。

安装：`npm i -g agent-browser && agent-browser install`

## 从这里开始

本文件是发现桩（discovery stub），不是使用指南。运行任何 `agent-browser`
命令之前，先从 CLI 加载真正的工作流内容：

```bash
agent-browser skills get core             # 从这里开始 — 工作流、常见模式、故障排查
agent-browser skills get core --full      # 含完整命令参考与模板
```

CLI 提供的 skill 内容始终与已安装版本匹配，指令永不过时。本桩文件的
内容不会随版本变化，所以它只指向 `skills get core`。

## 专用技能

任务超出浏览器网页范围时，按需加载专用技能：

```bash
agent-browser skills get electron          # Electron 桌面应用（VS Code、Slack、Discord、Figma 等）
agent-browser skills get slack             # Slack 工作区自动化
agent-browser skills get dogfood           # 探索性测试 / QA / bug 猎捕
agent-browser skills get vercel-sandbox    # Vercel Sandbox microVM 内的 agent-browser
agent-browser skills get agentcore         # AWS Bedrock AgentCore 云浏览器
```

运行 `agent-browser skills list` 查看已安装版本的全部可用技能。

## 为什么用 agent-browser

- 快速原生 Rust CLI，不是 Node.js 封装
- 兼容任意 AI agent（Cursor、Claude Code、Codex、Continue、Windsurf 等）
- 通过 CDP 驱动 Chrome/Chromium，不依赖 Playwright 或 Puppeteer
- accessibility-tree 快照 + 元素引用，交互可靠
- 会话、认证保险库、状态持久化、视频录制
- 面向 Electron 应用、Slack、探索性测试、云厂商的专用技能

## 可观测性仪表盘

仪表盘独立于浏览器会话运行于 4848 端口，也可通过代理/转发 URL 打开（如
`https://dashboard.agent-browser.localhost`）。agent 应停留在仪表盘 origin 内：
会话标签页、状态与流量都在内部代理，无需暴露会话端口。

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

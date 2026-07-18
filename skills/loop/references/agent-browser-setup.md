# agent-browser 环境配置与预检指南

> 方案 A（agent-browser MCP 全量替换 Playwright MCP）的安装、配置、预检规范。
> loop/go 技能在执行前端验证（F1-F5）前，**必须**确保 agent-browser 环境就绪。
> 本指南与具体 AI 编码工具无关（MCP 是标准协议）。各工具的配置路径见文末附录速查表。

---

## 一、安装

### 1.1 agent-browser CLI

```bash
# 方式 A: npm 全局安装（推荐，跨平台）
npm i -g agent-browser && agent-browser install

# 方式 B: Homebrew（macOS/Linux）
brew install agent-browser

# 方式 C: Cargo（从源码）
cargo install agent-browser
```

`agent-browser install` 会下载 Chrome for Testing（若系统无 Chrome/Chromium）。

### 1.2 Chrome/Chromium 依赖

agent-browser 通过 CDP 直连 Chrome，需要以下之一：
- 系统已安装 Google Chrome（任意现代版本）
- Chrome for Testing（`agent-browser install` 自动下载）
- Puppeteer 缓存中的 Chromium（自动 fallback）

---

## 二、MCP 配置（主推 `.mcp.json` + 工具速查）

### 2.1 标准配置（方案 A 推荐 · 项目根 `.mcp.json`）

agent-browser 是一个**标准 MCP server**，按 MCP 协议规范在任何支持 MCP 的宿主工具中均可加载。
推荐使用项目级 `.mcp.json`（MCP 官方约定路径，跨工具通用，随项目仓库提交）。

编辑项目根 `./.mcp.json`：

```json
{
  "mcpServers": {
    "agent-browser": {
      "type": "stdio",
      "command": "agent-browser",
      "args": ["mcp", "--tools", "core,network,debug,react"]
    }
  }
}
```

> 说明：字段名 `mcpServers` 是 MCP 规范定义的统一字段，不同工具（ZCode / Claude Code / Cursor 等）均遵循。
> 字段大小写在某些工具中可能不同（如驼峰 vs 全小写），以附录速查表中该工具的规范为准。

**`--tools` profile 说明**：

| Profile | 包含能力 | 启用建议 |
|---------|---------|---------|
| `core` | 导航、快照、交互、等待、读取、截图、eval、标签页 | ✅ 必选 |
| `network` | 网络请求、路由、HAR、离线、凭据 | ✅ F2 网络门禁需要 |
| `debug` | 控制台、错误、trace、record、diff、batch | ✅ F1 控制台门禁需要 |
| `react` | React 组件树、渲染追踪 | ⚠️ React 项目必选 |
| `state` | cookies、存储、auth、会话 | 可选（auth 为 CLI-only） |
| `tabs` | 标签页、窗口、对话框 | 可选 |
| `mobile` | 视口、设备、地理位置、触摸 | 可选（移动端测试） |
| `all` | 全部工具 | ⚠️ token 开销大，慎用 |

**推荐组合**：`core,network,debug,react`（覆盖 F1-F4 全维度，64 个工具）。

### 2.2 用户级配置（替代方案）

若不希望把 `.mcp.json` 提交进仓库（或希望全局生效），可改用宿主工具的用户级配置。
各工具的用户级配置路径见文末**附录：已知兼容工具 MCP 配置速查**。配置 JSON 结构与 2.1 相同。

### 2.3 Windows 注意事项

⚠️ **Windows subprocess 调用**：MCP 客户端通过 stdio 启动 MCP 服务器。`agent-browser` 是 npm 安装的 shim，Windows 上实际是 `agent-browser.cmd`。主流 MCP 客户端已处理此差异，**无需额外配置**。

若手动通过 Python subprocess 调用，需用 `shell=True` 或显式指定 `.cmd` 后缀。

### 2.4 持久登录态（方案 C）

需要复用 Chrome 登录态时，在 `args` 中追加 `--profile`：

```json
"args": ["mcp", "--tools", "core,network,debug,react", "--profile", "Default"]
```

⚠️ `--profile` 会与已运行的 Chrome 实例冲突，建议为验证专用创建独立 profile。

---

## 三、环境预检（G0 门禁）

### 3.1 自动预检命令

loop 技能在执行前端验证前，**必须**运行以下预检：

```bash
# 一键诊断
agent-browser doctor
```

**通过标准**（Summary 行必须显示 `0 fail`）：

| 检查项 | 通过判据 | 失败处置 |
|--------|---------|---------|
| CLI version | 显示版本号 | 重新安装 |
| Home directory | 存在且可写 | 检查权限 |
| State/socket dir | `~/.agent-browser` 可写 | 创建目录 |
| Chrome | 找到 chrome.exe | `agent-browser install` |
| Daemons | 无残留守护进程 | `agent-browser close --all` |
| Network | Chrome CDN 可达 | 检查网络/代理 |

### 3.2 版本要求

| 组件 | 最低版本 | 推荐 | 当前验证 |
|------|---------|------|---------|
| agent-browser | v0.29.0 | v0.29.1+ | ✅ v0.29.1 |
| Chrome | v110+ | 最新稳定版 | ✅ v149 |
| MCP protocol | 2025-11-25 | 最新 | ✅ |

### 3.3 MCP 连接验证

宿主工具启动后，确认 agent-browser MCP 已连接：

1. 查看宿主工具日志（路径见附录速查表）
2. 搜索 `agent-browser`，确认 `toolCount > 0`
3. 预期 `toolCount: 64`（core,network,debug,react 组合）

### 3.4 降级回退（方案 A → Playwright）

若 agent-browser MCP 不可用，临时回退：

1. 编辑宿主配置文件（`.mcp.json` 或对应工具的用户级配置，见附录），注释 `agent-browser` 配置
2. 恢复 Playwright MCP 配置：
   ```json
   "playwright": {
     "type": "stdio",
     "command": "npx",
     "args": ["@playwright/mcp@latest", "--browser", "chromium"]
   }
   ```
3. 同步恢复 `frontend-verification.md` 和 `gate-matrix.md` 中的工具名（git checkout 即可）

---

## 四、能力边界速查

### 4.1 MCP 工具 vs CLI 命令

```
MCP 一等工具（64个，类型安全，F1-F4 核心流程使用）
├── 交互: open/snapshot/click/fill/type/select/check/press/scroll
├── 等待: wait_ms/wait_for_selector/wait_for_text/wait_for_load
├── 读取: get_text/get_url/get_title/console/errors
├── 网络: network_requests/network_route/network_har_*/set_offline
├── 标签: tab_new/tab_list/tab_switch/tab_close
├── 调试: trace_*/profiler_*/record_*/diff_snapshot/diff_screenshot/diff_url/batch
└── React: react_tree/react_inspect/react_renders_*

仅 CLI（Bash 调用，无类型校验，增强场景使用）
├── 性能: vitals（LCP/FCP/TTFB/CLS/INP）
├── 认证: auth save/login/list（加密凭据库）
├── 会话: session list（多会话管理）
├── 鼠标: hover/dblclick/drag/focus/mouse
├── 截图: screenshot --annotate（标注截图，MCP 用 screenshot + extraArgs）
└── 桌面: electron（VS Code/Slack/Figma 等）
```

### 4.2 F1-F5 维度工具映射

| 门禁维度 | MCP 工具 | CLI（备选） |
|---------|---------|------------|
| F1 控制台 | `agent_browser_errors` + `agent_browser_console` | - |
| F2 网络 | `agent_browser_network_requests` | - |
| F3 渲染 | `agent_browser_snapshot` | - |
| F4 交互 | `agent_browser_click/fill/select` + `agent_browser_batch` | - |
| F5 样本对照 | `agent_browser_diff_snapshot` | `diff screenshot --baseline` |
| 性能（可选） | ❌ | `agent-browser vitals` |
| 录制审计 | `agent_browser_record_start/stop` | - |

### 4.3 Playwright MCP 能力缺口

agent-browser **无法替代** 的 Playwright MCP 能力：

| 能力 | 影响 | 缓解 |
|------|------|------|
| `browser_run_code`（Playwright API 执行） | 无法运行 `page.route()`/`page.waitForResponse()` 等深度 API | 用 `network_route` + `eval` 组合替代 |
| Firefox 浏览器 | 仅支持 Chrome/Chromium | 需 Firefox 时临时回退 Playwright |
| WebKit/Safari（桌面） | 仅 iOS Safari（通过 Appium） | 需桌面 Safari 时临时回退 |

---

## 五、故障排查

### 5.1 MCP 未连接

```
症状: 宿主工具日志无 agent-browser 工具注册
排查:
  1. agent-browser --version  （确认已安装）
  2. agent-browser doctor     （确认环境就绪）
  3. 检查配置文件的 command/args 拼写
  4. 手动启动测试: agent-browser mcp --tools core
```

### 5.2 Chrome 启动失败

```
症状: Launch test fail / 启动超时
排查:
  1. agent-browser install  （重新下载 Chrome for Testing）
  2. 检查是否有残留守护进程: agent-browser close --all
  3. 检查杀毒软件是否拦截 chrome.exe
  4. 尝试 --executable-path 指定系统 Chrome
```

### 5.2.1 daemon 状态损坏（Windows 高频问题）🔴

```
症状: agent-browser open <url> 挂起无输出（exit 124 timeout），
      但 agent-browser doctor 的 Launch test 能通过
根因: 手动 taskkill chrome.exe 或异常退出导致 daemon 与 Chrome 实例
      状态不一致，pid 文件残留但 Chrome 已死，daemon 无法恢复
处置（按顺序）:
  1. agent-browser close --all          # 优雅关闭所有会话
  2. taskkill //F //IM chrome.exe        # 强杀残留 Chrome（Windows）
  3. rm -f ~/.agent-browser/default.*    # 清理 pid/port/engine 状态文件
  4. sleep 3                             # 等待端口释放
  5. agent-browser doctor                # 触发 daemon 干净重建
  6. 若仍卡住: 重启宿主工具会话（MCP 连接会重建 daemon）
预防:
  - 禁止手动 taskkill chrome.exe，一律用 agent-browser close --all
  - 长时间不用时主动 close，避免守护进程泄漏
  - CI 环境每个 job 开始前先 close --all + 清理状态文件
影响: 环境问题（C类），非方案 A 代码缺陷，不影响文档正确性
```

### 5.3 截图路径问题（Windows）

```
症状: screenshot 返回成功但文件不存在
原因: Windows 路径反斜杠被 shell 吞掉
解决: 一律使用正斜杠 C:/path/to/file.png，不要用反斜杠
```

### 5.4 @ref 失效

```
症状: Unknown ref: eN
原因: 页面状态变化后旧 ref 失效
解决: 重新 snapshot 获取新 @ref
规则: snapshot → 用@ref操作 → snapshot → 用新@ref操作（循环）
```

### 5.5 favicon.ico 404 误报（F2）

```
症状: F2 网络门禁报 404，但页面功能正常
原因: 测试页面无 favicon.ico，浏览器自动请求
处置: B类（验证脚本问题），非业务 bug，F2 判定时排除 favicon.ico
配置: 测试 HTML 加 <link rel="icon" href="data:,"> 可消除
```

---

## 六、升级与维护

### 6.1 升级 agent-browser

```bash
agent-browser upgrade    # 自动检测安装方式并升级
agent-browser doctor     # 升级后重新诊断
```

### 6.2 清理过时文件

```bash
agent-browser doctor --fix    # 自动清理过时缓存/守护进程
```

### 6.3 版本兼容性矩阵

| agent-browser | Chrome | MCP protocol |
|:--:|:--:|:--:|
| v0.29.x | v110+ | 2025-11-25 |
| v0.30.x | v110+ | 2025-11-25 |

> 升级后若 MCP 工具数变化，需同步更新本文件的「能力边界」章节。

---

## 附录：已知兼容工具 MCP 配置速查

agent-browser 是标准 MCP server，可被任何符合 MCP 规范的宿主工具加载。
以下为已测/常见工具的配置路径（**仅供速查**；以各工具最新官方文档为准）：

| 工具 | 配置文件路径 | 优先级 | 格式 |
|---|---|---|---|
| **通用标准（推荐）** | `./.mcp.json`（项目根） | 最高 | `mcpServers` 字段 |
| ZCode | `~/.zcode/cli/config.json` | 用户级 | `mcp.servers` 字段 |
| Claude Code | `~/.claude/settings.json` 或 `.mcp.json` | 用户级 / 项目级 | `mcpServers` 字段 |
| Cursor | `~/.cursor/mcp.json` 或 `.cursor/mcp.json` | 用户级 / 项目级 | `mcpServers` 字段 |
| Codex | `~/.codex/config.toml` | 用户级 | `[mcp_servers]` 段 |
| Gemini CLI | `~/.gemini/settings.json` | 用户级 | `mcpServers` 字段 |
| TRAE | （v1.5 后补充） | — | — |

**未列出的工具**：参考该工具的官方 MCP 配置文档。`agent-browser` 是标准 MCP server，
按 2.1 节的 JSON 结构配置即可（若该工具的字段名/大小写有差异，以其规范为准）。

**日志路径速查**（MCP 连接验证用）：

| 工具 | 日志路径 |
|---|---|
| ZCode | `~/.zcode/cli/log/zcode-YYYY-MM-DD.jsonl` |
| Claude Code | `~/.cache/claude-cli-nodejs/` 或项目 `.claude/logs/` |
| Cursor | `~/Library/Application Support/Cursor/logs/`（macOS）/ `%APPDATA%\Cursor\logs\`（Windows） |
| 其它 | 见对应工具文档 |

> 本速查表仅作为已测工具示例。LoopEngine 不绑定具体工具。

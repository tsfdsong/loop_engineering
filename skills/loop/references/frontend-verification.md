# 前端验证协议（四阶段）

涉及前端/UI/页面/交互类功能时，**必须**执行此协议。

## 触发条件

验收条件含以下关键词任一，或任务涉及前端代码修改：
前端 / 页面 / UI / 组件 / 交互 / 网页 / 浏览器 / 点击 / 表单 / 路由

## 四阶段执行流程

```
阶段0: 环境就绪
  G1 已通过 + 前后端服务已启动

阶段1: 页面加载断言
  agent_browser_open(targetUrl) → agent_browser_snapshot
  → 断言: 页面标题/路由正确, 无全局错误边界

阶段2: 三件套采集 + 自动断言
  console = agent_browser_errors + agent_browser_console
  network = agent_browser_network_requests
  snapshot = 阶段1的结构
  → 自动断言（见判定表）

阶段3: 交互流执行（F4）
  对验收条件中每个用户操作流:
    snapshot → 拿@ref → click/fill → snapshot
    每步采集 console+network → 断言

阶段4: 汇总 → 门禁报告 F1-F4
  全绿 → 前端验证通过
  有红 → 进入自愈闭环
```

## 三件套判定表

| 信号源 | 通过判定 | 失败处置 |
|--------|---------|---------|
| `agent_browser_errors` | error 数量 = 0 | 每个 error 读堆栈 → 归类 A/B/C |
| `agent_browser_network_requests` | 全部 2xx/3xx | 每个 4xx/5xx 读响应体 → 归类 A/B/C |
| `agent_browser_snapshot` | 验收条件要求的元素全命中 | 缺失元素 → 检查渲染逻辑 → 归类 A |

**截图仅留证**: `agent_browser_screenshot` 仅存档（路径 `loop-screenshots/R<轮次>-<场景>.png`），不作为通过判据。

## agent-browser MCP 工具

| 工具 | 用途 |
|------|------|
| `agent_browser_open` | 导航到指定 URL |
| `agent_browser_snapshot` | 获取页面 accessibility tree（@eN 紧凑引用） |
| `agent_browser_click` | 点击元素（通过 @ref 定位） |
| `agent_browser_fill` | 填写输入框内容（清空后填入） |
| `agent_browser_type` | 追加输入文本（不清空） |
| `agent_browser_screenshot` | 截图留证（不作为判据；支持 --annotate 标注模式） |
| `agent_browser_errors` | 读取未捕获 JS 错误（**判据**，不含 warning） |
| `agent_browser_console` | 读取完整控制台日志（含 warning/info） |
| `agent_browser_network_requests` | 读取网络请求（**判据**） |
| `agent_browser_select` | 下拉选项选择 |
| `agent_browser_press` | 按键操作 |
| `agent_browser_wait_for_selector` | 等待元素/文本/URL/加载状态 |
| `agent_browser_eval` | 执行 JavaScript |
| `agent_browser_batch` | 批量执行多个命令（减少往返） |

### 独有增强能力

> ⚠️ **MCP 与 CLI 能力边界**：下表「MCP 工具」列在 agent-browser MCP 服务器中直接可用；「仅 CLI」列需通过 `Bash(agent-browser <cmd>)` 调用，MCP 未暴露。配置 `--tools core,network,debug,react` 时 MCP 暴露 64 个工具。

| 能力 | MCP 工具 | 仅 CLI | 用途 |
|------|:--:|:--:|------|
| 页面变化检测 | `agent_browser_diff_snapshot` | - | 对比前后快照，F4 交互后自动校验 |
| 视频录制 | `agent_browser_record_start/stop` | - | 操作过程 WebM 录制，审计回放 |
| 标注截图 | `agent_browser_screenshot --annotate` | - | 元素编号+坐标框，视觉驱动调试 |
| 网络追踪 | `agent_browser_network_har_*` | - | HAR 录制，网络回归分析 |
| React 内省 | `agent_browser_react_tree/inspect` | - | React 组件树/Suspense 边界 |
| Web Vitals | ❌ | `agent-browser vitals` | LCP/FCP/TTFB/CLS/INP 性能指标 |
| 认证保险库 | ❌ | `agent-browser auth save/login` | 加密凭据存储 |
| 会话管理 | ❌ | `agent-browser session list` | 多会话隔离 |
| hover/dblclick/drag | ❌ | `agent-browser hover/dblclick/drag` | 高级鼠标交互 |

**能力边界规则**：
- F1-F4 核心验证流程：全部使用 MCP 工具（一等工具，类型安全）
- 性能/认证/会话/高级鼠标：需时通过 `Bash` 调用 CLI（二等调用，无类型校验）
- 文档引用独有能力时，必须标注调用方式（MCP 或 CLI）

## @Ref 失效规则

- @ref（如 @e3）是某次 snapshot 的产物，仅在该页面状态下有效
- 以下情况后旧 @ref 立即失效，必须重新 `agent_browser_snapshot`:
  ① 执行过 `agent_browser_open` / `agent_browser_click` / `agent_browser_fill`(submit) 后
  ② 页面发生路由跳转后
  ③ 任何超过 1 次连续交互之间
- **标准交互序列**: snapshot → 拿@ref → click/fill → snapshot → 拿新@ref → click/fill → ...

## 登录态处理

agent-browser 提供多层登录态管理方案：

- **方案 A（推荐）**: 验证脚本内置登录步骤，每轮自行完成登录后测目标功能（纯 MCP）
- **方案 B（auth vault, CLI）**: `Bash(agent-browser auth save <name>)` 保存凭据 → `Bash(agent-browser auth login <name>)` 自动登录（凭据加密存储，LLM 不可见）
- **方案 C（Chrome profile, 启动参数）**: ZCode config 的 agent-browser MCP `args` 加 `--profile <name>` 复用已有 Chrome 配置文件的登录状态

## 前端服务生命周期

```
Round 开始
  → 检测是否需要前端验证
  → 是：启动前端开发服务器（后台）
  → 等待端口就绪（轮询，最多30秒）
  → 执行 agent-browser 验证
  → 关闭开发服务器
```

### 端口探测

1. 优先读配置（vite.config 的 server.port / next.config / package.json）
2. 读不到 → 默认尝试 5173 (vite) / 3000 (next/cra) / 8080 (vue-cli)
3. 后台运行 `npm run dev`
4. 轮询目标端口，最多30秒，间隔2秒
5. 失败三分支: 进程崩溃 → 读 stderr → 修代码 / 端口被占用 → 复用或换端口 / 30s未就绪 → 阻塞汇报

## 样本对照协议（F5）

有样本 URL 时启用:

1. **摄入(Step①)**: agent_browser_open(样本URL) → agent_browser_snapshot → 保存基准结构到 `loop-screenshots/sample-<name>.yml`
2. **对照(F5)**: 双开 snapshot → 逐区块比对(存在性/层级/元素类型)；也可用 `agent_browser_diff_snapshot` 自动检测变化
3. **判定**:
   - 客观项(区块缺失/元素类型错) → 自动判定，缺失进自愈
   - 主观项(配色/间距/风格) → 标记"🎨 设计待确认"，不自动改

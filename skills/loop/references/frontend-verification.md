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
  browser_navigate(targetUrl) → browser_snapshot
  → 断言: 页面标题/路由正确, 无全局错误边界

阶段2: 三件套采集 + 自动断言
  console = browser_console_messages(level=error)
  network = browser_network_requests()
  snapshot = 阶段1的结构
  → 自动断言（见判定表）

阶段3: 交互流执行（F4）
  对验收条件中每个用户操作流:
    snapshot → 拿ref → click/type → snapshot
    每步采集 console+network → 断言

阶段4: 汇总 → 门禁报告 F1-F4
  全绿 → 前端验证通过
  有红 → 进入自愈闭环
```

## 三件套判定表

| 信号源 | 通过判定 | 失败处置 |
|--------|---------|---------|
| `console_messages` | error 数量 = 0 | 每个 error 读堆栈 → 归类 A/B/C |
| `network_requests` | 全部 2xx/3xx | 每个 4xx/5xx 读响应体 → 归类 A/B/C |
| `snapshot` | 验收条件要求的元素全命中 | 缺失元素 → 检查渲染逻辑 → 归类 A |

**截图仅留证**: `browser_take_screenshot` 仅存档（路径 `loop-screenshots/R<轮次>-<场景>.png`），不作为通过判据。

## Playwright MCP 工具

| 工具 | 用途 |
|------|------|
| `browser_navigate` | 导航到指定 URL |
| `browser_snapshot` | 获取页面 accessibility tree |
| `browser_click` | 点击元素（通过 ref 定位） |
| `browser_type` | 填写输入框内容 |
| `browser_take_screenshot` | 截图留证（不作为判据） |
| `browser_console_messages` | 读取控制台日志（**判据**） |
| `browser_network_requests` | 读取网络请求（**判据**） |
| `browser_select_option` / `browser_press_key` | 表单交互（按需） |

## Ref 失效规则

- ref（如 @a1B）是某次 snapshot 的产物，仅在该页面状态下有效
- 以下情况后旧 ref 立即失效，必须重新 `browser_snapshot`:
  ① 执行过 `browser_navigate` / `browser_click` / `browser_type`(submit) 后
  ② 页面发生路由跳转后
  ③ 任何超过 1 次连续交互之间
- **标准交互序列**: snapshot → 拿ref → click/type → snapshot → 拿新ref → click/type → ...

## 登录态处理

Playwright MCP 默认不保持登录态。涉及需要登录的功能：
- **方案 A（推荐）**: 验证脚本内置登录步骤，每轮自行完成登录后测目标功能
- **方案 B（持久化）**: ZCode config 的 playwright MCP `args` 加 `--user-data-dir=<固定目录>`

## 前端服务生命周期

```
Round 开始
  → 检测是否需要前端验证
  → 是：启动前端开发服务器（后台）
  → 等待端口就绪（轮询，最多30秒）
  → 执行 Playwright 验证
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

1. **摄入(Step①)**: browser_navigate(样本URL) → snapshot → 保存基准结构到 `loop-screenshots/sample-<name>.yml`
2. **对照(F5)**: 双开 snapshot → 逐区块比对(存在性/层级/元素类型)
3. **判定**:
   - 客观项(区块缺失/元素类型错) → 自动判定，缺失进自愈
   - 主观项(配色/间距/风格) → 标记"🎨 设计待确认"，不自动改

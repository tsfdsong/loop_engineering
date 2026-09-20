# Visual Companion 指南（可视化伴侣）

基于浏览器的视觉头脑风暴伴侣，用于展示 mockup、图表与选项。

## 何时使用

**逐问题决定，不逐会话决定。** 判断标准：**这个问题看图比读字更容易懂吗？**

**用浏览器**——当内容本身是视觉的：

- **UI mockup** —— 线框、布局、导航结构、组件设计
- **架构图** —— 系统组件、数据流、关系图
- **并排视觉对比** —— 两种布局、两套配色、两个设计方向
- **设计打磨** —— 问题关乎观感、间距、视觉层级时
- **空间关系** —— 状态机、流程图、实体关系渲染成图

**用终端**——当内容是文字或表格：

- **需求与范围问题** —— "X 是什么意思？"、"哪些功能在范围内？"
- **概念性 A/B/C 选择** —— 在文字描述的方案间挑选
- **Trade-off 清单** —— 优缺点、对比表
- **技术决策** —— API 设计、数据建模、架构方案选型
- **澄清问题** —— 答案是文字而非视觉偏好的任何问题

UI 主题的问题不自动等于视觉问题。"你想要什么样的向导？"是概念问题——用终端。"这几个向导布局哪个感觉对？"是视觉问题——用浏览器。

## 工作原理

服务器监视目录中的 HTML 文件，把最新的推给浏览器。你把 HTML 写进 `screen_dir`，用户在浏览器看到并可点击选择。选择被记录到 `state_dir/events`，你下一轮读取。

**内容片段 vs 完整文档：** 若你的 HTML 以 `<!DOCTYPE` 或 `<html` 开头，服务器原样提供（只注入 helper 脚本）。否则服务器自动把你的内容包进 frame 模板——加头部、CSS 主题、选择指示器与全部交互基础设施。**默认写内容片段。** 只有需要完全控制页面时才写完整文档。

## 启动会话

```bash
# Start server with persistence (mockups saved to project)
scripts/start-server.sh --project-dir /path/to/project

# Returns: {"type":"server-started","port":52341,"url":"http://localhost:52341",
#           "screen_dir":"/path/to/project/.superpowers/brainstorm/12345-1706000000/content",
#           "state_dir":"/path/to/project/.superpowers/brainstorm/12345-1706000000/state"}
```

保存响应中的 `screen_dir` 与 `state_dir`。让用户打开 URL。

**找连接信息：** 服务器把启动 JSON 写到 `$STATE_DIR/server-info`。若你在后台启动且没抓到 stdout，读该文件拿 URL 和端口。用了 `--project-dir` 时，查 `<project>/.superpowers/brainstorm/` 找会话目录。

**注意：** 把项目根传给 `--project-dir`，mockup 持久化到 `.superpowers/brainstorm/`、服务器重启后仍在。不传则文件进 `/tmp`、会被清理。提醒用户把 `.superpowers/` 加进 `.gitignore`（若还没有）。

**按平台启动服务器：**

**Claude Code（macOS / Linux）：**
```bash
# Default mode works — the script backgrounds the server itself
scripts/start-server.sh --project-dir /path/to/project
```

**Claude Code（Windows）：**
```bash
# Windows auto-detects and uses foreground mode, which blocks the tool call.
# Use run_in_background: true on the Bash tool call so the server survives
# across conversation turns.
scripts/start-server.sh --project-dir /path/to/project
```
经 Bash 工具调用时设 `run_in_background: true`。下一轮读 `$STATE_DIR/server-info` 拿 URL 和端口。

**Codex：**
```bash
# Codex reaps background processes. The script auto-detects CODEX_CI and
# switches to foreground mode. Run it normally — no extra flags needed.
scripts/start-server.sh --project-dir /path/to/project
```

**Gemini CLI：**
```bash
# Use --foreground and set is_background: true on your shell tool call
# so the process survives across turns
scripts/start-server.sh --project-dir /path/to/project --foreground
```

**其他环境：** 服务器必须在会话轮次间保持后台运行。若你的环境会回收分离进程，用 `--foreground` 并以你平台的后台机制启动。

URL 从浏览器不可达时（远程/容器环境常见），绑定非回环地址：

```bash
scripts/start-server.sh \
  --project-dir /path/to/project \
  --host 0.0.0.0 \
  --url-host localhost
```

用 `--url-host` 控制返回 URL JSON 里打印的主机名。

## 循环

1. **确认服务器存活**，然后**写 HTML** 到 `screen_dir` 的新文件：
   - 每次写之前，确认 `$STATE_DIR/server-info` 存在。不存在（或 `$STATE_DIR/server-stopped` 存在）= 服务器已停——先 `start-server.sh` 重启再继续。服务器闲置 30 分钟自动退出。
   - 用语义化文件名：`platform.html`、`visual-style.html`、`layout.html`
   - **绝不复用文件名** —— 每屏一个新文件
   - 用 Write 工具 —— **绝不用 cat/heredoc**（往终端倒噪音）
   - 服务器自动提供最新文件

2. **告诉用户会看到什么，然后结束你的回合：**
   - 每步都提醒 URL（不只是第一次）
   - 一句话概述屏幕上是什么（如"正在展示首页的 3 种布局选项"）
   - 请他们在终端回应："看看然后告诉我你的想法。愿意的话可以点选一个选项。"

3. **下一轮** —— 用户在终端回应后：
   - `$STATE_DIR/events` 存在就读 —— 里面是用户浏览器交互（点击、选择）的 JSON 行
   - 与用户终端文字合并得到完整画面
   - 终端消息是主反馈；`state_dir/events` 提供结构化交互数据

4. **迭代或前进** —— 反馈改变了当前屏就写新文件（如 `layout-v2.html`）。当前步验证通过才进下一问。

5. **回到终端时卸载** —— 下一步不需要浏览器时（如澄清问题、trade-off 讨论），推一个等待屏清掉过期内容：

   ```html
   <!-- filename: waiting.html (or waiting-2.html, etc.) -->
   <div style="display:flex;align-items:center;justify-content:center;min-height:60vh">
     <p class="subtitle">Continuing in terminal...</p>
   </div>
   ```

   防止用户盯着已解决的选项而对话早已前进。下一个视觉问题出现时照常推新内容文件。

6. 重复直到完成。

## 写内容片段

只写页面内的内容。服务器自动包进 frame 模板（头部、主题 CSS、选择指示器与全部交互基础设施）。

**最小示例：**

```html
<h2>Which layout works better?</h2>
<p class="subtitle">Consider readability and visual hierarchy</p>

<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>Single Column</h3>
      <p>Clean, focused reading experience</p>
    </div>
  </div>
  <div class="option" data-choice="b" onclick="toggleSelect(this)">
    <div class="letter">B</div>
    <div class="content">
      <h3>Two Column</h3>
      <p>Sidebar navigation with main content</p>
    </div>
  </div>
</div>
```

就这样。不需要 `<html>`、CSS、`<script>` 标签。服务器全提供。

## 可用 CSS 类

frame 模板为你的内容提供这些类：

### 选项（A/B/C 选择）

```html
<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>Title</h3>
      <p>Description</p>
    </div>
  </div>
</div>
```

**多选：** 容器加 `data-multiselect` 允许多选。每次点击切换选中项。指示条显示计数。

```html
<div class="options" data-multiselect>
  <!-- same option markup — users can select/deselect multiple -->
</div>
```

### 卡片（视觉设计）

```html
<div class="cards">
  <div class="card" data-choice="design1" onclick="toggleSelect(this)">
    <div class="card-image"><!-- mockup content --></div>
    <div class="card-body">
      <h3>Name</h3>
      <p>Description</p>
    </div>
  </div>
</div>
```

### Mockup 容器

```html
<div class="mockup">
  <div class="mockup-header">Preview: Dashboard Layout</div>
  <div class="mockup-body"><!-- your mockup HTML --></div>
</div>
```

### 分栏视图（并排）

```html
<div class="split">
  <div class="mockup"><!-- left --></div>
  <div class="mockup"><!-- right --></div>
</div>
```

### 优缺点

```html
<div class="pros-cons">
  <div class="pros"><h4>Pros</h4><ul><li>Benefit</li></ul></div>
  <div class="cons"><h4>Cons</h4><ul><li>Drawback</li></ul></div>
</div>
```

### Mock 元素（线框构建块）

```html
<div class="mock-nav">Logo | Home | About | Contact</div>
<div style="display: flex;">
  <div class="mock-sidebar">Navigation</div>
  <div class="mock-content">Main content area</div>
</div>
<button class="mock-button">Action Button</button>
<input class="mock-input" placeholder="Input field">
<div class="placeholder">Placeholder area</div>
```

### 排版与小节

- `h2` —— 页面标题
- `h3` —— 小节标题
- `.subtitle` —— 标题下次要文字
- `.section` —— 带下边距的内容块
- `.label` —— 小号大写标签文字

## 浏览器事件格式

用户在浏览器点击选项时，交互记录到 `$STATE_DIR/events`（每行一个 JSON 对象）。你推送新屏时文件自动清空。

```jsonl
{"type":"click","choice":"a","text":"Option A - Simple Layout","timestamp":1706000101}
{"type":"click","choice":"c","text":"Option C - Complex Grid","timestamp":1706000108}
{"type":"click","choice":"b","text":"Option B - Hybrid","timestamp":1706000115}
```

完整事件流显示用户的探索路径——定下来之前可能点多个选项。最后一个 `choice` 事件通常是最终选择，但点击模式可能暴露犹豫或值得追问的偏好。

`$STATE_DIR/events` 不存在 = 用户没碰浏览器——只用终端文字。

## 设计技巧

- **保真度随问题伸缩** —— 布局问题用线框，打磨问题才做打磨
- **每页解释清楚问题** —— "哪种布局更专业？"而不是"选一个"
- **先迭代再前进** —— 反馈改当前屏就写新版本
- 每屏**最多 2-4 个选项**
- **该用真实内容时就用** —— 摄影作品集就放真图（Unsplash）。占位内容会掩盖设计问题
- **mockup 保持简单** —— 聚焦布局与结构，不做像素级设计

## 文件命名

- 用语义名：`platform.html`、`visual-style.html`、`layout.html`
- 绝不复用文件名——每屏必须新文件
- 迭代加版本后缀：`layout-v2.html`、`layout-v3.html`
- 服务器按修改时间提供最新文件

## 清理

```bash
scripts/stop-server.sh $SESSION_DIR
```

会话用了 `--project-dir` 时，mockup 文件留在 `.superpowers/brainstorm/` 供日后参考。只有 `/tmp` 会话在停止时被删。

## 参考

- frame 模板（CSS 参考）：`scripts/frame-template.html`
- helper 脚本（客户端）：`scripts/helper.js`

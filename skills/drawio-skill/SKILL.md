---
name: drawio-skill
version: 1.14.0
description: |
  TRIGGER: 创建图表 / 流程图 / 架构图 / ER / UML / 时序图 / 网络拓扑 / ML 模型图 / 思维导图 / '画图' / '流程图' / '架构图' / '时序图' / 'diagram' / 'flowchart'（不用于：文本解释，生成代码用 python-web-development）
  RULE: no specific rule（方法论 skill · 制图工具）
  DETAIL: 本 SKILL.md（drawio CLI + 自检 + 可选自动布局）
license: MIT
homepage: https://github.com/Agents365-ai/drawio-skill
compatibility: Requires draw.io desktop app CLI on PATH (macOS/Linux/Windows). Self-check step requires a vision-enabled model (e.g., Claude Sonnet/Opus); gracefully skipped if unavailable. Optional auto-layout (scripts/autolayout.py) needs Graphviz (dot).
platforms: [macos, linux, windows]
---

# Draw.io Diagrams

## Overview（概述）

用原生 draw.io 桌面版 CLI 生成 `.drawio` XML 文件并在本地导出 PNG/SVG/PDF/JPG。

**支持格式：** PNG、SVG、PDF、JPG —— 无需浏览器自动化。

PNG、SVG、PDF 导出支持 `--embed-diagram`（`-e`）—— 导出文件内嵌完整图表 XML，在 draw.io 中打开即可恢复可编辑图表。用双扩展名（`name.drawio.png`）标示内嵌 XML。

## 何时用 / 何时不用

**用本技能：** 精致、精确的图表（架构、网络、严格 UML、ERD）、需要实心不透明填充的、需要 10000+ 内置/品牌形状、泳道或自定义几何的、要导出为可编辑 PNG/SVG/PDF 的场景。

**不用 —— 走别的路：**
- 随手的手绘/白板风格 → **excalidraw** 或 **tldraw**
- 图即代码（进 git / Markdown 渲染）→ **mermaid**（通用）或 **plantuml**（UML）
- 自由无限画布或手绘笔触 → **tldraw**

## 内置资源

工作流引用到以下资源时按需读取——都不需要预先放进上下文。

| 文件 | 何时读 |
|---|---|
| `references/diagram-types.md` | 用户点名具体图表类型（ERD、UML 类、时序、架构、ML/DL、流程图） |
| `references/shapes.md` + `scripts/shapesearch.py` | 图表需要**特定形状**——云图标（AWS/Azure/GCP）、Cisco/Kubernetes/网络符号、UML/BPMN/ER/电气/P&ID 元件——或任何你本来要瞎猜 `style=` 字符串的时候。`shapesearch.py "<keywords>"` 返回 10k+ 形状的精确官方 style |
| `scripts/aiicons.py` | 图表涉及 **AI/LLM 品牌**（OpenAI、Claude、Gemini、Mistral、Llama、HuggingFace、Ollama、LangChain 等）—— `aiicons.py "<brand>"` 返回该品牌 logo 的 draw.io `image` style（lobe-icons 经 CDN；`--embed` 内联）。draw.io 没有内置 AI logo。见 `references/shapes.md` → "AI / LLM brand logos" |
| `references/style-presets.md` | 用户要求学习/保存/列出/设默认/删除样式预设，或你已解析出激活的预设、需要应用规则 |
| `references/style-extraction.md` | 你在 Learn 流程内且需要提取步骤（由 style-presets.md 调用） |
| `references/troubleshooting.md` | 导出失败、vision 拒绝 PNG、渲染不对 |
| `scripts/repair_png.py` | 每次 `-e` PNG 导出后 —— 修复 draw.io 截断的 IEND chunk（issue #8） |
| `scripts/encode_drawio_url.py` | CLI 不可用、需要浏览器兜底 diagrams.net URL（`--edit` 得可编辑编辑器 URL） |
| `references/autolayout.md` | 图表大或布局重（依赖/调用图、代码结构、>~15 节点）、想让 Graphviz 摆节点+布线而不是手摆坐标 |
| `scripts/pyimports.py` · `jsimports.py` · `goimports.py` · `rustimports.py` | 用户想可视化 **Python、JS/TS、Go 或 Rust 项目**结构 —— 提取 import 图（传递归约、可选 `--group` 容器、按子包嵌套）供 autolayout |
| `scripts/pyclasses.py` | 用户想要 **Python 类继承/类图** —— 提取类 + 继承边（`--group` 按模块装箱）供 autolayout |
| `scripts/validate.py` | 你生成了 `.drawio`（尤其经 autolayout或大图手摆）并在 vision 自检前想跑一次快速确定性结构 lint（悬空边、重复/保留 id、坏 parent、重叠） |

## 前置条件

必须安装 draw.io 桌面版且 CLI 可用：

**macOS sandbox / 沙箱隔离注意（如 codex.app）：** 某些沙箱化 macOS 环境中，调用 draw.io 桌面 CLI（哪怕 `drawio --version`）可能让 draw.io 进程崩溃或无输出。若发生，把 CLI 视为**在此沙箱隔离中不可用**——不要在沙箱内反复重试。CLI 导出工作优先用**非沙箱宿主环境**（沙箱隔离外），或用浏览器兜底 / 纯 XML 输出。

```bash
# macOS (Homebrew — recommended; CLI binary is `drawio`, not `draw.io`)
brew install --cask drawio
drawio --version

# macOS (full path if not in PATH)
/Applications/draw.io.app/Contents/MacOS/draw.io --version

# Windows
"C:\Program Files\draw.io\draw.io.exe" --version

# Linux
drawio --version
```

缺失时安装 draw.io 桌面版：
- macOS：`brew install --cask drawio` 或从 https://github.com/jgraph/drawio-desktop/releases 下载
- Windows：从 https://github.com/jgraph/drawio-desktop/releases 下载安装包
- Linux：从 https://github.com/jgraph/drawio-desktop/releases 下载 `.deb`/`.rpm` —— **不要用 snap**（AppArmor 沙箱在服务器上拒绝 secrets/keyring，导致崩溃）

## 工作流

开工前评估用户请求是否足够具体。缺关键细节时问 1-3 个聚焦问题：
- **图表类型** —— 哪个预设？（ERD、UML、时序、架构、ML/DL、流程图，或通用）
- **输出格式** —— PNG（默认）、SVG、PDF 还是 JPG？
- **输出位置** —— 默认用户工作目录；用户给了显式路径就遵循（如"放 `./artifacts/`"）。没提就不问。
- **范围/精度** —— 多少组件？有特定技术或标签吗？

请求已含这些细节或明显简单（如"画个 X 的流程图"）时跳过澄清。

**Step 0 —— 解析激活的预设。** 判断是否有用户自定义样式预设适用于本次生成。

- 扫描用户消息中明确点名样式预设的短语："use my `<name>` style"、"with my `<name>` style"、"in `<name>` mode"、"in the style of `<name>`"。光秃秃的 `with <name>` **不算**——"draw a diagram with redis" 点名的是组件不是样式。清晰命中 → 激活预设 = `<name>`。
- 否则，查 `~/.drawio-skill/styles/` 中是否有 `"default": true` 的文件。有 → 激活该预设。
- 否则 → 无激活预设；工作流其余部分落入内置颜色/形状/边约定。

从 `~/.drawio-skill/styles/<name>.json` 加载预设 JSON，兜底 `<this-skill-dir>/styles/built-in/<name>.json`。两处都不存在时，告知用户该名字未知、列出可用预设（用户目录 + 内置），然后停下——**不要**静默回落到默认。

预设加载成功时，在回复第一行提及：*"Using preset `<name>` (confidence: `<level>`)."* 预设如何改变颜色/形状/边/字体决策，见下方 **Applying a preset** 小节。

1. **检查依赖** —— **解析二进制在本系统的名字**，并在本工作流后续每条命令中逐字使用。按序尝试：(a) `drawio --version`（Homebrew cask、jgraph `.deb`/`.rpm`、Arch AUR 的规范名），(b) `draw.io --version`（旧构建、某些自制 symlink、某些发行版包），(c) macOS `.app` 直调：`/Applications/draw.io.app/Contents/MacOS/draw.io --version`，(d) Windows：`"C:\Program Files\draw.io\draw.io.exe" --version`。第一个能打印版本号的就是你的二进制；记住确切路径/名字并在下方每条导出命令中替换 `drawio`。**你的二进制名字不同就不要逐字抄示例命令**——示例用 `drawio` 只因它最常见。macOS-Homebrew 上 `drawio` 只是个 exec `/Applications/draw.io.app/Contents/MacOS/draw.io` 的薄包装脚本——同一引擎，候选 (c) 只在 `drawio` 包装缺失时需要（如拖拽安装而非 cask）。
2. **规划** —— 定形状、关系、布局（LR 或 TB），按层/档分组
3. **生成** —— 把 `.drawio` XML 写入磁盘。小图/样式图手摆坐标。**大图或布局重的图（依赖/调用图、代码结构、>~15 节点）不要手摆**——把图描述为 JSON，跑 `python3 <this-skill-dir>/scripts/autolayout.py graph.json -o <name>.drawio`，让 Graphviz 计算节点位置 + 正交布线（见 `references/autolayout.md`）。**Python / JS-TS / Go / Rust 项目**用对应 importer（`scripts/pyimports.py`、`jsimports.py`、`goimports.py`、`rustimports.py`）提取 import 图（传递归约；加 `--group` 按子包装箱，深树嵌套）供 autolayout；**Python 类继承**用 `scripts/pyclasses.py` 提取类 + 继承边。生成任何 `.drawio` 后，跑 `python3 <this-skill-dir>/scripts/validate.py <name>.drawio` 做快速结构 lint（悬空边、重复 id、重叠）再导出。默认输出目录是用户工作目录；用户指定了输出路径/目录（如 `./artifacts/`、`docs/images/`）就用它——先 `mkdir -p`。步骤 4 和 7 的 PNG/SVG/PDF 导出沿用同一目录选择。
4. **导出草稿** —— 跑 CLI 出预览 PNG。**此步不要传 `-e`**——它附加的内嵌 `zTXt mxGraphModel` chunk 会让 vision API（含 Claude）在步骤 5 返回 400 "Could not process image"。**用 `--width 2000`（不是 `-s 2`）限制预览宽度**——Claude 的 vision API 拒绝大于 2576×2576px 的图（"Unable to resize image — dimensions exceed the 2576x2576px limit"），中大型图上 `-s 2` 很容易超限。干净预览存为 `<name>.png`（单扩展名）。内嵌与全分辨率缩放只属于最终导出（步骤 7）。
5. **自检** —— 用 agent 内建 vision 能力读导出的 PNG，抓明显问题、给用户看之前自动修（需 vision 模型如 Claude Sonnet/Opus）。读 PNG 返回 400 / "Could not process image" 时，几乎肯定误传了 `-e`——去掉 `-e` 重导再试一次。仍失败则跳过自检进步骤 6。
6. **评审循环** —— 给用户看图、收反馈、做针对性 XML 编辑、重导出、循环到批准
7. **最终导出** —— 把批准版重导出到全部请求格式。此处用 `-e`（PNG/SVG/PDF）让交付物在 draw.io 中保持可编辑；存为 `<name>.drawio.png` 标示内嵌 XML。**`-e` PNG 后立即跑 `python3 <this-skill-dir>/scripts/repair_png.py <name>.drawio.png`**——draw.io CLI 在 `-e` PNG 输出中截断 IEND chunk（缺 8 字节），产出 vision API 和严格 PNG 解码器都拒绝的坏文件（issue #8）。报告文件路径。

**若 `drawio --version` 崩溃或无输出（codex.app 等受限 macOS 沙箱隔离中常见）：**
- 不要在沙箱内继续重试 CLI 调用。
- 跳过步骤 4、5、6、7（CLI 导出 + 基于 PNG 的评审），改用**浏览器兜底**（`scripts/encode_drawio_url.py`）或只交付 `.drawio` XML。
- 用户需要 PNG/SVG/PDF 时，请其在**非沙箱宿主环境**（沙箱隔离外）跑导出命令并回传文件。

升级规则：
- 二进制在 PATH（或已知 app 路径存在）但执行异常退出、空输出、Electron 启动失败、显示/会话错误、疑似沙箱限制——优先做一次升级重试再兜底。
- 二进制完全缺失——不要仅为更激进地搜索而升级；直接走安装指引或兜底。

### Step 5: 自检

导出草稿 PNG 后，用 agent 的 vision 能力（如 Claude 图像输入）读图并在给用户看之前检查这些问题。agent 不支持 vision 就跳过自检、直接展示 PNG。

**重要：** 此处读的草稿 PNG 必须是**不带** `-e` 导出的。draw.io 的 `-e` 产出 IEND chunk 截断的 PNG（缺 8 字节 type+CRC），Anthropic vision API 以 400 "Could not process image" 拒绝（issue #8）。预览步骤最简单的修法是完全跳过 `-e`；步骤 7 的最终导出保留 `-e` 并跑修复脚本。此处见 400 就去掉 `-e` 重导再试一次；仍失败（其他原因）则跳过自检进步骤 6。

| 检查项 | 找什么 | 自动修动作 |
|-------|-----------------|-----------------|
| 形状重叠 | 两个以上形状叠在一起 | 把形状挪开 ≥200px |
| 标签被裁 | 文字在形状边界处被切 | 增大形状宽/高容纳标签 |
| 连接缺失 | 箭头视觉上没连到形状 | 验证 `source`/`target` id 匹配既有 cell |
| 画出画布 | 形状在负坐标或远离主体 | 移到簇附近的正坐标 |
| 边穿形状 | 一条边视觉上穿过无关形状 | 加 waypoint（`<Array as="points">`)绕行，或加大形状间距 |
| 边叠边 | 多条边在同一路径上重叠 | 在形状周边分散出入点（用不同 exitX/entryX） |

- 最多 **2 轮自检**——2 轮修复后仍有问题就直接给用户看
- 每次修复后重导出并重读新 PNG

### Step 6: 评审循环

自检后，展示导出的图并向用户征求反馈。

**针对性编辑规则** —— 每类反馈做最小 XML 改动：

| 用户要求 | XML 编辑动作 |
|-------------|----------------|
| 改 X 的颜色 | 按 `value` 匹配 X 找到 `mxCell`，更新 `style` 中的 `fillColor`/`strokeColor` |
| 加节点 | 追加新 `mxCell` vertex，用下一个可用 `id`，摆在相关节点旁 |
| 删节点 | 删除该 `mxCell` vertex 及所有 `source`/`target` 匹配的边 |
| 移动形状 X | 更新匹配 `mxCell` 的 `mxGeometry` 中 `x`/`y` |
| 调整大小 | 更新匹配 `mxCell` 的 `mxGeometry` 中 `width`/`height` |
| 加 A→B 箭头 | 追加新 `mxCell` edge，`source`/`target` 匹配 A、B 的 id |
| 改标签文字 | 更新匹配 `mxCell` 的 `value` 属性 |
| 改布局方向 | **整体重新生成** —— 按新方向重建 XML |

**规则：**
- 单元素改动：就地编辑既有 XML——保留先前迭代调好的布局
- 布局级改动（如 LR↔TB 互换、"推倒重来"）：整体重生成 XML
- 每轮覆盖同一个 `{name}.png`（不带 `-e`）——不要造 `v1`、`v2`、`v3`。`-e` 只属于步骤 7 的最终导出
- 应用编辑后重导出并展示新图
- 循环直到用户说批准 / 完成 / LGTM
- **安全阀：** 5 轮迭代后，建议用户在 draw.io 桌面版中打开 `.drawio` 做细调

### Step 7: 最终导出

用户批准后：
- 导出到全部请求格式（PNG、SVG、PDF、JPG）——未指定则默认 PNG
- 报告 `.drawio` 源文件与导出图的路径
- **自动打开：** 主动提出在 draw.io 桌面版打开 `.drawio` 细调 —— `open diagram.drawio`（macOS）、`xdg-open`（Linux）、`start`（Windows）
- 确认文件已保存可用

## Style Presets（样式预设）

**样式预设**是捕获用户视觉偏好（调色板、形状、字体、边）的命名 JSON 文件。激活时完全取代本技能的内置颜色/形状约定。

**查找顺序**（SKILL.md Step 0 解析出预设名后）：
1. `~/.drawio-skill/styles/<name>.json` —— 用户预设（`git pull` 后仍在）
2. `<this-skill-dir>/styles/built-in/<name>.json` —— 内置（`default`、`corporate`、`handdrawn`）

任何文件操作前先把用户提供的名字转小写——schema 强制小写。

**其余内容——Learn 流程（从文件提取预设）、管理操作（list/default/delete/rename）、应用规则（颜色查找、形状关键词、边、字体、附加项、与图表类型预设的交互）、校验——读 `references/style-presets.md`。** 仅当用户调用那些流程或需要把激活预设应用到本次生成时才需要。

## Draw.io XML 结构

### 文件骨架

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- user shapes start at id="2" -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

**规则：**
- `id="0"` 与 `id="1"` 是必需的根 cell——绝不省略
- 用户形状从 `id="2"` 起顺序递增
- 所有形状 `parent="1"`（容器内则用容器 id）
- 所有文字在 style 中用 `html=1` 保证正确渲染
- **绝不在 XML 注释里用 `--`**——XML 规范非法，导致解析错误
- 属性值转义特殊字符：`&amp;`、`&lt;`、`&gt;`、`&quot;`
- **标签多行文字：** `value` 属性内用 `&#xa;` 换行（不是字面 `\n`）。示例：`value="Line 1&#xa;Line 2"`

### 形状类型（vertex）

| Style 关键字 | 用途 |
|--------------|---------|
| `rounded=0` | 直角矩形（默认） |
| `rounded=1` | 圆角矩形——服务、模块 |
| `ellipse;` | 圆/椭圆——起止、数据库 |
| `rhombus;` | 菱形——判断 |
| `shape=mxgraph.aws4.resourceIcon;` | AWS 图标 |
| `shape=cylinder3;` | 圆柱——数据库 |
| `swimlane;` | 带标题栏的分组/容器 |

**厂商/品牌图标**（AWS/Azure/GCP/Cisco/Kubernetes）及任何非平凡形状，不要瞎猜 `shape=mxgraph.*` 名字——错名渲染成空白框。跑 `python3 <this-skill-dir>/scripts/shapesearch.py "<keywords>"` 拿精确官方 style + 尺寸，或看 `references/shapes.md` 的手写速查表。**AI/LLM 品牌 logo**（OpenAI、Claude、Gemini 等，draw.io 一个都没有）用 `python3 <this-skill-dir>/scripts/aiicons.py "<brand>"`。

### 必需属性

```xml
<!-- Rectangle / rounded box -->
<mxCell id="2" value="Label" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="160" height="60" as="geometry" />
</mxCell>

<!-- Cylinder (database) -->
<mxCell id="3" value="DB" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;" vertex="1" parent="1">
  <mxGeometry x="350" y="100" width="120" height="80" as="geometry" />
</mxCell>

<!-- Diamond (decision) -->
<mxCell id="4" value="Check?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
  <mxGeometry x="100" y="220" width="160" height="80" as="geometry" />
</mxCell>
```

### 容器与分组

有嵌套元素的架构图，用 draw.io 的 parent-child 包含——**不要**只是把形状摆在大形状上面。

| 类型 | Style | 何时用 |
|------|-------|-------------|
| **Group**（不可见） | `group;pointerEvents=0;` | 无需可视边框、容器自身无连接 |
| **Swimlane**（带标题） | `swimlane;startSize=30;` | 容器需要可见标题栏、或容器自身有连接 |
| **自定义容器** | 任意 shape 加 `container=1;pointerEvents=0;` | 任何充当容器但自身无连接的形状 |

**关键规则：**
- 不应截获子元素间连接的容器 style 加 `pointerEvents=0;`
- 子元素设 `parent="containerId"`，坐标**相对容器**

```xml
<!-- Swimlane container -->
<mxCell id="svc1" value="User Service" style="swimlane;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="300" height="200" as="geometry"/>
</mxCell>
<!-- Child inside container — coordinates relative to parent -->
<mxCell id="api1" value="REST API" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="svc1">
  <mxGeometry x="20" y="40" width="120" height="60" as="geometry"/>
</mxCell>
<mxCell id="db1" value="Database" style="shape=cylinder3;whiteSpace=wrap;html=1;" vertex="1" parent="svc1">
  <mxGeometry x="160" y="40" width="120" height="60" as="geometry"/>
</mxCell>
```

### 连接器（edge）

**关键：** 每个 edge `mxCell` 必须含 `<mxGeometry relative="1" as="geometry" />` 子元素。自闭合的 edge cell（`<mxCell ... edge="1" ... />`）**无效**、不渲染。永远用展开形式。

```xml
<!-- Directed arrow — always include rounded, orthogonalLoop, jettySize for clean routing -->
<mxCell id="10" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="2" target="3">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Arrow with label + explicit entry/exit points to control direction -->
<mxCell id="11" value="HTTP/REST" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="2" target="4">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Arrow with waypoints — use when edge must route around other shapes -->
<mxCell id="12" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="3" target="5">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="500" y="50" />
    </Array>
  </mxGeometry>
</mxCell>
```

**边样式规则：**
- **动画连线：** 任意边 style 加 `flowAnimation=1;` 显示沿箭头移动的光点动画。SVG 导出与 draw.io 桌面均有效——数据流/管线图理想之选。示例：`style="edgeStyle=orthogonalEdgeStyle;flowAnimation=1;rounded=1;..."`
- **永远**包含 `rounded=1;orthogonalLoop=1;jettySize=auto`——启用避重叠的智能布线
- 一个节点有 2+ 连接时，每条边都钉 `exitX/exitY/entryX/entryY`——把线分散到形状周边
- 边必须绕过中间形状时加 `<Array as="points">` waypoint
- **给箭头留空间：** 最后一个拐弯与目标形状之间的末段直线必须 ≥20px。太短则箭头叠在拐弯上、看起来坏了。加大节点间距或加显式 waypoint 修复

### 在形状上分散连接

多条边连同一形状时，分配不同出入点防叠：

| 位置 | exitX/entryX | exitY/entryY | 何时用 |
|----------|-------------|-------------|----------|
| 顶中 | 0.5 | 0 | 连上方节点 |
| 左上 | 0.25 | 0 | 自上第 2 连接 |
| 右上 | 0.75 | 0 | 自上第 3 连接 |
| 右中 | 1 | 0.5 | 连右侧节点 |
| 底中 | 0.5 | 1 | 连下方节点 |
| 左中 | 0 | 0.5 | 连左侧节点 |

**规则：** 一侧有 N 个连接就均分（如底部 3 连接 → exitX = 0.25、0.5、0.75）

### 调色板（fillColor / strokeColor）

*仅在无激活预设时使用（见上方 "Applying a preset"）。*

| 颜色 | fillColor | strokeColor | 用途 |
|-----------|-----------|-------------|---------|
| 蓝 | `#dae8fc` | `#6c8ebf` | 服务、客户端 |
| 绿 | `#d5e8d4` | `#82b366` | 成功、数据库 |
| 黄 | `#fff2cc` | `#d6b656` | 队列、判断 |
| 橙 | `#ffe6cc` | `#d79b00` | 网关、API |
| 红/粉 | `#f8cecc` | `#b85450` | 错误、告警 |
| 灰 | `#f5f5f5` | `#666666` | 外部/中性 |
| 紫 | `#e1d5e7` | `#9673a6` | 安全、认证 |

### 布局技巧

**间距——随复杂度伸缩：**

| 图表复杂度 | 节点 | 水平间距 | 垂直间距 |
|-------------------|-------|----------------|--------------|
| 简单 | ≤5 | 200px | 150px |
| 中等 | 6–10 | 280px | 200px |
| 复杂 | >10 | 350px | 250px |

**布线走廊：** 形状行/列之间留约 80px 空走廊供边穿行不穿形状。绝不把形状放在边需要穿过的空档里。

**网格对齐：** 所有 `x`、`y`、`width`、`height` 取 **10 的倍数**——保证在 draw.io 默认网格上干净对齐、便于手改。

**通用规则：**
- 分配 x/y 前先规划网格——先在纸上/脑中勾出节点位置
- 相关节点放同一水平或垂直带
- 逻辑分组用带可见边框的 `swimlane`
- 连接多的"枢纽"节点放中心，让边向外辐射而非交叉
- 强制垂直直线连接时，在边上显式钉出入点：
  `exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0`
- 子节点永远与父节点中心对齐（同 center x）避免斜线
- **事件总线模式：** Kafka/总线节点放在**服务行的中心**而非下方——两侧服务用短水平箭头即可达（左侧 `exitX=1`、右侧 `exitX=0`），消灭所有交叉线
- 水平连接（`exitX=1` 或 `exitX=0`）永不穿过同行竖直节点；用于对等连接与发布连接

**避免边穿形状：**
- 定坐标前脑中走一遍每条边——必穿无关形状时，移形状或加 waypoint
- 树/层级布局：节点分层（行），只在相邻层之间连接，减少交叉
- 星型/枢纽布局：枢纽居中、卫星环绕——边短且呈辐射状
- 边必须跨多行/列时，沿外围走廊走，不穿图中间

## 导出

### 命令

有**两种**导出模式：

- **预览/自检**（工作流步骤 4）——不带 `-e`。输出 `diagram.png`。vision 自检必需；此处用 `-e` 会触发 vision API 400 "Could not process image"（issue #8）。
- **最终/交付**（步骤 7）——传 `-e`。输出 `diagram.drawio.png`。内嵌 XML 保持文件在 draw.io 中可编辑。

> 下方命令中 `drawio` 是你在 Step 1 解析出的二进制名的占位符。你的二进制在 PATH 上叫 `draw.io`（带点——旧版或发行版打包）就全程替换之。只有 macOS `.app` 或 Windows `.exe` 可用时，用下方完整路径变体。

```bash
# Preview PNG (use this in step 4, before self-check) — NO -e, width-capped to stay under vision's 2576px ceiling
drawio -x -f png --width 2000 -o diagram.png input.drawio

# Final PNG (step 7, after user approval) — WITH -e, double extension
drawio -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# macOS — full path (if not in PATH); preview / final variants
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png --width 2000 -o diagram.png input.drawio
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# Windows
"C:\Program Files\draw.io\draw.io.exe" -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# Linux (headless — requires xvfb-run; on servers add HOME and --disable-gpu)
export HOME=${HOME:-/tmp}
xvfb-run -a --server-args="-screen 0 1280x1024x24" \
  drawio -x -f png -e -s 2 -o diagram.drawio.png input.drawio --disable-gpu
# Running as root (CI / Docker)? Append --no-sandbox AT THE END (placing it earlier makes drawio treat it as the input filename)

# SVG export (final — -e is safe; SVG is text)
drawio -x -f svg -e -o diagram.svg input.drawio

# PDF export (final)
drawio -x -f pdf -e -o diagram.pdf input.drawio

# Custom output directory (e.g. CI artifacts dir) — create if missing, then export there
mkdir -p ./artifacts && drawio -x -f png -e -s 2 -o ./artifacts/diagram.drawio.png input.drawio
```

### 导出后 PNG 修复（`-e` PNG 导出后必需）

draw.io CLI 在产出 `-e` PNG 时截断 IEND chunk——文件以 4 字节 IEND 长度字段结尾，但 `IEND` 类型 + CRC（8 字节）缺失。后果：vision API 返回 400 "Could not process image"、严格 PNG 解码器报错。SVG/PDF 不受影响。

每次 `-e` PNG 导出后立即跑：

```bash
python3 <this-skill-dir>/scripts/repair_png.py diagram.drawio.png
```

脚本的 `endswith(IEND)` 守卫使其在 draw.io 上游修好后自动变 no-op——无条件运行也安全。

**关键 flag：**
- `-x` —— 导出模式（必需）
- `-f` —— 格式：`png`、`svg`、`pdf`、`jpg`
- `-e` —— 输出内嵌图表 XML（PNG、SVG、PDF）——导出文件在 draw.io 中保持可编辑。**步骤 5 自检的预览 PNG 跳过**——`-e` PNG 的 IEND 截断会被 vision API 拒绝（issue #8）。最终 PNG 保留 `-e` 并跑 `scripts/repair_png.py`（见导出后修复）。SVG/PDF 不受影响
- `-s` —— 缩放：`1`、`2`、`3`（最终 PNG 推荐 2；步骤 4 预览**不要用**——见 `--width`）
- `--width <px>` —— 目标宽度像素（无短形式；`-w` **不存在**且会静默弄坏输入文件解析器）。步骤 4 预览用 `--width 2000` 保证 PNG 不超 Claude vision 的 2576×2576 上限。另有 `--height <px>` 供细高图用。不要与 `-s` 合用
- `-o` —— 输出文件路径；接受任意目录（如 `./artifacts/diagram.drawio.png`）——先 `mkdir -p`。内嵌时用 `.drawio.png` 双扩展名
- `-b` —— 图外边距（默认 0，推荐 10）
- `-t` —— 透明背景（仅 PNG）
- `--page-index 0` —— 导出指定页（默认全部）

### 浏览器兜底（无需 CLI）

draw.io 桌面 CLI 不可用时，生成客户端 URL：

```bash
python3 <this-skill-dir>/scripts/encode_drawio_url.py input.drawio          # read-only viewer
python3 <this-skill-dir>/scripts/encode_drawio_url.py --edit input.drawio    # opens in the editor
```

默认打印 `https://viewer.diagrams.net/...#R…` 查看器 URL；`--edit` 打印直接进入可编辑编辑器的 `https://app.diagrams.net/...#create=…` URL。两种方式下图表 XML 都经 `encodeURIComponent` 编码、deflate 压缩、base64 进 URL fragment——fragment（`#` 之后）永不发给服务器，零上传。`encodeURIComponent` 步骤是强制的：没有它，任何含字面 `%` 或非 ASCII（如 CJK）标签的图会让浏览器抛 "URI malformed"、图永远打不开。

用 `open "$URL"`（macOS）/ `xdg-open "$URL"`（Linux）打开 URL。**WSL2 / Windows** 上 `cmd.exe` 会丢 `#fragment`——改写一个 `.url` 快捷方式文件再打开（见 `references/troubleshooting.md` → "WSL2 / Windows specifics"）。

### 兜底链

工具不可用时优雅降级：

| 场景 | 行为 |
|----------|----------|
| draw.io CLI 缺失、Python 可用 | 用浏览器兜底（diagrams.net URL） |
| draw.io CLI 缺失、Python 缺失 | 只生成 `.drawio` XML；指引用户在 draw.io 桌面版或 diagrams.net 手动打开 |
| draw.io CLI 在 macOS 沙箱隔离中崩溃/无输出 | 视 CLI 为沙箱内不可用；用浏览器兜底 / 纯 XML；请用户在非沙箱宿主环境跑 CLI 导出 |
| vision 不可用做自检 | 跳过自检（步骤 5）；直接给用户看导出的 PNG |
| 导出失败（Chromium/显示问题） | Linux 上用 `xvfb-run -a` 重试；仍失败则交付 `.drawio` XML 并建议手动导出 |
| Linux 服务器（headless）导出失败 | 按序尝试：(1) `xvfb-run -a`，(2) root 时在**末尾**追加 `--no-sandbox`，(3) 加 `--disable-gpu`，(4) `export HOME=/tmp`，(5) 装 apt 依赖（`libgtk-3-0 libnotify4 libnss3 libgbm1 libasound2t64` 等），(6) 兜底 [tomkludy/drawio-renderer](https://hub.docker.com/r/tomkludy/drawio-renderer) Docker（headless 导出 REST API） |

### 检查 drawio 是否在 PATH

```bash
# Prefer the Homebrew / Linux-package binary name (no dot)
if command -v drawio &>/dev/null; then
  DRAWIO="drawio"
# Fall back to the dot-named binary (older installs, manual symlinks)
elif command -v draw.io &>/dev/null; then
  DRAWIO="draw.io"
# macOS .app bundle (binary inside the bundle keeps the dot)
elif [ -f "/Applications/draw.io.app/Contents/MacOS/draw.io" ]; then
  DRAWIO="/Applications/draw.io.app/Contents/MacOS/draw.io"
# WSL2: the CLI is the Windows desktop exe, reached via /mnt/c (note the space)
elif grep -qi microsoft /proc/version 2>/dev/null && [ -f "/mnt/c/Program Files/draw.io/draw.io.exe" ]; then
  DRAWIO="/mnt/c/Program Files/draw.io/draw.io.exe"
else
  echo "drawio not found — install from https://github.com/jgraph/drawio-desktop/releases (Homebrew: brew install --cask drawio)"
fi
```

**WSL2 / 原生 Windows** 上打开导出文件与浏览器兜底 URL 需要路径转换 + `.url` 文件 workaround（`cmd.exe` 丢 URL `#fragment`）——见 `references/troubleshooting.md` 的 "WSL2 / Windows specifics" 节。

## Common Mistakes

出问题时（导出失败、vision 拒绝 PNG、布局坏、边乱走），看 `references/troubleshooting.md` 的逐行"错误 → 修复"表。

## 图表类型预设

用户请求特定图表类型时，读 `references/diagram-types.md` 取对应预设（形状、边、布局方向）。按用户措辞选择：

| 用户说 | `references/diagram-types.md` 中的节 |
|---|---|
| "ER diagram"、"schema diagram"、"data model" | ERD |
| "UML class diagram"、"class diagram" | UML Class |
| "sequence diagram"、"interaction diagram"、"lifeline" | Sequence |
| "architecture"、"system diagram"、"service diagram" | Architecture |
| "neural network"、"model architecture"、"ML diagram"、"deep learning" | ML / Deep Learning Model |
| "flowchart"、"decision tree"、"process flow" | Flowchart |

图表类型预设设定**结构性** style 关键字。若用户样式预设也激活（见 `## Style Presets`），保留结构关键字、把颜色/字体/边/附加项叠上去——合并规则见 `references/style-presets.md` → "Interaction with diagram-type presets"。

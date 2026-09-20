# Style Presets —— 学习、应用、管理

**样式预设**是捕获用户视觉偏好的命名 JSON 文件——调色板、形状词汇、字体、边样式。预设激活时，完全取代 SKILL.md 颜色/形状/边表中的内置约定。

何时读本文：
- 用户要求从文件"学习 / 保存 / 记住 / 提取"样式
- 用户想管理既有预设（列出、设默认、删除、重命名）
- 你在 Step 0 解析出了激活预设、需要应用规则
- 加载前需要校验预设文件

## 位置与查找顺序

1. `~/.drawio-skill/styles/<name>.json` —— 用户预设（`git pull` 后仍在）。
2. `<this-skill-dir>/styles/built-in/<name>.json` —— 技能内置（`default`、`corporate`、`handdrawn`）。

同名时用户预设遮蔽内置。

只有用户预能有 `"default": true`。用户说*"把 `<内置名>` 设为我的默认"*时，先把内置 JSON 复制到 `~/.drawio-skill/styles/<name>.json`，再在副本上设 `default: true`——内置文件本身不动。

**名字规范化：** 写入或查找文件前，用户提供的名字一律转小写（预设 schema 强制小写；大写名过不了校验）。

## 应用预设

SKILL.md 的 Step 0 识别出预设后，它完全取代本次制图的内置调色板、形状关键字、边默认值与字体——不要混入内置颜色表的值。

**颜色查找。** 对形状扮演的每个角色（service / database / queue / gateway / error / external / security），先由 `preset.roles[role]` 解析出槽名，再由 `preset.palette[<槽>]` 得 `(fillColor, strokeColor)` 对。`roles[role]` 未设或解析出的槽为 `null` 时，走回退阶梯：

1. 试角色的规范槽（`service→primary`、`database→success`、`queue→warning`、`gateway→accent`、`error→danger`、`external→neutral`、`security→secondary`）。
2. 该槽也空，选预设中填充数最多的非空槽。
3. 绝不回内置颜色表——预即是权威。

**判断与容器形状**不在 `preset.roles` 里——它们有形状词汇（`preset.shapes.decision`、`preset.shapes.container`）但无角色到槽的映射。取色如下：
- **判断**（菱形）→ 用 `preset.palette.warning`（内置约定中的规范黄槽）。`warning` 空则从 `warning` 起走上面的槽回退阶梯。
- **容器**（swimlane）→ 用容器所代表层/分组对应的调色板槽（如"Services"层容器用 `primary`；"Data"层用 `success`）。无层信号时默认 `primary`。

**形状关键字。** 用 `preset.shapes[role]` 作 vertex style 串的**前缀**（在 `whiteSpace=wrap;html=1;...` 之前）。例：database 角色，若 `preset.shapes.database = "shape=cylinder3"`，则 vertex style 以 `shape=cylinder3;whiteSpace=wrap;html=1;fillColor=...` 开头。六个命名形状键为 `service`、`database`、`queue`、`decision`、`external`、`container`。角色 `gateway`、`error`、`security` 复用 `preset.shapes.service`，除非预设显式填了同名键。

**边。** 用 `preset.edges.style` 作基础边样式串，追加 `preset.edges.arrow`。逐边的路由键（`exitX/exitY/entryX/entryY/...`）仍按 SKILL.md 的常规路由规则添加。两形状之间的流匹配 `preset.edges.dashedFor` 中的词（用户 prompt 用了该词，或边一端的角色典型关系是"可选"）时，边样式追加 `;dashed=1`。

**字体。** 每个 vertex style 追加 `fontFamily=<preset.font.fontFamily>;fontSize=<preset.font.fontSize>`。`preset.font.titleBold` 为 `true` 时，容器头与 swimlane 标题额外加 `fontSize=<preset.font.titleFontSize>;fontStyle=1`。

**附加项。**
- `preset.extras.sketch === true` → 每个 vertex 与 edge style 追加 `sketch=1`。
- `preset.extras.globalStrokeWidth !== 1`（非 drawio 默认 1 的任何值，含 `0.5`）→ 每个 vertex 与 edge style 追加 `strokeWidth=<n>`。

**与图表类型预设的交互**（ERD / UML / 时序 / ML / 流程图）。图表类型预设设定的结构性 style 关键字必须保留（如 ERD 表依赖 `shape=table;startSize=30;container=1;childLayout=tableLayout;...`）。规则：保留图表类型预设的结构关键字，其上叠加用户预设的颜色 / 字体 / 边 / 附加项。图表类型预设硬编码的颜色（`fillColor=#dae8fc` 等）与用户预设冲突时，用户预设的颜色胜。例外：`fillColor=none` 是结构性的——不要用调色板颜色替换。

## Learn 流程

**触发语：** "learn my style from `<path>` as `<name>`"、"save this as `<name>` style"、"remember this style as `<name>`"。

**按扩展名分派：**
- `.drawio`、`.xml` → XML 路径
- `.png`、`.jpg`、`.jpeg`、`.svg`（栅格化平面图）→ 图像路径

**步骤：**

1. **加载提取参考。** 读 `references/style-extraction.md` 进上下文。
2. **提取**，按参考中的 XML 路径或图像路径流程。
3. **规范化并构建候选。** 用户提供的预设名转小写。本流程中所有文件路径都用这个规范化名。构建候选预设 JSON，写到 `/tmp/drawio-preset-<name>.json`（`<name>` 为已规范化名）。**先不要**存到 `~/.drawio-skill/styles/<name>.json`。
4. **渲染样张**，用 `references/style-extraction.md` 的样图骨架、以候选预设参数化。用主工作流同款命令导出 PNG 到 `./preset-<name>-sample.png`（`drawio -x -f png -e -s 2 -o ./preset-<name>-sample.png /tmp/drawio-preset-<name>.drawio`），然后对它跑 `repair_png.py`（渲染步骤见 `style-extraction.md`）。
5. **给用户看：**
   - 预设摘要表（调色板 hex、各角色形状、字体、边样式、附加项）。
   - 样张 PNG 路径（环境支持就内嵌图）。
   - 溯源行：`source.type`、`source.path`、`extracted_at`、`confidence`。
6. **等批准：**
   - "save" / "looks good" → 候选写入 `~/.drawio-skill/styles/<name>.json`。目录不存在则创建。删临时文件与样张 PNG。
   - "change `<field>` to `<value>`" → 改内存中的候选，重渲染，重新问。
   - "cancel" / "abort" / "no" → 删临时文件与样张；什么都不存。

**错误行为：**

| 失败 | 行为 |
|---|---|
| 源路径不存在 | 停；报告路径未找到。 |
| XML 解析失败 | 停；报解析错误；建议在 drawio 桌面版打开修复。 |
| 图像 vision 不可用 | 停；请用户换 vision 模型重跑或提供 `.drawio` 文件。 |
| 提取出 0 个 vertex / 形状 | 停；拒绝保存。 |
| 提取出 <3 组不同颜色对 | 继续；标 `confidence: "low"`（图像）或 `"medium"`（XML）；摘要中警告。 |
| 预设名与既有用户预设冲突 | 问：覆盖，还是换名。 |
| 预设名与内置预设冲突 | 存到用户目录（遮蔽内置）；警告一次。 |
| 样张渲染失败 | 照常展示摘要；注明"样张渲染失败——仍按你的确认保存"。不阻塞。 |

## 管理操作

全部自然语言——无斜杠命令。

*所有 `<name>`、`<a>`、`<b>` 参数在任何文件操作前先做名字规范化（小写）。*

| 用户说 | Agent 做 |
|---|---|
| "list my styles"、"what styles do I have"、"show me my style presets" | 读 `~/.drawio-skill/styles/` 与 `<this-skill-dir>/styles/built-in/`。打印表：`name`、`location`（user/built-in）、`source.type`、`confidence`、`default` 标记。被用户预设遮蔽的内置标出。 |
| "show my `<name>` style"、"what's in `<name>`" | 打印预设 JSON（美化）+ 一行摘要（来源、置信度、是否默认）。 |
| "make `<name>` the default"、"set `<name>` as default" | `<name>` 是用户预设：其上设 `default: true`；清掉其他有 default 的用户预设；两个文件都保存。`<name>` 是内置：先把 `<this-skill-dir>/styles/built-in/<name>.json` 复制到 `~/.drawio-skill/styles/<name>.json`，再在副本上设 `default: true`。绝不改动内置文件。 |
| "remove default"、"unset default" | 清掉持有 `default: true` 的那个用户预设。 |
| "delete `<name>`"、"remove `<name>`" | 先确认。然后 `rm ~/.drawio-skill/styles/<name>.json`。拒绝删 `<this-skill-dir>/styles/built-in/` 下的文件——建议用同名用户预设遮蔽。 |
| "rename `<a>` to `<b>`" | `mv ~/.drawio-skill/styles/<a>.json ~/.drawio-skill/styles/<b>.json`，然后更新内部 `name` 字段。`<a>` 是内置则失败（可提供复制后重命名）。 |
| "learn my style from `<path>` as `<name>`" | 转上方 Learn 流程。 |

## 预设文件校验

加载任何预设（生成或管理）时做轻量结构检查：
- 必需顶层字段齐全（`name`、`version`、`palette`、`roles`、`shapes`、`font`、`edges`）。
- `version === 1`。
- 每个已填充的调色板槽同时有 `fillColor` 与 `strokeColor`，均为 `#RRGGBB`。
- `confidence` ∈ {`"low"`、`"medium"`、`"high"`}（若存在）。

校验失败时：
- **生成期间：** 警告用户，本次制图回落内置约定，不改文件。
- **学习期间：** 拒绝保存候选；报告哪个字段失败。

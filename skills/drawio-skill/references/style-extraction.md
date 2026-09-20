# Style Extraction —— agent 参考

用户要求学习样式（"learn my style from `<path>` as `<name>`"）或提取后需要渲染样张时，由 `SKILL.md` 按需加载。

## 样图（用于批准渲染）

提取出候选预设后，用候选的调色板/形状/字体/边渲染这个七节点样张。每个角色恰好出现一次；六条边、其中一条虚线，演练 `edges.arrow`、`edges.style` 与 `edges.dashedFor`。

**布局（TB）：**
- 行 1（y=40）：`gateway` 居中于 x=340
- 行 2（y=180）：`security`（x=80）、`service`（x=340）、`queue`（x=600）
- 行 3（y=340）：`database`（x=80）、`external`（x=340）、`error`（x=600）

**模板 —— 用候选预设替换 `{{...}}` 占位符。**

角色 `R` 的 vertex style 构造为：
`<shapes[R]>;whiteSpace=wrap;html=1;fillColor=<palette[roles[R]].fillColor>;strokeColor=<palette[roles[R]].strokeColor>;fontFamily=<font.fontFamily>;fontSize=<font.fontSize>`
- `extras.sketch=true` 时，每个 vertex style 与每个 edge style 追加 `;sketch=1`。
- `extras.globalStrokeWidth !== 1`（即非 drawio 默认 1 的任何值，含 `0.5`）时，每个 vertex style 与每个 edge style 追加 `;strokeWidth=<n>`。

边 style 构造为：
`<edges.style>;<edges.arrow>`
- 逐边路由键（`exitX/entryX/...`）按下方字面量加入。
- 边 15 演练 `edges.dashedFor`：
  - `edges.dashedFor` **非空**时，用其第一个条目作边的 `value`（标签）**并**给边 style 追加 `;dashed=1`。
  - `edges.dashedFor` 为空（`[]`）时，用标签 `cross-call` 且**不**追加 `;dashed=1`——预设没有虚线约定，样张不得伪造。

**占位符展开（填 XML 时应用）：**
- `{{VSTYLE:<role>}}` 展开为上述 vertex-style 公式（`R = <role>`）。结果写字面串；不做 URL 编码。
- `{{ESTYLE}}` 展开为上述边 style 公式。
- `{{EDGE15_LABEL}}` 与 `{{EDGE15_DASH}}` 遵循上面的边 15 规则。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="Preset Sample">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Row 1: gateway -->
        <mxCell id="2" value="Gateway" style="{{VSTYLE:gateway}}" vertex="1" parent="1">
          <mxGeometry x="340" y="40" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Row 2: security | service | queue -->
        <mxCell id="3" value="Auth" style="{{VSTYLE:security}}" vertex="1" parent="1">
          <mxGeometry x="80" y="180" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="4" value="Service" style="{{VSTYLE:service}}" vertex="1" parent="1">
          <mxGeometry x="340" y="180" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="5" value="Queue" style="{{VSTYLE:queue}}" vertex="1" parent="1">
          <mxGeometry x="600" y="180" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Row 3: database | external | error -->
        <mxCell id="6" value="Database" style="{{VSTYLE:database}}" vertex="1" parent="1">
          <mxGeometry x="80" y="340" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="7" value="External API" style="{{VSTYLE:external}}" vertex="1" parent="1">
          <mxGeometry x="340" y="340" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8" value="Error Sink" style="{{VSTYLE:error}}" vertex="1" parent="1">
          <mxGeometry x="600" y="340" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Edges -->
        <mxCell id="10" value="" style="{{ESTYLE}};exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="2" target="3">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="11" value="" style="{{ESTYLE}};exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="2" target="4">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="12" value="" style="{{ESTYLE}};exitX=0.75;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="2" target="5">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="13" value="" style="{{ESTYLE}};exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="7">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="14" value="" style="{{ESTYLE}};exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="6">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="15" value="{{EDGE15_LABEL}}" style="{{ESTYLE}}{{EDGE15_DASH}};exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="8">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### 渲染样张

1. 填好的 XML 写到 `/tmp/drawio-preset-<name>.drawio`。
2. 跑主工作流同款命令 `drawio -x -f png -e -s 2 -o <preset-name>-sample.png <tmp>.drawio`（二进制不叫 `drawio` 时替换为 SKILL.md Step 1 解析的名字）。
3. 修 IEND chunk：`python3 <this-skill-dir>/scripts/repair_png.py <preset-name>-sample.png` —— `-e` 会像主工作流步骤 7 那样截断 PNG，样张需要同样修复才可读。
4. PNG 存为 `./preset-<name>-sample.png`（用户工作目录）。
5. 给用户看：预设摘要表 + PNG 路径 + 溯源/置信度行。

### 批准循环

- "save" / "looks good" → 候选写入 `~/.drawio-skill/styles/<name>.json`；删临时文件与样张 PNG。
- "change <field> to <value>" → 改内存中的候选；重渲染；重新问。
- "cancel" → 删临时文件与样张 PNG；不保存。

### 样张渲染失败时（draw.io CLI 缺失 / 导出报错）

照常展示摘要表与溯源行，注明：*"样张 PNG 渲染失败（CLI 不可用）。你确认后仍可保存。"* 不阻塞。

## XML 提取路径

输入：`.drawio` 文件路径。输出：候选预设 JSON。确定性的，无 LLM 推断。

### 步骤

1. **解析文件。** 读 XML，收集每个带 `style=` 属性的 `<mxCell>`，分成 vertex（`vertex="1"`）与 edge（`edge="1"`）。
2. **逐个 `style=` 串按 `;` 切词。** 每个元素要么是 `key=value` 要么是裸关键字（如 `rhombus`、`ellipse`、`rounded=1`）。
3. **提取调色板。** 对每个 vertex 取 `(fillColor, strokeColor)` 对（两者皆无则跳过）。计频。保留前 ≤7 对。
4. **提取形状词汇 + 角色映射。** 对每个 vertex 按优先级判定形状类：
   `cylinder3 > ellipse > rhombus > swimlane > rounded=1 > rounded=0`。
   然后从 vertex 的形状类与 `value`（标签）属性推断语义角色。**按序评估下列规则；首个命中胜。**
   - `cylinder3` → `database`
   - `rhombus` → `decision`
   - `swimlane` → `container`
   - 有 `dashed=1` + **灰色系填充**（R、G、B 三通道彼此都在 ±16 内，即近消色差）→ `external`
   - 标签匹配 `/queue|bus|kafka|rabbit/i` → `queue`
   - 标签匹配 `/gateway|api|lb|load/i` → `gateway`
   - 标签匹配 `/auth|login|jwt|oauth/i` → `security`
   - 标签匹配 `/error|fail|alert/i` → `error`
   - 其余 → `service`

   对每个**有规范调色板槽的角色**——`service`、`database`、`queue`、`gateway`、`error`、`external`、`security`——最高频的 `(角色, 颜色对)` 映射胜。该对进入角色的规范调色板槽：
   `service→primary, database→success, queue→warning, gateway→accent, error→danger, external→neutral, security→secondary`。
   把 `roles[role]` 设为该槽名。

   **判断与容器形状不生成 `roles[...]` 条目**——只记录在 `shapes.decision` 与 `shapes.container`。在判断/容器 vertex 上观察到的颜色对仍参与调色板（可填剩余槽）但不绑定语义角色。

   剩余颜色对（未被任何角色-槽映射认领）按频率降序填入其余空调色板槽。

   每个角色使用的形状类串记录进 `shapes[role]`。六个命名形状键为 `service`、`database`、`queue`、`decision`、`external`、`container` —— `gateway`、`error`、`security` 角色继承 `shapes.service`，不生成自己的 `shapes[...]` 条目。示例：`shapes.database = "shape=cylinder3"`。

5. **提取字体。** 跨 vertex 计算众数 `fontFamily` 与 `fontSize`，输出为 `font.fontFamily` 与 `font.fontSize`。同时把逐 vertex 的 `fontStyle` 记为**工作变量**（非输出字段——schema 无顶层 `font.fontStyle`）。若一个可区分的 vertex 子集用了更大 `fontSize` 且 `fontStyle=1`（粗体），把该子集视为标题：`font.titleFontSize` 设为其众数尺寸并设 `font.titleBold: true`。否则省略两个标题字段。

6. **提取边默认值。** 取众数边 style 串，但计数前剥离这些逐边坐标键：`entryX`、`entryY`、`exitX`、`exitY`、`entryDx`、`entryDy`、`exitDx`、`exitDy`。箭头样式从 `endArrow`/`endFill` 单独记入 `edges.arrow`。
   若有边带 `dashed=1`，收集其 `value`（标签）属性。若 ≥2 条共享一个公共词（如都标 "async" 或 "optional"），把该词加入 `edges.dashedFor`。

7. **提取附加项。** 任何 vertex 或边出现 `sketch=1` → `extras.sketch = true`。跨 vertex 的众数 `strokeWidth` → `extras.globalStrokeWidth`（默认 `1`）。

8. **设溯源。**
   ```json
   {
     "source": { "type": "xml", "path": "<输入绝对路径>", "extracted_at": "YYYY-MM-DD" },
     "confidence": "high"
   }
   ```

### XML 边界情况

| 情况 | 行为 |
|---|---|
| 源颜色对 <3 组 | 未填的槽留 `null`。`confidence` 降为 `"medium"`。摘要警告用户。 |
| 源颜色对 >7 组 | 按频率保留前 7。摘要警告部分颜色被丢弃。 |
| 非标准 `shape=` 关键字（如 `shape=mxgraph.aws4.*`） | 不匹配步骤 4 的优先级梯，vertex 形状类落到 `rounded=0`。图标语义丢失；颜色、标签、边样式仍被捕获。角色推断仍走标签正则。摘要注明：*"检测到非标准形状库——预设不保留图标（颜色与标签已捕获）。"* |
| 非英文标签 | 步骤 4 的英文关键词正则大多落空；多数 vertex 塌缩为 `service`。调色板/形状/字体/边仍正确捕获（不依赖标签文字）。`confidence` 保持 `"high"`。摘要注明：*"角色标签非英文——`service`/`database`/`decision`/`container`/`external` 由形状类推断；其他角色未映射。"* |
| 文件完全没有 `<mxCell vertex="1">` | 停。拒绝保存。消息：*"没有可学的东西——源文件没有形状。"* |

## 图像提取路径

输入：PNG/JPG（或任何 vision 可读图像格式）路径。输出：候选预设 JSON。基于推断；`confidence` 顶多 `"medium"`。

**前置：** agent 的 vision 能力必须可用（与主工作流自检同机制）。vision 不可用则停下并告诉用户：
*"基于图像的学习需要 vision 模型（Claude Sonnet 或 Opus）。换此类模型重跑，或改提供 `.drawio` 源文件。"*（实际执行时用用户语言表达同义信息。）

### 步骤

1. **读图。** 用 agent 的 vision 输入——与主工作流步骤 5 自检读导出 PNG 同路。

2. **目检提取调色板。** 识别形状主体上的不同填充色区域。

   对每个不同填充：
   - `fillColor` —— 每个 RGB 通道量化到最近的 16 的倍数。若所得 HSL 亮度低于 0.75，抬到 0.85（保色调与饱和度；设 L=0.85；HSL→RGB 往返）。输出 `#RRGGBB`。drawio 标准浅彩占据 L≈0.85–0.96；低于 0.75 读作"对填充色太暗"，此步把它抬回该区间。
   - `strokeColor` —— 读匹配边框。不可读时由填充加深 ~25% 推导（匹配 HSL，L 降 0.25）。

   每个 `(fillColor, strokeColor)` 对按此决策序映射到命名槽：

   1. **先查灰。** 填充的 R、G、B 三通道彼此在 ±16 内（与 XML 路径灰色系规则同定义），或 HSL 饱和度 < 0.20，归 `neutral`。此检查无视色调角，优先胜出。
   2. **否则按色调带。** 用这些显式 HSL 色调区间：
      - 180°–260° → `primary`（蓝）
      - 80°–170° → `success`（绿）
      - 45°–65° → `warning`（黄）
      - 20°–44° → `accent`（橙）
      - 0°–19° 或 320°–360° → `danger`（红/粉）
      - 260°–320° → `secondary`（紫）
   3. **无带命中**（65°–80° 或 170°–180° 的间隙区）→ 按角距溢到最近带。

   **碰撞规则。** ≥2 个不同填充落同一槽时，按图中覆盖像素总面积降序排。最大者保规范槽。其余填充按色调带角距溢到**最近的空槽**——先两侧相邻带、再向外。全部槽已满则丢弃多余并在摘要警告。

3. **提取形状词汇。** 按轮廓分类每个可见形状：
   - 圆角矩形 → `rounded=1`
   - 直角矩形 → `rounded=0`
   - 圆 / 椭圆 → `ellipse`
   - 菱形 → `rhombus`
   - 圆柱（上下边弯曲的矩形）→ `shape=cylinder3`
   - 带标题容器（标题栏 + 内嵌子元素）→ `swimlane;startSize=30`
   - 虚线边框矩形 → `rounded=1;dashed=1`

   角色指派用**与 XML 路径步骤 4 相同的标签文字 + 形状规则**。可见标签经 vision 读取。

4. **提取字体。** 尽力而为。可区分类别：
   - 明显衬线 → `fontFamily: "Georgia"`
   - 明显等宽 → `fontFamily: "Courier New"`
   - 其余 → `fontFamily: "Helvetica"`

   尺寸按相对观感：
   - 小 → `fontSize: 11`
   - 中 → `fontSize: 12`
   - 大 → `fontSize: 14`

   标题/容器头明显更大或更粗 → 相应设 `titleFontSize` 并 `titleBold: true`。

5. **提取边默认值。**
   - 直角正交箭头 → `edges.style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1"`。
   - 曲线箭头 → `edges.style` 追加 `;curved=1`。
   - 实心三角箭头 → `edges.arrow = "endArrow=classic;endFill=1"`。
   - 开口 V 形箭头 → `edges.arrow = "endArrow=open;endFill=0"`。
   - 标签旁有 "optional"、"async"、"fallback"、"secondary" 类虚线箭头 → 把这些标签词加入 `edges.dashedFor`。

6. **提取附加项。**
   - 明显手绘 / 粗糙 / 素描风（波浪笔触、不均匀填充）→ `extras.sketch = true`。
   - 粗笔触（明显 >1.5 倍正常）→ `extras.globalStrokeWidth = 2`。
   - 否则默认：`extras = { "sketch": false, "globalStrokeWidth": 1 }`。

7. **设溯源与置信度。**
   ```json
   {
     "source": { "type": "image", "path": "<输入绝对路径>", "extracted_at": "YYYY-MM-DD" },
     "confidence": "medium"
   }
   ```
   调整：
   - 可识别形状 <3 个 → `confidence: "low"`。
   - 图像路径默认停在 `"medium"`。通往 `"high"` 的唯一路径是严格可验证的信号：源图本身由 drawio 导出（可辨认的 drawio 默认界面、网格或可见水印），**且**七个调色板槽全填，**且**七个角色都有标签。这保住了推断式（图像）与解析式（XML）溯源之间的语义差距。

### 图像边界情况

| 情况 | 行为 |
|---|---|
| vision 不可用 | 按上述停下——不退回瞎猜。 |
| 图中可识别形状 <3 个 | 继续；标 `confidence: "low"`；摘要明确警告该预设是粗略近似。 |
| 图中无可见标签 | 角色指派塌缩为仅形状类：圆柱 → `database`、菱形 → `decision`、swimlane → `container`、灰填充虚线框 → `external`、其余 → `service`。调色板/字体/边仍捕获。摘要注明：*"无可读标签——未推断形状类之外的语义角色。"* |
| 两个调色板槽会落同一色系 | 较高频者保规范槽；另一个溢到相邻空槽（步骤 2 规则）。 |
| 图中不同填充 >7 个 | 按步骤 2 碰撞规则保留覆盖面积最大的 7 个。摘要警告部分颜色被丢弃。 |

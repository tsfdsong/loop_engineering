# Auto-layout（Graphviz 自动布局）

图表**大或布局重**时读本文——依赖/调用图、代码/模块结构、约 **>15 节点**——手摆 `x`/`y` 坐标又慢、又易错、又容易重叠。

不要在 Generate 步骤手算坐标，把图描述为 JSON，让 `scripts/autolayout.py` 用 Graphviz 摆节点、布边，然后对产出的 `.drawio` 走正常工作流（导出草稿 → 自检 → …）。

小图或精修样式图保持手摆——自动布局用精细控制换规模。

## 依赖

需要 PATH 上有 Graphviz `dot`：

```bash
# macOS
brew install graphviz
# Debian/Ubuntu
sudo apt install graphviz
```

`dot` 缺失时脚本带清晰信息退出——那种情况下回退手摆坐标。

## 用法

```bash
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o diagram.drawio
```

向 stderr 打印 `wrote diagram.drawio (N nodes, M edges)` 并写出正常 `.drawio` 文件。然后从主工作流的**导出草稿**步骤继续（`--width 2000` 预览 PNG、自检、评审循环、`-e` + `repair_png.py` 最终导出）。

## 输入格式

```json
{
  "direction": "TB",
  "nodes": [
    {"id": "client", "label": "Web Client", "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"},
    {"id": "gw", "label": "API Gateway", "group": "edge", "groupLabel": "Edge tier"},
    {"id": "db", "label": "User DB", "style": "shape=cylinder3;whiteSpace=wrap;html=1;", "width": 120, "height": 80, "group": "data"}
  ],
  "edges": [
    {"source": "client", "target": "gw", "label": "HTTPS"},
    {"source": "gw", "target": "db"}
  ]
}
```

**字段**

| 字段 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `direction` | 否 | `TB` | `TB`（上→下）或 `LR`（左→右）——布局 rank 方向 |
| `nodes[].id` | **是** | — | 唯一；不得为 `0` 或 `1`（draw.io 根 cell 保留） |
| `nodes[].label` | 否 | 取 `id` | 显示文字；自动 XML 转义 |
| `nodes[].style` | 否 | 组色，否则蓝 | 任意 draw.io style 串——复用 `diagram-types.md` 的角色/形状样式与激活预设。无 style 的节点按其组着色（见**容器/分组**）；显式 style 永远胜 |
| `nodes[].width` / `height` | 否 | `120` / `60` | 像素；dot 按此真实尺寸布局 |
| `nodes[].group` | 否 | 无 | 组键，或 `/` 分隔路径（`"core/db"`）做**嵌套**容器——同路径节点装箱在一起（见**容器/分组**） |
| `nodes[].groupLabel` | 否 | 路径末段 | 显示在节点最深层容器上的标题（首个带该路径的节点胜） |
| `edges[].source` / `target` | **是** | — | 必须匹配节点 id |
| `edges[].label` | 否 | 空 | 边文字 |

## 它怎么摆

- 节点位置来自 `dot`（层级分层布局），换算成 draw.io 像素并对齐网格（10 的倍数）。
- 边用 `splines=ortho`：dot 的正交路线重放为 draw.io waypoint，边**绕**节点走而非穿过。
- 调用脚本前把每个节点的 `style` 设为激活预设的角色/形状值来应用预设——脚本本身不认识预设。

## 容器 / 分组

给节点 `group` 键，脚本把每组包进带标题的容器（顶部有组标题的虚线框），并经 Graphviz cluster 告诉 dot 保持该组节点在一起。分组节点成为容器的子元素（`parent="<容器>"`、相对坐标）；未分组节点留在顶层。这把扁平乱麻变成"相关模块装箱"的架构视图。

**嵌套。** `group` 值带 `/` 分隔符即建嵌套容器：`"core/db"` 把节点放进 `db` 框、`db` 框又坐在 `core` 框里。每个路径前缀都成为容器，任意深的包树映射为嵌套框。节点也可以*直接*坐在父框里（`group: "core"`）与兄弟子框（`group: "core/db"`）并列。

- **按组着色。** 每个顶层组分到技能自有调色板（`styles/built-in/default.json`，按角色顺序轮换：蓝 → 绿 → 橙 → 紫 → 黄 → 红 → 灰）中的一种颜色。无自有 `style` 的节点用其组色着色，容器边框 + 标题同色——相关模块读作彩色簇而非单色框。带自有 `style` 的节点（如来自已应用预设）不动。传 `--mono` 关闭着色（灰虚线框、默认蓝节点——旧外观）。未分组图不受影响。
- 每个容器框是成员与子框的包围盒加统一内边距。dot cluster 边距设为同值，故每个框等于 dot 的 cluster 框——dot 保证**任意嵌套深度**下互不重叠。
- 标题坐在顶部内边距（`verticalAlign=top`）；框标题为路径末段，或某成员的 `groupLabel`。
- 容器仅是视觉（自身无边）。边仍连节点→节点、正常跨容器路由。
- 容器顶部内边距若会越过页面原点，整图平移，确保没有负坐标。

## 预览前先 validate

`scripts/validate.py` 是确定性结构 linter——在（更慢的、基于 vision 的）自检之前对产出的 `.drawio` 跑：

```bash
python3 <this-skill-dir>/scripts/validate.py diagram.drawio
```

它抓悬空边端点、重复/保留 id、坏 parent 引用（错误），以及离格/负坐标几何与同层节点重叠（警告）——不启动 draw.io。任一错误（或 `--strict` 下任一警告）退出码非零，可做工作流闸门。自动布局输出应总是干净通过；失败意味着输入图畸形（如边引用了缺失的节点 id）。

## Importers —— 可视化代码结构

内置 importer 把代码库转成可供 autolayout 的 graph JSON，"可视化这个项目"成为两步流水线：

| 语言 | 脚本 | 节点 = | 边 = |
|---|---|---|---|
| Python | `scripts/pyimports.py <dir>` | 模块 / 包（`ast`） | 项目内 `import` / `from` |
| JS / TS | `scripts/jsimports.py <dir>` | 源文件（`.ts/.tsx/.js/.jsx/.mjs/.cjs`） | 解析后的相对 `import`/`export from`/`require()`/`import()` |
| Go | `scripts/goimports.py <dir>` | 包（目录，经 `go.mod`） | 模块内包导入 |
| Rust | `scripts/rustimports.py <dir>` | 模块（`.rs` 文件 / `mod`） | crate 内 `use crate::` / `super::` / `self::` |
| Python（类） | `scripts/pyclasses.py <dir>` | 类（`ast`） | 子类 → 基类（继承） |

```bash
python3 <this-skill-dir>/scripts/pyimports.py myproject -o graph.json
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o diagram.drawio
```

各 importer 只保留**项目内**边（第三方/标准库导入忽略），缩短节点标签（去掉共享的包/模块/目录前缀；id 保持全限定），共享同一组 flag：`--direction TB|LR`（默认 `TB`）、`--group`、`--no-reduce`。

- **Python**（`pyimports.py`）：目录本身是包（有 `__init__.py`）时，模块名带包限定，项目自身的绝对导入可解析；嵌套子包（`pkg.sub.mod`）已处理。
- **JS/TS**（`jsimports.py`）：解析基于路径（尝试源扩展名与目录 `index` 文件）；跳过 `node_modules` 与裸说明符。扫描基于 regex，不是完整解析器。
- **Go**（`goimports.py`）：从 `go.mod` 读 `module` 路径；每个 `.go` 文件目录是一个包；跳过 `*_test.go` 与 `vendor/`。
- **Rust**（`rustimports.py`）：每个 `.rs` 文件是一个模块（`mod.rs`/`main.rs`/`lib.rs` 命名所属模块）；边来自以 `crate::`/`super::`/`self::` 为根的 `use` 路径（花括号组展开）。跳过 `std`/外部 crate 与 `target/`。基于 regex——内联 `mod { … }` 块不拆分，2015 版裸 crate 内路径不解析。
- **Python 类**（`pyclasses.py`）：更细粒度——每类一节点，边从各子类指向其扩展的项目内基类，结果是自动生成的类继承图。基类按名匹配（优先同模块）；外部基类（`object`、第三方）忽略。加 `--group` 时类按模块装箱，深包树自然嵌套。只做继承——函数级调用图超出范围（Python 静态调用解析不可靠）。

**密度归约默认开启**——可读结果的关键。真实 import 图很密（asyncio：33 模块 / ~149 边）；不归约会渲染成乱麻。每个 importer 应用**传递归约**（Graphviz `tred`——丢弃已由更长路径蕴含的边），asyncio 上从 ~149 边砍到 ~46，乱麻变清晰可追的图。传 `--no-reduce` 保留每条边。

**`--group`** 按子包 / 目录路径给每个节点分容器，autolayout 把相关模块装箱——路径有深度时嵌套（见**容器/分组**）。把大代码图变成分层架构视图的最快路径。

其他语言：用任意分析器产出同样的 graph JSON（如 JS/TS 更丰富解析用 `dependency-cruiser`、Go 调用图用 `go-callvis`），同样喂给 autolayout。

## 边界

- **摆放是拓扑的不是语义的**——dot 最小化边交叉，可能把节点放进你手摆不会选的列。换另一个 `direction` 重导出，或事后手调产出的 XML（它是正常 `.drawio`）。
- **import 边是静态的**——`pyimports`/`jsimports`/`goimports` 读静态 import 语句（不是动态 `importlib`、运行时 `require`、反射）；`pyclasses` 只解析继承，不含方法级调用。
- 同一 `(source, target)` 对的**平行边**共用一条路线。
- **容器不加边**——`group`/嵌套仅为布局装箱；边保持节点→节点。要建带自身连接的手工 swimlane/架构容器，见 SKILL.md "容器与分组"。

# 形状词汇与搜索

图表需要**特定形状**时读本文——云厂商图标（AWS/Azure/GCP）、网络/Cisco/Kubernetes 符号、UML/BPMN/ER 元件、电气或 P&ID 部件——或任何你本来要*猜* `style=` 串的时刻。

拿 style 有两条路：

1. **搜官方形状索引**（`scripts/shapesearch.py`）——10,446 个真实 draw.io 调色板形状，带精确 `style`、`w`、`h`。品牌/厂商图标与任何非平凡形状用它。**搜索到的 style 永远优先于手写的 `shape=mxgraph.*` 猜测**——猜错的模板名会静默渲染成空白框。
2. **下方速查表**——常见内置形状，其 style 串足够短且稳定、可以手写（矩形、流程图符号、UML 原语、容器、边）。

## 搜索形状

```bash
python3 <this-skill-dir>/scripts/shapesearch.py "aws lambda" --limit 5
python3 <this-skill-dir>/scripts/shapesearch.py "uml actor" --json
```

- 查询为空格分隔关键词；匹配基于 tag，带 Soundex 模糊与 `camelCase`/数字拆分（`"pid2valve"` → `pid valve`）。
- 每个命中打印 `Title (WxH)` 加完整 `style=` 串。`--json` 时输出 `[{style,w,h,title}]` 供程序化使用。
- 把 `style` 逐字复制进 `mxCell`，用报告的 `w`/`h` 作 `mxGeometry` 宽/高（厂商图标按固定纵横比绘制）。
- 结果按 tag 相关度排序，**标题**含查询词的形状在各分数层冒泡置顶。但排序仍是启发式，且很多形状共用标题（三个 `Lambda` 变体：`aws3`/`aws4`/`aws3d`）——用 `--limit 5` 跑，按标题和尺寸挑你要的那行，不要盲取第 1。

```xml
<mxCell id="2" value="Lambda" style="<paste the searched style here>" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="78" height="78" as="geometry"/>
</mxCell>
```

覆盖库：AWS（`aws3`/`aws4`）、Azure、GCP、Cisco、Kubernetes、UML、BPMN、ER、电气、P&ID、mockup/线框、流程图、网络、通用/基础集。内置索引（`data/shape-index.json.gz`）为上游 draw.io 形状数据——归属见 `data/SHAPE-INDEX-NOTICE.md`。

## AI / LLM 品牌 logo

draw.io 内置库**没有**现代 AI/LLM 品牌 logo，"LLM 应用架构"否则只能渲染成通用方框。`scripts/aiicons.py` 把品牌名（OpenAI、Claude、Gemini、Mistral、Llama、HuggingFace、Ollama、LangChain 等 321 个）解析为 [lobe-icons](https://github.com/lobehub/lobe-icons)（MIT）支撑的 draw.io `image` style。

```bash
python3 <this-skill-dir>/scripts/aiicons.py "claude" --json        # CDN reference
python3 <this-skill-dir>/scripts/aiicons.py "openai" --embed        # self-contained
python3 <this-skill-dir>/scripts/aiicons.py --list                  # all brands
```

- 存在 `-color` 变体则选之，否则用单色 logo（如 OpenAI 仅单色）。返回正方形 `image` style；宽高都用报告的 `--size`（默认 48）。
- **默认经 CDN URL 引用图标**——SVG 在 unpkg 上、不在本仓库，故**渲染或打开图时 draw.io 需要网络**；离线导出画出空白框。传 `--embed` 一次性抓取 SVG 并内联为 data URI（可移植、离线可渲染、XML 更大）。
- Logo 为各所有者的商标，仅作识别引用——与 draw.io 附带 AWS/Azure 图标同一依据。
- lobe 缺少的 RAG/LLM 应用常见**数据存储**（Qdrant、Redis、Postgres、Mongo、Elasticsearch、Milvus、Supabase、Neo4j、ClickHouse、Kafka、Snowflake、Databricks 等）经 [simple-icons](https://simpleicons.org) CDN（CC0）自动兜底解析——同命令、同输出形态。两个集合都没有的品牌无 logo；用圆柱（`shape=cylinder3;`，见下）或 `scripts/shapesearch.py "<name> database"`。

## 速查表 —— 可手写的 style

以下足够稳定、无需搜索。搭配 `whiteSpace=wrap;html=1;` 使用。

### 常用形状（`shape=` 关键字）

| 需求 | style |
|---|---|
| 矩形 / 圆角框 | `rounded=0;` / `rounded=1;` |
| 圆 / 椭圆 | `ellipse;`（正圆加 `aspect=fixed;`） |
| 菱形（判断） | `rhombus;` |
| 圆柱（数据库） | `shape=cylinder3;` |
| 云 | `cloud;` |
| 立方体（3D） | `shape=cube;` |
| 便利贴 | `shape=note;` |
| 文档（卷底） | `shape=document;` |
| 文件夹 | `shape=folder;` |
| 卡片（切角） | `shape=card;` |
| 处理（双边框） | `shape=process;` |
| 步骤 / 人字纹 | `shape=step;` |
| 平行四边形（I/O） | `shape=parallelogram;perimeter=parallelogramPerimeter;` |
| 梯形 | `shape=trapezoid;perimeter=trapezoidPerimeter;` |
| 六边形 | `shape=hexagon;perimeter=hexagonPerimeter2;` |
| 手工输入 | `shape=manualInput;` |
| 数据存储 | `shape=dataStorage;` |
| 页外连接符 | `shape=offPageConnector;` |
| 延迟 | `shape=delay;` |
| OR / XOR 门 | `shape=or;` / `shape=xor;` |
| 块状箭头 | `shape=singleArrow;` / `shape=doubleArrow;` |
| 标注（气泡） | `shape=callout;` |

### UML 原语

| 元素 | style |
|---|---|
| 角色（小人） | `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;` |
| 边界 | `shape=umlBoundary;` |
| 控制 | `shape=umlControl;` |
| 实体 | `shape=umlEntity;` |
| 生命线 | `shape=umlLifeline;perimeter=lifelinePerimeter;container=1;` |
| 帧 | `shape=umlFrame;` |
| 提供接口（棒棒糖） | `shape=lollipop;direction=south;` |
| 需求接口 | `shape=requires;direction=north;` |
| 组件 | `shape=component;` |

### 容器（父子；子元素用相对坐标）

| 类型 | style | 何时 |
|---|---|---|
| 不可见组 | `group;pointerEvents=0;` | 无边框、自身无连接 |
| 带标题 swimlane | `swimlane;startSize=30;` | 可见标题栏 / 有连接 |
| 任意形状作容器 | 追加 `container=1;pointerEvents=0;` | 装箱但自身无连接 |

### 边

| 需求 | 加进 style |
|---|---|
| 正交路由 | `edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;` |
| 曲线 | `curved=1;` |
| 无箭头 | `endArrow=none;` |
| 开口/细箭头 | `endArrow=open;` / `endArrow=classicThin;` |
| 虚线 | `dashed=1;`（图案用 `dashPattern=8 8;`） |
| 流动动画 | `flowAnimation=1;` |
| 标签背景 | `labelBackgroundColor=#ffffff;` |

### 实用属性旋钮

- `fontStyle` 是位掩码：`1`=粗体、`2`=斜体、`4`=下划线（相加组合：`3`=粗+斜）。
- `direction=north|south|east|west` 按 90° 旋转形状；自由旋转用 `rotation=<deg>`。
- `gradientColor=#RRGGBB;` + `gradientDirection=north;` 做渐变填充。
- `sketch=1;` 手绘风（可能的话经样式预设全局设置）。

更丰富的逐形状细节，上游源为 jgraph/drawio-mcp 的 `shared/style-reference.md`（Apache-2.0）。

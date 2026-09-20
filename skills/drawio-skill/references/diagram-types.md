# 图表类型预设

用户请求特定图表类型时，套用下面对应预设的形状、样式与布局约定。这些预设设定**结构性** style 关键字（如 ERD 的 `shape=table;childLayout=tableLayout`）；用户样式预设（见 `references/style-presets.md`）在其上叠加颜色/字体/边/附加项。

何时读本文：
- 用户点名下列图表类型之一（ERD、UML 类、时序、架构、ML/DL 模型、流程图）
- 你在为新图选择形状词汇或布局方向

## ERD（实体关系图）

| 元素 | Style | 说明 |
|---------|-------|-------|
| 表 | `shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#6c8ebf;fillColor=#dae8fc;` | 每张表是一个容器 |
| 行（列） | `shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;` | 表的子元素，`parent=tableId` |
| PK 列 | 行上加粗：`fontStyle=1` | 用 `PK` 前缀或钥匙图标标记 |
| FK 关系 | 虚线边：`dashed=1;endArrow=ERmandOne;startArrow=ERmandOne;` | 用 ER 记法箭头 |
| 布局 | TB，表间距 300px | 相关表纵向分组 |

## UML 类图

| 元素 | Style | 说明 |
|---------|-------|-------|
| 类框 | `swimlane;fontStyle=1;align=center;startSize=26;html=1;` | 三段式：标题 / 属性 / 方法 |
| 分隔线 | `line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=10;rotatable=0;labelPosition=left;points=[];portConstraint=eastwest;` | 段与段之间 |
| 继承 | `endArrow=block;endFill=0;` | 空心三角箭头 |
| 实现 | `endArrow=block;endFill=0;dashed=1;` | 虚线 + 空心三角 |
| 组合 | `endArrow=diamondThin;endFill=1;` | 实心菱形 |
| 聚合 | `endArrow=diamondThin;endFill=0;` | 空心菱形 |
| 布局 | TB，类间距 250px | 接口在实现之上 |

## 时序图

| 元素 | Style | 说明 |
|---------|-------|-------|
| 角色/对象 | `shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;` | 带竖虚线的生命线 |
| 同步消息 | `html=1;verticalAlign=bottom;endArrow=block;` | 实线、实心箭头 |
| 异步消息 | `html=1;verticalAlign=bottom;endArrow=open;dashed=1;` | 虚线、开口箭头 |
| 返回消息 | `html=1;verticalAlign=bottom;endArrow=open;dashed=1;strokeColor=#999999;` | 灰色虚线 |
| 激活条 | 生命线上加 `shape=umlFrame;whiteSpace=wrap;` | 生命线上的窄矩形 |
| 布局 | LR，生命线间距 200px | 时间自上而下 |

## 架构图

| 元素 | Style | 说明 |
|---------|-------|-------|
| 层/档 | `swimlane;startSize=30;` | 分组容器：Client / API / Service / Data |
| 服务 | `rounded=1;whiteSpace=wrap;html=1;` + 层色 | 按层用调色板 |
| 数据库 | `shape=cylinder3;whiteSpace=wrap;html=1;` | 绿色系 |
| 队列/总线 | `rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;` | 黄色——按枢纽模式居中放 |
| 网关/LB | `shape=mxgraph.aws4.resourceIcon;` 或 `rounded=1;` + 橙色 | 橙色系 |
| 外部 | `rounded=1;dashed=1;fillColor=#f5f5f5;strokeColor=#666666;` | 虚线边框表外部系统 |
| 布局 | 按层数 TB 或 LR；≥4 层用 TB | 枢纽节点居中 |

## ML / 深度学习模型图

用于神经网络架构图——适合投 NeurIPS、ICML、ICLR 的论文。

| 元素 | Style | 说明 |
|---------|-------|-------|
| 层块 | `rounded=1;whiteSpace=wrap;html=1;` + 类型色 | 主构建块 |
| 输入/输出 | `fillColor=#d5e8d4;strokeColor=#82b366;` | 绿 |
| Conv / 池化 | `fillColor=#dae8fc;strokeColor=#6c8ebf;` | 蓝 |
| Attention / Transformer | `fillColor=#e1d5e7;strokeColor=#9673a6;` | 紫 |
| RNN / LSTM / GRU | `fillColor=#fff2cc;strokeColor=#d6b656;` | 黄 |
| FC / Linear | `fillColor=#ffe6cc;strokeColor=#d79b00;` | 橙 |
| Loss / 激活 | `fillColor=#f8cecc;strokeColor=#b85450;` | 红/粉 |
| 跳连（skip） | `dashed=1;endArrow=block;curved=1;` | 虚线曲线箭头 |
| 张量形状标签 | 加第二行标注：`value="Conv2D&#xa;(B, 64, 32, 32)"` | 多行用 `&#xa;` |
| 布局 | TB（数据自上→下），层距 150px | 编码器/解码器用 swimlane 分组 |

**张量形状约定：** 每层标注输入/输出张量维度，`(B, C, H, W)` 或 `(B, T, D)` 格式。维度放标签第二行，用 `&#xa;` 分隔。

## 流程图（增强）

| 元素 | Style | 说明 |
|---------|-------|-------|
| 开始/结束 | `ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;` | 绿色椭圆 |
| 处理 | `rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;` | 蓝色矩形 |
| 判断 | `rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;` | 黄色菱形 |
| 输入/输出 | `shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;` | 橙色平行四边形 |
| 子流程 | `rounded=0;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;` + 双边框 | 紫 |
| Yes/No 标签 | 判断出边上 `value="Yes"` / `value="No"` | 判断分支永远标标签 |
| 布局 | TB，垂直间距 200px | 判断左右分支、汇合回中线 |

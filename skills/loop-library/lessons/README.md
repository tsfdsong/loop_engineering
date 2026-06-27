# loop 经验库

loop 技能的**持续积累教训库**。每次 `/loop` 任务启动时按需注入相关经验，任务结束时沉淀新教训。让 loop "越来越聪明"。

## 目录结构

```
lessons/
├── README.md          ← 本文件（格式规范）
├── frontend.md        ← 前端类教训（渲染/交互/Playwright）
├── backend.md         ← 后端类教训（API/ORM/逻辑）
├── environment.md     ← 环境/部署类教训（DB/Redis/Docker）
├── verification.md    ← 验证/门禁类教训（测试/构建/断言）
└── design.md          ← 设计/交互类教训（布局/样本对照）
```

## 单条经验格式

每条经验是一个 Markdown 条目，含 YAML frontmatter + 正文：

```markdown
---
id: FE-001                       # 唯一ID，格式 <DOMAIN>-<序号>
domain: frontend                 # frontend/backend/environment/verification/design
severity: high                   # high/medium/low
applies_when:                    # 适用条件（全部满足才命中，AND 关系）
  - task_type: frontend          # 任务类型: frontend/backend/fullstack/config/docs
  - has_sample_url: true         # 布尔特征: has_sample_url/has_database/has_docker
  - tech_stack: react            # 技术栈交集: 任务的 tech_stack 与此有交集即命中
source: loop/mcp-plaza-0626      # 来源任务分支
created: 2026-06-26              # 创建日期
supersedes: ""                   # (可选) 废弃的旧经验 ID
deprecated: false                # (可选) 是否已废弃
---

## <经验标题>

**问题**: <具体场景描述，发生了什么>

**根因**: <为什么会出现这个问题>

**规则**: <应该怎么做，可执行的规则>

**关联门禁**: <对应门禁矩阵的维度，如 F1, F2, G5>
```

## 字段说明

| 字段 | 说明 |
|------|------|
| `id` | `<DOMAIN缩写>-<3位序号>`，如 FE-001 / BE-002 / VER-003 / ENV-001 / DS-001 |
| `applies_when` | 任务特征匹配条件列表。loop 在 Step① 提取任务特征向量后，逐条比对。**列表内全部条件满足才命中**（AND）。`tech_stack` 字段是交集匹配（任务栈 ∩ 此值 非空即满足）。 |
| `severity` | high 的经验优先注入，违反时触发更严格处置 |
| `source` | 来源任务分支名，可追溯原始场景 |
| `关联门禁` | 指向门禁矩阵维度，形成"经验→门禁→自愈"闭环 |

## 匹配规则（loop Step① 执行）

1. loop 提取当前任务的**特征向量**：
   - `task_type`: frontend / backend / fullstack / config / docs
   - `has_sample_url`: 是否提供了前端样本 URL
   - `has_database`: 是否涉及数据库
   - `has_docker`: 是否涉及 Docker
   - `tech_stack`: 技术栈列表（如 [react, fastapi, postgres]）
   - `complexity`: lite / standard / full

2. 扫描所有 `lessons/*.md` 的每条经验，对其 `applies_when` 做匹配：
   - `task_type`: **包含匹配**——任务的 task_type 在经验的 task_type 列表中即命中。`fullstack` 任务同时命中 `backend` 和 `frontend` 经验。
   - `has_*`: 布尔精确匹配
   - `tech_stack`: 交集匹配（任务栈 ∩ 经验值 非空即命中）
   - **列表内所有条件必须全部满足**（AND）

3. 命中的经验 → 提取"规则"段落注入本轮上下文；未命中的 → 跳过（省 token）

4. 输出"已注入经验清单"给用户确认

## 维护规则

| 规则 | 说明 |
|------|------|
| **去重** | 沉淀前先扫描同领域文件，语义重复的不新增（避免膨胀） |
| **冲突升级** | 新经验与旧经验矛盾时，新经验标 `supersedes: <旧id>`，旧条目标 `deprecated: true` |
| **不物理删除** | 只追加和标记废弃，保留演进历史 |
| **人工可编辑** | 纯 Markdown，用户可随时手动修正/删除/补充 |

## 沉淀时机

| 时机 | 触发 | 动作 |
|------|------|------|
| **自愈成功后** | 自愈闭环修复了一条门禁失败 | 去重后写入对应领域文件，报告标注"📍 新增经验" |
| **阻塞保护时** | 连续2轮无进展进入阻塞 | 提取当前阻塞点作为教训写入，标记 `status: unresolved` |
| **Step⑥ 交付时** | 任务完成复盘 | 回顾本轮所有自愈动作 + 用户纠正点，提炼新教训写入 |

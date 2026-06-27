# 经验库协议

loop 技能的持续积累教训库。每次任务启动时按需注入相关经验，自愈成功和任务完成时沉淀新教训。

## 目录结构

```
loop-library/lessons/
├── README.md          ← 格式规范
├── frontend.md        ← 前端类教训（渲染/交互/agent-browser）
├── backend.md         ← 后端类教训（API/ORM/逻辑）
├── environment.md     ← 环境/部署类教训（DB/Redis/Docker）
├── verification.md    ← 验证/门禁类教训（测试/构建/断言）
├── design.md          ← 设计/交互类教训（布局/样本对照）
└── （更多领域按需扩展）
```

## 单条经验格式

```markdown
---
id: FE-001                       # 唯一ID，格式 <DOMAIN>-<序号>
domain: frontend                 # frontend/backend/environment/verification/design/orchestration
severity: high                   # high/medium/low
applies_when:                    # 适用条件（全部满足才命中，AND 关系）
  - task_type: frontend          # frontend/backend/fullstack/config/docs
  - has_sample_url: true         # 布尔特征
  - tech_stack: react            # 交集匹配
source: loop/mcp-plaza-0626      # 来源任务分支
created: 2026-06-26
supersedes: ""
deprecated: false
---

## 经验标题

**问题**: 具体场景描述

**根因**: 为什么会出现

**规则**: 应该怎么做，可执行的规则

**关联门禁**: 对应门禁矩阵的维度，如 F1, F2, G5
```

## 注入时机（Step①）

1. 提取任务特征向量: task_type, has_sample_url, has_database, has_docker, tech_stack, complexity
2. 扫描 `loop-library/lessons/*.md` 每条经验的 `applies_when` 做匹配
3. 命中的经验 → 提取"规则"段落注入上下文
4. 输出"已注入经验清单"给用户确认

### 匹配规则

- `task_type`: 包含匹配，fullstack 同时命中 backend+frontend
- `has_*`: 布尔精确匹配
- `tech_stack`: 交集匹配
- 列表内所有条件 AND 关系

## 沉淀时机

| 时机 | 触发 | 动作 |
|------|------|------|
| **自愈成功后** | 自愈闭环修复了一条门禁失败 | 去重后写入对应领域文件，"📍 新增经验" |
| **阻塞保护时** | 连续2轮无进展进入阻塞 | 提取阻塞点作为教训，标记 `status: unresolved` |
| **Step⑥ 交付时** | 任务完成复盘 | 回顾本轮自愈动作+用户纠正点，提炼新教训 |

## 维护规则

| 规则 | 说明 |
|------|------|
| **去重** | 语义重复的不新增（避免膨胀） |
| **冲突升级** | 新经验标 `supersedes: <旧id>`，旧标记 `deprecated: true` |
| **不物理删除** | 只追加和标记废弃，保留演进历史 |
| **人工可编辑** | 纯 Markdown，用户可随时手动修正 |

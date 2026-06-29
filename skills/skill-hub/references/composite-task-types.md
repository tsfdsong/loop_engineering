# 复合任务类型定义（v6.0）

> Orchestrator 在识别到复合任务时，按下表匹配并调度对应技能链。

## 5 类预设复合任务

| # | 类型 | 默认技能链 | 编排方式 | 触发关键词 |
|---|------|----------|---------|----------|
| 1 | 调研+决策 | brainstorming → system-review → writing-plans | 串行 | 调研 + 决策/选型/对比 |
| 2 | 分析+建议 | system-review → brainstorming | 串行 | 审查/分析 + 改进/建议 |
| 3 | 诊断+修复 | systematic-debugging → verification-before-completion | 串行 | 报错/Bug + 修复 |
| 4 | 设计+实现 | brainstorming → writing-plans → executing-plans | 串行 | 设计 + 实现/开发 |
| 5 | 规划+并行 | subagent-driven-development | 并行 | 并行/多任务 + 调研 |

## 触发判定（混合策略）

**第一层：规则判定**（零 token）
- 关键词扫描：复用 skill-hub/SKILL.md 现有 53 技能关键词表
- 复合任务触发条件：
  - 意图数 ≥ 2
  - 关键词命中 ≥ 2 个不同技能的"触发关键词"
  - 满足上述任一 + 触发关键词属于同一"复合任务类型"

**第二层：LLM 验证**（仅在规则冲突时）
- 规则冲突：同时命中 ≥ 2 个复合任务类型
- 规则无匹配但 LLM 判断为复合
- 防御 LLM 自评盲点：列出 Top-2 类型用 AskUserQuestion 让用户选

## 不可触发场景（显式排除）

- 关键词命中 1 个 → 走 v5.4 单技能路径（不被升级到 Orchestrator）
- 关键词命中 ≥2 但属于"竞争关系"（冲突裁决）→ 走 v5.4 冲突裁决
- 触发词仅命中"Bug/报错" → 优先 systematic-debugging（按 v5.4 核心规则 #7）

## 显式触发

用户可使用 `/composite <type>` 前缀强制指定复合任务类型：
- `/composite 1 调研下 A 和 B 方案的优缺点`
- `/composite 5 并行调研 fastapi, django, flask 三个框架`

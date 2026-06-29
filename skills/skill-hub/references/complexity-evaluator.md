# 复杂度评估器（v6.0 Layer 2）

> 在意图分析层输出"意图向量"后，复杂度评估器决定走 v5.4 单技能路径还是 v6.0 Orchestrator 路径。

## 评估流程

```python
# 伪代码（实现参考）
def evaluate_complexity(user_input: str, intent_vector: list[str]) -> TaskType:
    # 1. 关键词扫描
    matched_skills = match_keywords(user_input)  # 复用 v5.4 关键词表

    # 2. 意图数判定
    if len(intent_vector) <= 1:
        return TaskType.SINGLE_SKILL

    # 3. 复合任务规则匹配
    composite_match = match_composite_pattern(intent_vector, user_input)
    if composite_match:
        return composite_match

    # 4. 默认走单技能
    return TaskType.SINGLE_SKILL
```

## 决策矩阵

| 输入特征 | 输出任务类型 | 路径 |
|---------|------------|------|
| 关键词命中 1 个 | SINGLE_SKILL | v5.4 路径 |
| 关键词命中 ≥2 但属于竞争 | SINGLE_SKILL（冲突裁决） | v5.4 路径 |
| 关键词命中 ≥2 属于互补 + 命中复合模式 | COMPOSITE | v6.0 Orchestrator |
| 关键词无匹配 + 语义兜底命中 1 个 | SINGLE_SKILL | v5.4 语义兜底 |
| 关键词无匹配 + 语义兜底命中多个且为互补 | COMPOSITE | v6.0 Orchestrator |
| 显式 `/composite <type>` 前缀 | COMPOSITE | v6.0 Orchestrator |

## LLM 验证触发条件

仅在以下情况启用 LLM 验证：
1. 规则冲突：复合模式同时匹配 ≥ 2 个类型
2. 规则无匹配：意图向量 ≥2 但未命中任何复合模式
3. 用户显式怀疑：用 `/clarify` 前缀请求 LLM 解释为何选/不选某个类型

**LLM 验证的硬约束**（在 `composite-task-types.md` 和 `plan-orchestrator-protocol.md` 同样引用）：
- 必须列出 Top-2 候选让用户选（防御 LLM 自评盲点）
- 不允许 LLM 单独决定
- 验证成本计入 token 预算

## 性能预算

- 规则判定：< 1ms（纯字符串匹配）
- LLM 验证：< 2k token（只输出 Top-2 候选 + 理由）
- 总开销：相对 v5.4 增加 < 5%（**注**：alpha 阶段为设计目标，未实际测量）

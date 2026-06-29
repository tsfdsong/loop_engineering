# Orchestrator 编排协议（v6.0 Layer 3）

> Orchestrator 在复合任务识别后，按本协议调度多个技能。

## 串行编排

**适用**：调研+决策 / 分析+建议 / 诊断+修复 / 设计+实现

**协议**：
```yaml
serial_execution:
  - step_1: {skill: brainstorming, input: <user_input>}
  - step_2: {skill: system-review, input: <user_input> + <step_1.summary>}
  - step_3: {skill: writing-plans, input: <user_input> + <step_1.summary> + <step_2.summary>}
```

**上下文传递（Mode B 默认）**：
- 每步只看前序 skill 的**最终结论摘要**（≤ 500 token）
- 摘要格式：```结论: ...  关键证据: ...  不确定项: ...```
- **不传递**前序 skill 的中间思考步骤

## 并行编排

**适用**：规划+并行（subagent-driven-development）

**协议**：
```yaml
parallel_execution:
  orchestrator: subagent-driven-development
  workers:
    - {subagent: "调研 fastapi", output_topic: "fastapi_overview"}
    - {subagent: "调研 django", output_topic: "django_overview"}
    - {subagent: "调研 flask", output_topic: "flask_overview"}
  synthesis: "对比 3 个框架的优缺点"
```

**冲突防御**：
- 内部串行化 MCP 工具调用
- 每个 subagent 独立工作目录（用 git worktree）

## 强制停止条件

```yaml
stop_conditions:
  max_steps: 5  # 防复合任务无限展开 → 触发 stop_reason: step_limit_exceeded
  max_duration_minutes: 10  # 防 hang 住 → 触发 stop_reason: timeout
  consecutive_identical_intents: 2  # 连续 2 步意图相同则中止 → 触发 stop_reason: loop_detected
  required_verification: verification-before-completion  # 每步必须验证
```

> `stop_reason` enum 完整定义见 `trace-format.md`：`completed / timeout / loop_detected / user_abort / user_decision_required / token_limit_exceeded / step_limit_exceeded / skill_failed`。

**中止后行为**：
1. 抛出结构化错误：`{trace_id, completed_steps, remaining_steps, stop_reason}`
2. 询问用户：重试 / 跳过未完成步 / 降级到单技能模式
3. 不静默失败

## 失败处理矩阵

| 失败类型 | 处理 |
|---------|------|
| 规则路由失败 | 降级到 LLM 兜底（同 v5.4 语义兜底） |
| LLM 验证失败（冲突） | 列出 Top-2 候选，AskUserQuestion 让用户选 |
| Skill 加载失败 | 跳过该步，记录错误，继续下一步 |
| Skill 执行失败 | 中止编排，问用户决策 |
| Token 预算超限 | 触发 headroom 压缩前序摘要 |
| 循环调用 | 强制中止，提示用户 |

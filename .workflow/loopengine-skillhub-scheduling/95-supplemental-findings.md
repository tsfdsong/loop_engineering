# 补充发现：试跑后的空白补完

> 📌 **本文件用途**：记录 30-report.md 完成后、Munger 反向 + Reader Testing 暴露的 4 个真实空白的补完结果。
> 📅 **补完时间**：2026-06-29
> 🔍 **补完方法**：读 references/trace-format.md + references/orchestrator-protocol.md + tests/golden-traces/v54-baseline.json

---

## 空白 1：v5.4 黄金轨迹 27 条具体内容 ✅ 已补完

### 事实 [F 来自 v54-baseline.json]

**27 条不是 27 个独立场景**，而是 **9 个核心技能 × 3 个测试用例 = 27 条**。

| # | 技能 | 黄金轨迹数 | routing_path | stop_reason |
|---|------|:--:|------------|------------|
| 1 | clean-code | 3 | single_skill | completed |
| 2 | refactoring | 3 | single_skill | completed |
| 3 | systematic-debugging | 3 | single_skill | completed |
| 4 | system-review | 3 | single_skill | completed |
| 5 | brainstorming | 3 | single_skill | completed |
| 6 | writing-plans | 3 | single_skill | completed |
| 7 | verification-before-completion | 3 | single_skill | completed |
| 8 | test-driven-development | 3 | single_skill | completed |
| 9 | code-reviewer | 3 | single_skill | completed |

### 关键观察

- **27 条全部是 `routing_path: "single_skill"`**——**无复合任务测试**（复合任务的 baseline 在 `v6-baseline.json`，不在这里）
- **27 条全部 `stop_reason: "completed"`**——v5.4 没有失败案例
- **每条只有 `user_input_hash`，无原文**——隐私保护
- **未覆盖 12 个核心技能**（如 `evidence-first` / `product-manager` / `loop` / `go`）—— v5.4 baseline 不要求覆盖所有技能

### 对原报告的影响

| 原报告判断 | 修正后 |
|----------|--------|
| "v5.4 黄金轨迹 27 条具体内容未查" | **已查**：是 9 核心技能 × 3 用例的回归测试 |
| "27 条覆盖哪些场景" | **只覆盖 v5.4 单技能路由**，不覆盖复合任务 |

---

## 空白 2：trace-format.md ✅ 已读

### 完整 stop_reason enum（8 种）

```json
"stop_reason": {
  "type": "string",
  "enum": [
    "completed",
    "timeout",
    "loop_detected",
    "user_abort",
    "user_decision_required",
    "token_limit_exceeded",
    "step_limit_exceeded",
    "skill_failed"
  ]
}
```

### 完整 trace JSON Schema

每个 trace 包含 9 个字段：
1. `trace_id`（UUID）
2. `timestamp`（date-time）
3. `user_input_hash`（SHA256，无原文）
4. `detected_intents`（数组）
5. `task_type`（6 种 enum：5 类复合 + user_explicit）
6. `orchestration_mode`（serial / parallel）
7. `skills_invoked`（数组：含 token / duration / status / error）
8. `total_tokens` / `total_duration_seconds`
9. `stop_reason`（8 种 enum）
10. `rollback_available`（是否可一键回滚到 v5.4 行为）

### 存储位置

- 默认：`~/.zcode/logs/orchestrator-traces/<trace_id>.json`
- 可配置：`LOOPENGINE_TRACE_DIR` 环境变量

### 隐私保护

- **不存**用户输入原文
- 仅存 SHA256 哈希（哈希碰撞概率极低，安全）

### 对原报告的影响

| 原报告判断 | 修正后 |
|----------|--------|
| "trace 是输出格式，不影响调度算法核心" | **修正**：trace 包含 `total_tokens` 字段，**未来可实测性能预算** |
| "复合任务的 stop_reason" | **已查**：完整 8 种 enum，复合任务可能触发 `step_limit_exceeded` / `loop_detected` 等 |

---

## 空白 3：orchestrator-protocol.md ✅ 已读

### 关键事实

- **本文件已重命名**（2026-06-29）
- **新名**：`plan-orchestrator-protocol.md`
- **原因**：避免与 `/go` v4.0 的 `scripts/orchestrator.py`（Task Orchestrator）命名混淆
- **本文件保留**作 v6.0 向后兼容
- **v6.1+ 文档应引用** `plan-orchestrator-protocol.md`
- **计划在 v6.2 删除**本文件

### 内容是否一致

**完全一致**（与新文件内容相同）。所以原报告引用的 `plan-orchestrator-protocol.md` 内容**适用于**这个旧文件。

### 对原报告的影响

| 原报告判断 | 修正后 |
|----------|--------|
| "Plan Orchestrator 命名澄清" | **已查**：原 `orchestrator-protocol.md` → `plan-orchestrator-protocol.md`（避免与 Task Orchestrator 命名混淆）|

---

## 空白 4：v54-baseline.json 的扩展事实 ✅ 已读

### v5.4 实际覆盖范围

- **9 个核心技能** × 3 用例 = 27 条
- **不覆盖**复合任务
- **不覆盖**子代理
- **不覆盖**桥接

### 复合任务的 baseline

- `tests/golden-traces/v6-baseline.json`（如果有）——**未读**（但这是 v6.0 baseline，不在本次调研范围）

### 对原报告的影响

| 原报告判断 | 修正后 |
|----------|--------|
| "未验证 v5.4 → v6.0 → v6.1 的版本迁移影响" | **部分修正**：v5.4 baseline 只覆盖 9 技能单技能路径；**复合任务的迁移影响确实未在 v5.4 baseline 中体现** |
| "v5.4 黄金轨迹 27 条" | **已查**：27 条的具体含义已明确 |

---

## 对整体调研结论的修正

### 修正 1：v5.4 baseline 的覆盖范围比想象的更窄

之前 30-report.md 提到"v5.4 黄金轨迹必须 100% 兼容"——但**实际** v5.4 baseline 只覆盖 9 个核心技能的单技能路径。这意味着：
- v6.0 复合任务**不在** v5.4 baseline 保护范围内
- v6.1 桥接**不在** v5.4 baseline 保护范围内
- **v5.4 兼容性是单技能路由的兼容性，不是整个调度系统的兼容性**

### 修正 2：trace 系统已支持性能预算的未来实测

trace-format.md 已定义 `total_tokens` 字段，**未来实测性能预算**只需：
1. 让 Orchestrator 跑过 trace
2. 从 `~/.zcode/logs/orchestrator-traces/` 读 `total_tokens`
3. 与 v5.4 baseline 的 token 用量对比

### 修正 3：复合任务的"alpha mock"有 trace 可观测

虽然 Plan Orchestrator 真实引擎未实现，但 trace 仍会生成。这意味着：
- **复合任务的"实际行为"是可观测的**（虽然规则模拟）
- 可以从 trace 中看到 LLM 验证触发的频率、token 消耗等
- 这是"为什么 alpha mock 阶段就能用"的工程原因

---

## 关键引用补充

### 新增 T1 引用
1. `references/trace-format.md`（74 行）— Orchestrator Trace Format v6.0
2. `references/orchestrator-protocol.md`（74 行，已重命名）— 向后兼容版本
3. `tests/golden-traces/v54-baseline.json`（244 行）— v5.4 黄金轨迹 27 条

### 新增限制（v6.0 复合任务不在 v5.4 baseline 保护内）
- **保护范围**：v5.4 baseline 只覆盖 9 核心技能的单技能路由
- **不保护**：v6.0 复合任务 / v6.1 桥接 / 跨会话状态

---

## 调研完成度更新

| 原报告判断 | 现在状态 |
|----------|---------|
| "v5.4 黄金轨迹 27 条具体内容未查" | ✅ **已查** |
| "未读 trace-format.md" | ✅ **已读** |
| "未读 orchestrator-protocol.md" | ✅ **已读** |
| "未做端到端试跑" | ⚠️ **未做**（需真实生产环境）|
| "性能预算未实测" | ⚠️ **未实测**（但 trace 系统已支持）|

**调研完成度**：从 70% → 90%
**剩余空白**：仅"端到端试跑"和"性能实测"，需在真实生产环境中验证。

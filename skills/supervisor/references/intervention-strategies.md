# Intervention Strategies — R1-R4 详细决策树

> 本文档定义 supervisor 的四档干预策略链（R1→R2→R3→R4）。
> 原则：从轻到重 · 能自动则自动 · 不能则上报 · 绝不静默放弃。

## 干预决策总览

```
检测到子任务异常
   │
   ├─ 异常类型？
   │
   ├─ 门禁失败（Gx ❌）      ────► R1 重启（≤2 次）
   │                              │
   │                              └─ R1 失败 2 次 ────► R2 降级
   │
   ├─ loop exhausted          ────► R2 降级（≤1 次）
   │                              │
   │                              └─ R2 失败 ────────► R4 上报
   │
   ├─ 依赖断裂（E 等 A·A fail）──► R3 重切 DAG
   │                              │
   │                              └─ R3 无法解决 ─────► R4 上报
   │
   └─ R1×2 + R2×1 均失败      ────► R4 上报（强制）
```

## R1 重启策略

- **触发条件**：门禁失败（Gx ❌）· 即子任务跑完代码但 quality_gate/test/lint 不过
- **动作**：
  1. 复用原 WorkerTaskPacket（相同 spec、相同 spec_hashes）
  2. 派发到**新 worktree**（`wt-<task>-retry-N`）
  3. 把上次失败的门禁日志作为 context 附带（避免重复犯同样错）
- **上限**：最多 2 次
  - 第 1 次：R1×1
  - 第 2 次：R1×2
  - 第 3 次仍失败：直接进 R2（不再 R1）
- **记录格式**：
  ```json
  {"strategy": "R1", "attempt": 1, "trigger": "G2_failed",
   "old_worktree": "../wt-T1", "new_worktree": "../wt-T1-retry-1",
   "ts": "2026-07-17T10:23:01Z"}
  ```

## R2 降级策略

- **触发条件**：
  - loop 状态为 `exhausted`（自愈预算耗尽）
  - 或 R1 重启 2 次仍失败
- **动作**：
  1. 读 `.loopengine.yaml` 的 `fallback_chain: [Primary, Secondary, Tertiary]`
  2. 当前级别 +1（Primary→Secondary）
  3. 用降级后的策略重派
  4. 摘要标 `degraded=true`
- **上限**：最多 1 次（避免无限降级链）
- **记录格式**：
  ```json
  {"strategy": "R2", "trigger": "loop_exhausted",
   "from_level": "Primary", "to_level": "Secondary",
   "worktree": "../wt-T1-deg-1", "ts": "..."}
  ```

## R3 重切策略

- **触发条件**：依赖断裂 · 如任务 E 依赖 A，但 A 永久 fail（已 R1×2+R2×1）
- **动作**：
  1. 重新计算 DAG
  2. 把 E 标为 `independent` 或换依赖到 B
  3. 需要 go 协同（supervisor 写建议 · go 确认后重派）
- **上限**：1 次（重切很贵 · 不反复）
- **记录格式**：
  ```json
  {"strategy": "R3", "trigger": "dep_broken",
   "task": "E", "old_dep": "A", "new_dep": "B",
   "dag_diff": "...", "ts": "..."}
  ```

## R4 上报策略（强制 · 红线）

- **触发条件**（任一）：
  - R1×2 + R2×1 都失败
  - R3 无法解决
  - 不可恢复的依赖错误
- **动作**：**必走 AskUserQuestion**（绝不静默放弃）
- **问题模板**：
  - header: `子任务 T<X> 卡住`
  - question: `T<X> 已 R1×2 + R2×1 失败 · 如何处理？`
  - options:
    1. 立即修复（我提供线索 · supervisor 转 R1）
    2. 登记后续（标 TODO · 跳过当前）
    3. 标记已知边界（写入 KNOWN_LIMITATIONS.md）
    4. 忽略（接受失败 · 继续 merge 其他）
- **记录格式**：
  ```json
  {"strategy": "R4", "trigger": "all_failed",
   "task": "T<X>", "asked_at": "...", "user_choice": "登记后续"}
  ```

## 干预计数器（防失控）

每个任务维护独立计数器：
- `r1_count`（默认上限 2）
- `r2_count`（默认上限 1）
- `r3_count`（默认上限 1）
- `r4_asked`（布尔 · 已上报则不再重复问）

任一计数器超上限 → 自动跳到下一档。

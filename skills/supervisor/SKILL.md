---
name: supervisor
description: |
  TRIGGER: go 派发多子任务后 / L2/L3 复杂任务并发 / 子任务卡住或降级 / "监控子任务" / "看门狗"
  RULE: 持续监控子任务状态（任务级 polling + 异常双轨）+ R1-R4 干预链（重启→降级→重切→上报）
  DETAIL: 本 SKILL.md + 状态文件 .supervisor-state.json 通信 + references/
---

# supervisor — 编排层监控看门狗（v2.0 · 痛点 4 专治）

> 痛点：复杂多子任务场景下完成度不高 · 总需用户干预
> 根因：缺 Supervisor 看门狗（go 派完任务就等 merge · 无持续监控）
> 解法：独立 agent 监控 + R1-R4 干预链 + 状态文件通信

## 核心定位

supervisor 是**独立 agent**（subagent），与 go 主流程**真物理并发**：
- go 主流程：拆 → 派 → 移交监控权 → 等 supervisor 汇报 → merge
- supervisor：持续监控 + 主动干预（R1-R4）+ 向 go 汇报

supervisor **不**接管：
- ❌ loop 内部自愈（A/B/C/🎨 分级 · loop 自己负责）
- ❌ 任务拆分（go 负责）
- ❌ merge（go 负责）

## 监控机制（任务级 polling + 异常双轨）

### 任务级 polling（v1.0）
- 每 N 秒（默认 30s · 可配）读各 worktree 的 `.loop-state-*.json`
- 提取状态：running / stuck / exhausted / done
- 汇总到 `.supervisor-state.json`

### 异常主动告警（v1.0）
- 监听关键事件：门禁失败 / loop exhausted / 依赖断裂 / 多次重试
- 异常立即触发干预（不等下次 polling）

## R1-R4 干预策略链（核心）

```
子任务卡住
  ├─ 门禁失败（Gx ❌）→ R1 重启（最多 2 次）
  ├─ loop exhausted → R2 降级（最多 1 次）
  ├─ 依赖断裂 → R3 重切 DAG
  └─ 多次失败 → R4 上报（必走 AskUserQuestion · 不静默放弃）
```

### R1 重启策略
- 触发：门禁失败（Gx ❌）
- 动作：用相同 WorkerTaskPacket 重派到新 worktree
- 上限：最多 2 次（第 3 次失败 → 进 R2）
- 记录：decision_log

### R2 降级策略
- 触发：loop exhausted / R1 重启 2 次仍失败
- 动作：按 `.loopengine.yaml` 的 fallback_chain 降级（Primary → Secondary → Tertiary）
- 上限：最多 1 次（再失败 → 进 R4）
- 记录：decision_log + 摘要标 `degraded=true`

### R3 重切策略
- 触发：任务依赖错了（如 E 等 A 但 A 永久失败）
- 动作：重新计算 DAG · 把 E 标为可独立或换依赖
- 灵活但复杂（需 go 协同）
- 记录：decision_log + DAG diff

### R4 上报策略
- 触发：R1×2 + R2×1 都失败 / R3 无法解决
- 动作：**必走 AskUserQuestion**（不静默放弃）
- 选项：立即修复 / 登记后续 / 标记已知边界 / 忽略
- 默认阈值：约 3-5 分钟后 R4 上报（R1×2 ≈ 2-3 分钟 + R2×1 ≈ 1-2 分钟）

## 与 go 的通信（状态文件）

### `.supervisor-state.json` 格式
```json
{
  "version": "1.0",
  "session_id": "<go-session>",
  "started_at": "ISO 8601",
  "tasks": [
    {
      "id": "T1",
      "worktree": "../wt-T1",
      "status": "running|stuck|exhausted|done|failed",
      "last_update": "ISO 8601",
      "interventions": ["R1×1", "R1×2"],
      "degraded": false
    }
  ],
  "summary": {
    "total": 5,
    "done": 3,
    "running": 1,
    "failed": 1,
    "r4_pending": false
  }
}
```

### 通信协议
- supervisor 写状态文件
- go 主流程轮询读状态文件
- 全完成（summary.done == total）或 r4_pending=true → go 进入 merge 阶段

## 与 loop 自愈的边界（重要）

| 层 | 职责 | 谁负责 |
|---|---|---|
| L1 自愈 | 单任务内部门禁失败的自愈（A/B/C/🎨 分级）| loop 自己 |
| **L2 Supervisor** | 子任务**间**的协调（重启/降级/重切/上报）| **supervisor** |
| L3 用户 | R4 上报后的最终决策 | 用户 |

**红线**：supervisor 不接管 loop 内部自愈（不重复造自愈闭环）。只在 loop exhausted 后才 R2 降级。

## 默认阈值

- R1 重启：最多 2 次
- R2 降级：最多 1 次
- R4 上报：约 3-5 分钟（R1×2 + R2×1）
- polling 间隔：30s（可配）

## 与 v2.0 红线的关系

| 红线 | 协同 |
|---|---|
| V3 Subagent 边界 | supervisor 本身是 subagent · 遵循 5 类必接输入 |
| V4 Worktree 隔离 | supervisor 监控的子任务必须在独立 worktree |
| V5 进度汇报 | supervisor 状态文件 = 进度汇报的细粒度版 |

## v2.0 与 spec-D 协同

- spec-E（已整合到 v2.0）：supervisor 是**单工具内**（ZCode 内）的监控 agent
- spec-D v1.5+：可升级为**跨工具** supervisor（多工具间监控）
- 本 skill 为单工具版 · 未来扩展见 spec-D

## 配置（`.loopengine.yaml`）

```yaml
supervisor:
  enabled_levels: [L2, L3]   # L1 不启动 supervisor（简单任务）
  r4_threshold: default      # default = R1×2 + R2×1
  polling_interval: 30       # 秒
```

不配置 → 默认值（L2/L3 启动 · R1×2+R2×1 · 30s polling）。

## references/

- `references/intervention-strategies.md` · R1-R4 详细决策树
- `references/state-protocol.md` · `.supervisor-state.json` 完整 schema
- `references/loop-boundary.md` · 与 loop 自愈的边界划分

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

---

## §N. 与 go/loop 协作（v2.0 强化 · 补 system-review 发现的 gap）

### 与 go 的协作时序

```
go Step ⑤ 派发
  ├─ 派 supervisor（subagent · 持续监控）
  ├─ 派 loop A/B/C（subagent · 各 worktree）
  └─ go 主流程等待 supervisor 状态文件

supervisor 启动后:
  1. 读 .loopengine.yaml · 确认 enabled_levels/r4_threshold/polling_interval
  2. 每 polling_interval 秒读各 worktree 的 .loop-state-*.json
  3. 异常立即触发 R1-R4
  4. 写 .supervisor-state.json（tasks 数组 + summary）
  5. 全完成或 R4 → 在 state 文件标 status=complete 或 r4_pending=true

go 主流程:
  - 每 N 秒读 .supervisor-state.json
  - summary.done == total → 进入 Step ⑥ merge
  - r4_pending=true → AskUserQuestion 上报用户
```

**通信契约（状态文件 = 唯一真源）：**
- supervisor **只写** `.supervisor-state.json`（不直接调 go）
- go 主流程**只读** state 文件（不主动问 supervisor）
- 这解耦了 supervisor 与 go 的生命周期（supervisor 可独立崩溃重启 · state 文件保留）

### 与 loop 的边界（不接管 loop 内部自愈）

| 场景 | 谁负责 | 动作 |
|---|---|---|
| loop 内门禁失败（Gx ❌）| loop 自己 | A/B/C/🎨 自愈分级 |
| loop exhausted（自愈失败）| supervisor 接管 | R2 降级（按 .loopengine.yaml fallback_chain）|
| loop done | supervisor 记录 | tasks[].status=done · summary.done++ |
| 依赖断裂（等永久的上游）| supervisor 接管 | R3 重切 DAG（需 go 协同）|
| R1×2 + R2×1 都失败 | supervisor 上报 | R4 AskUserQuestion（不静默放弃）|

**红线（最高优先级）：supervisor 不接管 loop 内部自愈。** 只在 loop exhausted（A/B/C/🎨 全失败）后才 R2 降级。越界 = 重复造自愈闭环 = 状态混乱。

### 与 go/loop 的三方协议（v2.0 通信矩阵）

| 信号流向 | 机制 | 频率 |
|---|---|---|
| go → supervisor | 启动时派发（Agent 工具）+ 读 `.loopengine.yaml` | 一次 |
| supervisor → go | 写 `.supervisor-state.json`（go 轮询读） | 每 polling_interval |
| loop → supervisor | 写 `.loop-state-*.json`（supervisor 轮询读） | 每门禁状态变更 |
| supervisor → loop | **不直接通信**（只通过 go 重派/R2 降级间接生效） | N/A |
| supervisor → 用户 | R4 时通过 go 触发 AskUserQuestion | 仅 R4 |

---

## §N. 端到端示例（v2.0 强化）

### 示例 1：3 子任务监控（R1 重启 + R2 降级 + 正常完成）

**上下文:** go 派发 3 子任务（T1 schema / T2 API / T3 test）· supervisor 启动监控

**supervisor 时序（polling_interval=30s · r4_threshold=default）：**

```
T+0:00   supervisor 启动 → 读 .loopengine.yaml → enabled_levels=[L2,L3] ✅
         初始化 .supervisor-state.json（tasks=[T1,T2,T3] · all running）
T+0:30   polling #1 → T1 done · T2 running · T3 waiting
         summary: {total:3, done:1, running:1, waiting:1}
T+1:00   polling #2 → T2 G3 ❌（test 失败）· loop 自愈 A 级触发中
         不干预（loop 自愈区间 · 红线）
T+1:30   polling #3 → T2 exhausted（A/B/C/🎨 全失败）
         🔴 触发 R1 重启 #1 → 重派 T2 到 wt-T2-v2 · interventions=["R1×1"]
T+3:00   polling #4 → T2-v2 再次 exhausted（同类 test 失败）
         🔴 触发 R1 重启 #2（上限）→ 重派 T2 到 wt-T2-v3 · interventions=["R1×1","R1×2"]
T+4:30   polling #5 → T2-v3 exhausted（R1 上限达成）
         🔴 触发 R2 降级 → 按 fallback_chain 切 DeepSeek · tasks[T2].degraded=true
T+6:00   polling #6 → T2 done（DeepSeek 降级产物）→ T3 启动
T+9:00   polling #7 → T3 done
         summary: {total:3, done:3, r4_pending:false}
         标 status=complete → go 读到 → 进入 Step ⑥ merge
```

**state 文件最终态（关键字段）：**
```json
{
  "tasks": [
    {"id":"T1","status":"done","interventions":[],"degraded":false},
    {"id":"T2","status":"done","interventions":["R1×1","R1×2","R2×1"],"degraded":true},
    {"id":"T3","status":"done","interventions":[],"degraded":false}
  ],
  "summary": {"total":3,"done":3,"r4_pending":false}
}
```

**go 读到后的动作:** T2 degraded=true → Step ⑧ 触发 🛑 人工闸门（不自动合并 · 交付报告含 R1×2+R2×1 决策追溯）。

### 示例 2：R4 上报（R1×2 + R2×1 全失败）

**上下文:** T2 是核心接口 · R1 重启 2 次 + R2 降级 1 次后仍失败

**supervisor 时序（接续示例 1 的 R2 失败分支）：**

```
T+6:00   R2 降级后 T2 仍 exhausted（DeepSeek 也搞不定 · 复杂度超模型能力）
         🔴 触发 R4 上报 → 标 r4_pending=true
         写 state: {summary:{done:2, failed:1, r4_pending:true}}
T+6:01   go 主流程轮询读到 r4_pending=true
         → AskUserQuestion 上报用户（不静默放弃）
```

**AskUserQuestion 选项（go 触发 · supervisor 提供 context）：**
- **立即人工修复**（推荐 · 核心接口不可降级交付）
- 登记后续（移入 backlog · 当前分支标 WIP）
- 标记已知边界（文档化限制 · 部分交付）
- 忽略（强制合并 · 风险自负）

**红线兑现:** R4 必走 AskUserQuestion · 不静默放弃 · 决策由用户做（L3 层）。

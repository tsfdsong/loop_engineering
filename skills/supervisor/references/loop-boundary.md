# Loop Boundary — supervisor 与 loop 自愈的边界划分

> 核心红线：**supervisor 不接管 loop 内部自愈**。
> 自愈闭环（A/B/C/🎨 分级）属于 loop · supervisor 只在 loop exhausted 后才介入。

## 三层职责划分

| 层 | 职责 | 触发者 | 执行者 | 工具 |
|---|---|---|---|---|
| L1 自愈 | 单任务内部 · 门禁失败的分级自愈 | loop 门禁 | **loop 自己** | A/B/C/🎨 分级 |
| L2 Supervisor | 子任务**间**协调 · 重启/降级/重切/上报 | supervisor polling 或异常 | **supervisor** | R1-R4 |
| L3 用户 | R4 上报后的最终决策 | supervisor R4 | **用户** | AskUserQuestion |

## 何时 supervisor 接管（L2 触发）

supervisor 仅在以下情况接管：

1. **loop exhausted**：loop 自愈预算（A/B/C/🎨）已耗尽 · 写状态 `exhausted`
   → supervisor 触发 R2 降级
2. **门禁反复失败**：R1 干预范围（loop 尚未 exhausted · 但已 stuck 多次）
   → supervisor 触发 R1 重启
3. **依赖断裂**：跨任务问题（E 等 A · A 永久失败）
   → supervisor 触发 R3 重切
4. **不可恢复**：R1×2+R2×1 都失败
   → supervisor 触发 R4 上报

## 何时交给 loop 自己处理（L1 保留）

以下场景 **supervisor 不介入** · 由 loop 自愈闭环处理：

| 场景 | loop 动作 | supervisor 动作 |
|---|---|---|
| 单次门禁失败 | A 级自愈（重试） | 不介入 |
| 测试失败 | B 级自愈（定位+修） | 不介入 |
| 编译失败 | C 级自愈（回退+重构） | 不介入 |
| 风格/文档 | 🎨 级（低优先级修） | 不介入 |
| 单任务内重试 | A/B/C 自愈预算内 | 不介入 |

## 判定流程

```
事件：子任务出现门禁失败
   │
   ▼
loop 是否还有自愈预算？
   │
   ├─ 是 ──► loop 自己处理（L1）· supervisor 仅记录
   │
   └─ 否（exhausted）
           │
           ▼
       supervisor 接管（L2）
           │
           ├─ R1 重启（≤2）
           ├─ R2 降级（≤1）
           ├─ R3 重切
           └─ R4 上报（→ L3 用户）
```

## 红线（不可逾越）

1. **supervisor 不重复造自愈闭环**：不在 supervisor 内实现 A/B/C/🎨 分级
2. **supervisor 不抢 loop 的活**：loop 还能自愈时 · supervisor 只观察
3. **supervisor 必走 R4**：所有自动干预失败后 · 必须上报用户（不静默放弃）

## 协同接口

- loop 写 `.loop-state-<task>.json`（含 `status`、`self_heal_budget_remaining`）
- supervisor 读 loop 状态 · 据此判断是否接管
- supervisor 写 `.supervisor-state.json`（含 interventions）
- loop **不读** supervisor 状态（单向 · loop 不依赖 supervisor）

## 反模式（禁止）

- ❌ supervisor 在 loop 未 exhausted 时 R2 降级（抢活）
- ❌ supervisor 实现自己的 A/B/C 分级（重复造轮子）
- ❌ supervisor 静默跳过失败任务（违反 R4 红线）
- ❌ loop 读 supervisor 状态改变自身行为（耦合）

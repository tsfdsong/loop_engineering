# G9/G10 协作契约（v6.1 共享 spec · 中优先级）

> **来源**：从 `skills/go/SKILL.md` 第 32 行 +
> `skills/loop/SKILL.md` 第 58 行 +
> `skills/loop/references/gate-matrix.md` 抽取 G9/G10 职责划分。
> **抽取原因**：G9/G10 协作规则散落 3 处，抽取后集中管理，避免职责重叠。

## G9 vs G10 职责边界

| 维度 | G9（loop 内） | G10（go 内） |
|------|--------------|--------------|
| **触发位置** | loop 每个子任务 commit 前 | go Step ⑦.5 交付前 |
| **调用对象** | `code-reviewer` 技能 | `system-review` 技能 |
| **检查范围** | `git diff HEAD~1` 单次提交 | `git diff main..feature-branch` 累积变更 |
| **触发频率** | 每个子任务都审查 | 每个特性分支审查一次 |
| **失败处理** | ERROR 触发自愈重试 / WARNING 记录到 handoff | ERROR 暂停交付 / WARNING 记录不阻断 |

## 硬约束

### loop 侧

1. **不重复触发 system-review**（G10 在 go 内一次性触发）
2. **只读 `handoff.gate_result` 字段**展示 G10 结果
3. **commit 前 G9 必须通过**（无 ERROR 级别问题）

### go 侧

1. **Step ⑦.5 必须调用 system-review**（不能跳过 G10）
2. **不调用 code-reviewer**（G9 由 loop 在子任务级别处理）
3. **G10 ERROR 暂停交付**，报告问题，等待人工

## 桥接模式（v6.1 新增 · opt-in）

当 `LOOPENGINE_BRIDGES=alpha` 启用时，可选启用 subagent-dd 作为 G9/G10 的替代实现：

### loop G9 桥接

```bash
# 默认（v6.1 行为不变）
/loop 实现分页功能
  └─ G9 = code-reviewer 审查单次提交

# 启用桥接
LOOPENGINE_BRIDGES=alpha /loop --reviewer=subagent-dd 实现分页功能
  └─ G9 = subagent-dd 三阶段循环
       （implementer → spec reviewer → code quality reviewer）
```

**契约**：
- 桥接时 G9 由 `subagent-dd` 的 `dispatch_code_quality_reviewer` 实现
- 仍需先过 `dispatch_spec_reviewer` 的 ✅ 判定（`review_gate` 强约束）
- 桥接失败时自动降级到 `code-reviewer`，不报错中断

### go G10 桥接

```bash
# 默认（v6.1 行为不变）
/go 实现订单管理功能
  └─ G10 = system-review 审查整特性分支

# 启用桥接
LOOPENGINE_BRIDGES=alpha /go --reviewer=subagent-dd 实现订单管理功能
  └─ G10 = subagent-dd final reviewer
       （人工子代理 + 3 层问题分级）
```

**契约**：
- 桥接时 G10 由 `subagent-dd` 的 `final reviewer` 实现
- 仍走 subagent-dd 的强顺序约束（spec ✅ → code quality）
- 桥接失败时自动降级到 `system-review`

## 桥接契约失败时的降级

| 桥接调用结果 | 降级策略 |
|------------|---------|
| `dispatch_implementer` BLOCKED | 降级到原 G9/G10 实现 + 记录 degraded_reason |
| `dispatch_spec_reviewer` 持续 ❌（>3 次） | 降级到原 G9/G10 + 记录 specs_stuck=true |
| `dispatch_code_quality_reviewer` 抛异常 | 降级到原 G9/G10 + 记录 bridge_error |
| `LOOPENGINE_BRIDGES=disabled` | 完全不加载桥接，走原 G9/G10 |

## 兼容性

- ✅ v5.4 G9/G10 行为 100% 兼容
- ✅ v6.0 G9/G10 行为 100% 兼容
- ✅ 桥接默认关闭，opt-in 启用
- ✅ 桥接失败自动降级，不破坏既有交付流程

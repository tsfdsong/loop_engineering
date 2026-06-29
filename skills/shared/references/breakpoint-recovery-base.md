# 断点恢复基础协议（v6.1 共享 spec · 中优先级）

> **来源**：从 `skills/go/references/breakpoint-recovery.md`（任务树级）+
> `skills/loop/references/state-protocol.md` 断点段（轮次级）抽取通用三步骤。
> **抽取原因**：步骤相同（一致性校验 → 搁置时长 → 状态定位），概念同源但实现分离。

## 三步骤协议

### Step 1: 一致性校验

| 检查项 | go 侧 | loop 侧 |
|--------|-------|--------|
| Git HEAD 对比 | `.orchestrate-state.json.tasks[].git_head_before` vs 当前 `git rev-parse HEAD` | `.loop-state-*.json.last_commit_sha` vs 当前 |
| 分支存在性 | `feature_branch` 是否存在 | 当前 worktree 分支是否存在 |
| Worktree 完整性 | `.go/worktrees/<task-id>/` 目录是否存在 | 当前 worktree 目录是否存在 |

**失败处理**：不一致 → 询问用户（resume / reset / abandon）。

### Step 2: 搁置时长检查

| 当前时间 - updated_at | 处理 |
|----------------------|------|
| < 1 小时 | 🟢 直接 resume |
| 1-24 小时 | 🟡 提示搁置时长，自动 resume |
| > 24 小时 | 🔴 强制询问用户（resume / reset / abandon） |

### Step 3: 状态定位

**go 侧（任务树级）**：
- 找到最后一个 `status: in_progress` 的子任务
- 读取其 `handoff.gate_result` 恢复执行上下文
- 6 类错误分类重试策略（详见 `breakpoint-recovery.md`）

**loop 侧（轮次级）**：
- 找到 `current_step` 和 `current_round`
- 恢复 `decision_log[]` 和 `blockers[]`
- 跳到该 step 继续执行

## 通用决策表

| 状态 | 决策 |
|------|------|
| `planning` | 从 Step 0 开始（重新评估计划） |
| `in_progress` | 从 current_step/current_task 继续 |
| `paused` | 询问用户 resume 还是 reset |
| `completed` / `failed` | 询问用户（re-run / abandon） |

## 双轨制实现

| 抽象层 | 文档位置 |
|--------|---------|
| go 任务树级 | `skills/go/references/breakpoint-recovery.md`（补充 6 类错误分类） |
| loop 轮次级 | `skills/loop/references/state-protocol.md` 第 55-64 行（轮次级处理） |

**铁律**：本 spec 只定义通用三步骤，各技能在自己的文档中补充特定实现细节。

## 兼容性

- ✅ 既有断点恢复逻辑 100% 保留
- ✅ 既有 .orchestrate-state.json / .loop-state-*.json 100% 兼容

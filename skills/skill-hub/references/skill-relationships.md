# 三技能协同契约（v6.1）

> 本文定义 `go` / `loop` / `subagent-driven-development` 三技能的调用边界、
> 状态协议共享、桥接模式与冲突场景的处理规则。skill-hub 在调度时按本文优先
> 于单技能默认行为。

## 1. 三技能定位（不可替换）

| 技能 | 抽象层 | 核心能力 | 不可替代点 |
|------|--------|---------|----------|
| **`go`** v4.0 | 编排层（Orchestrator） | 多任务拆分 + DAG + worktree 真并发 + 全局回归 | 唯一具备真并发 + 跨模块集成回归 |
| **`loop`** v4.1 | 执行层（Closer） | 单任务闭环 + 自动化门禁矩阵 + 自愈 A/B/C/🎨 | 唯一带自动自愈分级 + 经验库 |
| **`subagent-driven-development`** | 平行执行范式 | 多任务串行 + 人工子代理双阶段审查 | 唯一具备"spec ✅ → code quality"强顺序 + TDD 强制 |

**铁律**：三者**不互相替代**，调度时按本文第 3 节决策树选型。

## 2. 调用关系（硬约束）

### 2.1 `go` → `loop` 单向调用

```
go Step ⑤ 调度子任务
  └─→ 每个子任务 worktree 内调 loop --auto
       └─→ loop 完成 → 写 handoff.gate_result
            └─→ go 读 handoff 聚合 → Step ⑦ 全局回归
```

**规则**：
- `go` 调 `loop` 时**必须**传 `--auto`（无人值守）
- `loop` 在 `go` 的 worktree 内执行，**不创建嵌套 worktree**
- `loop` 不重复 `go` 的 6 维度需求分析（已在 go Step ①.5 完成）
- `loop` **不**重复调 `system-review`（G10 在 go Step ⑦.5 一次性触发）

### 2.2 `subagent-driven-development` 平行范式

```
subagent-driven-development 主会话层级
  ├─→ implementer subagent (TDD + commit + 自审)
  ├─→ spec reviewer subagent (规格合规审查)
  └─→ code quality reviewer subagent (质量审查)
```

**规则**：
- `subagent-dd` **仅在主会话层级**调用，**不**作为其他技能的子任务
- `subagent-dd` 派发的 subagent **不**再触发 Orchestrator 路径
- `subagent-dd` **不**与 `dispatching-parallel-agents` 互触发（详见第 4 节）

### 2.3 `subagent-dd` 与 `dispatching-parallel-agents` 的边界

| 维度 | `subagent-driven-development` | `dispatching-parallel-agents` |
|------|------------------------------|------------------------------|
| 触发场景 | **有 writing-plans 计划** + 任务相互独立 + 需 spec/code 双审 | **临时问题域分头调研**（无计划） |
| 任务来源 | 从 plan 文档顺序读 | 用户临时给出 N 个独立问题 |
| 审查机制 | 强顺序：spec ✅ → code quality | 无审查（仅并行执行） |
| 串/并行 | 任务间**串行** | 任务间**真并行** |
| 何时用 | "按计划走完 5 个任务" | "分头调研 A、B、C 三个库" |

**冲突裁决**：
- 有现成 plan → `subagent-driven-development`
- 临时多问题域并行调研 → `dispatching-parallel-agents`
- 同时出现 plan + 调研 → `subagent-driven-development` 主导，`dispatching-parallel-agents` 不触发

## 3. 调度决策树（v6.1 新增）

```
收到任务
  │
  ├─ 有现成 writing-plans 计划？
  │   ├─ 是 → subagent-driven-development
  │   │       └─ 强 TDD + spec/code 双审纪律场景
  │   └─ 否 ↓
  │
  ├─ 跨模块/需要 DAG/需要 worktree 真并发？
  │   ├─ 是 → go
  │   │       └─ 默认调 loop --auto 执行子任务
  │   │       └─ 可选 LOOPENGINE_BRIDGES=alpha --reviewer=subagent-dd 增强 G10
  │   └─ 否 ↓
  │
  ├─ 端到端单任务闭环 + 自动化门禁 + 自愈？
  │   ├─ 是 → loop
  │   │       └─ 默认走 --default 模式（自适应 L1/L2/L3）
  │   │       └─ 可选 LOOPENGINE_BRIDGES=alpha --reviewer=subagent-dd 增强 G9
  │   └─ 否 ↓
  │
  └─ 临时多问题域并行调研（无 plan）？
      └─ 是 → dispatching-parallel-agents
```

## 4. 状态协议共享（双轨制 + 共享 spec）

### 4.1 双轨制声明

| 状态文件 | 抽象层 | 负责技能 | 存放位置 |
|---------|--------|---------|---------|
| `.orchestrate-state.json` | **宏观**（任务树） | `go` | 项目根目录（feature 分支上） |
| `.loop-state-<slug>.json` | **微观**（单任务） | `loop` | worktree 目录内 |

**铁律**：两份状态文件**不合并**（合并会破坏分层设计），但**共享 owner 字段规范**（详见 `shared/references/owner-field-spec.md`）。

### 4.2 共享 spec 清单

| 共享 spec | 用途 | 两边引用 |
|----------|------|---------|
| `shared/references/owner-field-spec.md` | 并发占用控制（pid/session_id/heartbeat） | go + loop state-protocol |
| `shared/references/atomic-write-spec.md` | 状态文件原子写规范（tempfile + os.replace） | go + loop state-protocol |
| `shared/references/state-protocol-base.md` | 状态机通用定义（planning → in_progress → ...） | go + loop state-protocol |
| `shared/references/breakpoint-recovery-base.md` | 断点恢复三步骤 | go + loop |
| `shared/references/g9-g10-coordination.md` | G9/G10 协作契约 | loop G9 + go G10 |

## 5. 桥接模式（v6.1 新增 · opt-in）

### 5.1 灰度开关

```bash
# 默认（不启用）
LOOPENGINE_BRIDGES=disabled    # 默认值，不加载 subagent-dd 桥接

# 启用桥接（alpha）
LOOPENGINE_BRIDGES=alpha       # 加载 bridges/contract.py，允许 --reviewer 选项
```

**铁律**：
- **默认关闭**（100% 兼容 v5.4/v6.0）
- 启用时仅加载桥接组件，不改变原有 G9/G10 默认实现
- 桥接失败时**自动降级**到原 G9/G10，不报错中断

### 5.2 桥接契约（6 个核心）

| 桥接组件 | 输入 | 输出 | 替换关系 |
|---------|------|------|---------|
| `dispatch_implementer` | task_text, context, workdir, model_tier | `ImplementerStatus` 枚举 | 替代 G9 内的 commit 前自审 |
| `dispatch_spec_reviewer` | requirements, implementer_report | `SpecVerdict`（✅/❌） | 替代 G9 内的 spec 审查 |
| `dispatch_code_quality_reviewer` | task_summary, base_sha, head_sha, plan_ref | `QualityAssessment`（3 层 Issues） | 替代 G9/G10 内的质量审查 |
| `model_select` | task_signals | 'cheap'/'standard'/'capable' | 提供模型选型信号 |
| `handle_implementer_status` | status, report | 应对动作 | 处理 BLOCKED/NEEDS_CONTEXT 等 |
| `review_gate` | spec_verdict, quality_assessment | bool | 强顺序约束：spec ✅ → code quality |

**完整定义**：见 `subagent-driven-development/bridges/contract.py`

### 5.3 与 go 的集成（Step ⑦.5 G10）

```bash
# 默认（v6.1 行为不变）
/go 实现订单管理功能
  └─ G10 = system-review 审查整特性分支

# 启用桥接
LOOPENGINE_BRIDGES=alpha /go --reviewer=subagent-dd 实现订单管理功能
  └─ G10 = subagent-dd 的 final reviewer
       （人工子代理 + 3 层问题分级 + 顺序约束）
```

### 5.4 与 loop 的集成（G9 commit 前）

```bash
# 默认（v6.1 行为不变）
/loop 实现分页功能
  └─ G9 = code-reviewer 审查单次提交

# 启用桥接
LOOPENGINE_BRIDGES=alpha /loop --reviewer=subagent-dd 实现分页功能
  └─ G9 = subagent-dd 三阶段循环
       （implementer → spec reviewer → code quality reviewer）
```

## 6. 冲突场景与处理规则

### 6.1 同一任务可被多个技能匹配

| 场景 | 命中技能 | 裁决 |
|------|---------|------|
| "审查项目架构" | system-review / subagent-dd | → system-review（项目级）/ subagent-dd（计划级） |
| "实现分页 + 还要做权限" | loop × 2 | → loop（默认）/ go（需并发） |
| "并行调研 A、B、C" | subagent-dd / dispatching-parallel-agents | 见 §2.3 |
| "调试 + 修代码" | systematic-debugging / loop | → systematic-debugging（先诊断） → loop（再执行修复） |

### 6.2 技能执行中的边界违规检测

| 违规类型 | 检测信号 | 处理 |
|---------|---------|------|
| `loop` 重复触发 `system-review` | skill-hub 监控到 system-review 在 1 个 loop 会话内被调 ≥ 2 次 | 警告 + 强制走 `handoff.gate_result` 路径 |
| `subagent-dd` 在 subagent 内部调 Orchestrator | subagent 触发 `/composite` 或 `/go` | 静默降级到当前会话的 LLM 兜底 |
| `go` 内 `loop` 写 `.orchestrate-state.json` | `loop` 越权写非自己 worktree 目录的状态文件 | 警告 + 回滚（仅写 `.loop-state-*.json`） |
| `loop` 内 `systematic-debugging` 修复结果回写 `go.decision_log` | `systematic-debugging` 写非本会话 `.orchestrate-state.json` | 拒绝 + 提示用户手动同步 |

## 7. 兼容性承诺

| 基线 | 保护策略 | 检查点 |
|------|---------|--------|
| v5.4 黄金轨迹 27 条 | skill-hub 单技能路由 100% 兼容 | `tests/golden-traces/v54-baseline.json` 不动 |
| v6.0 复合任务 5 类表 | 调度行为不变 | `tests/golden-traces/v6-baseline.json` 不动 |
| `.orchestrate-state.json` 字段 | owner/decision_log 字段定义保持 | 既有 state 文件全部仍可加载 |
| `.loop-state-*.json` 字段 | 同上 | 同上 |
| 桥接默认关闭 | `LOOPENGINE_BRIDGES=disabled` 不加载 bridges/ | `contract.py` 入口检查 env var |

## 8. 不在本文范围

- ❌ 三技能功能合并（已明确禁止）
- ❌ Orchestrator 真实引擎实现（仍 alpha mock）
- ❌ state-protocol 双轨制合并（已明确禁止）
- ❌ loop 与 go 状态文件互通写入（owner 字段共享 ≠ 互相写入）

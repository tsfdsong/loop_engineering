# Design: loop 纯化为薄执行环（对齐流行 closed-loop）

> **日期**: 2026-07-21  
> **状态**: **Approved** · 2026-07-21  
> **动机**: loop 被定位为「执行层」，却承载需求确认 + spec-driven-development 级计划，与 go / brainstorming 重叠，且偏离业界「loop = 编码↔验证↔自愈」语义。  
> **相关**: `docs/2026-07-21-go-dag-parallel-frontier-design.md`（并行调度）；本设计只收窄 **loop 职责**。

## 0. 核心目的

将 **loop** 收敛为单任务 **闭环执行器**：

```text
已有可执行目标 + 验收 → 编码 ↔ 门禁/验证 ↔ 自愈 → 交付
```

**不再**作为迷你编排器做产品级需求调研或完整实施计划。

成功标准：

1. 裸 `/loop` 在验收齐全时尽快进入编码+门禁，无「需求理解是否正确」确认轮。  
2. `/go` → loop 无二次需求分析、无 spec-driven-development。  
3. 与 brainstorming / go 的职责表无「需求确认」三处重复。

## 1. 问题陈述

| 层 | 口号 | 实际（纯化前） |
|----|------|----------------|
| go | 编排 | 含 Step ①.5 六维需求分析 + DAG |
| loop 默认 | 执行层 | Step ① 需求确认 + ② 复杂度/轮次 + ③ spec-driven-development |
| brainstorming | 探索 | 未定型需求/选型 |

结果：分层名不副实；solo `/loop` 与 go 子任务路径行为分裂；小任务也偏慢。

## 2. 已确认决策

| # | 决策 | 选择 |
|---|------|------|
| D1 | 与流行 loop 对齐 | **薄执行环**（方案 A） |
| D2 | 产品级需求 | **brainstorming**（未定型）/ **go**（大活分析） |
| D3 | 编排与拆分 | **仅 go**（及上游 plan）；loop 不做 spec-driven-development |
| D4 | 轻 intake | **仅**缺可测验收时 A+D 补短清单；默认审计闸门不拦 |
| D5 | go→loop | **强制**执行态（`--auto` 或等价）；缺 goal/验收则失败回交 |
| D6 | 模糊需求 | 提示走 brainstorming；**不**在 loop 内开长确认流 |

## 3. 目标分层

```text
brainstorming     未定型：探索 / 选型 / 设计草稿
       ↓（可选）
go                大活：项目分析 / DAG / 并行 / 汇合
       ↓ 任务包（goal + 验收已可执行）
loop              编码 ↔ 门禁 ↔ 自愈 ↔ 交付
```

**loop 一句话定位**：单任务闭环执行器——把代码改对并门禁全绿。

## 4. 行为变更

### 4.1 裸 `/loop`（纯化后默认）

| 步骤 | 纯化前 | 纯化后 |
|------|--------|--------|
| 需求确认 Ask | 有 | **删除** |
| 验收补全 (A+D) | 有，常伴随确认 | **保留**：仅缺可测验收时补短清单，默认不 Ask |
| 复杂度/轮次 Ask | 有 | **删除**；L 来自 `--level` / `--lite|--full` / 默认 L2 |
| spec-driven-development 拆分 | 有 | **删除**；最多内部 1–3 条改动要点（不落计划文件、不问用户） |
| Git 隔离 | 有 | **保留** |
| 门禁 / 自愈 / 验证官 / 交付 | 有 | **保留**（核心） |

### 4.2 `/loop --auto` 与 go 子任务

- **禁止**产品需求确认、**禁止** spec-driven-development（含「自动拆分」）。  
- 任务包必须含可执行 `goal` + 验收；否则 **非 0 语义失败**，回交调用方。  
- L 级别：优先消费 go 传入；勿重新做编排级评估。  
- 已在 `go-*` worktree：复用隔离（现状保留）。

### 4.3 模糊输入

检测到明显未定型（纯选型/「要不要做 X」）→ **一句提示**建议 brainstorming 或 `/go`，不进入旧 Step ① 确认流。

## 5. 文档与代码改动面（实施时）

| 路径 | 动作 |
|------|------|
| `skills/loop/SKILL.md` | 重写定位与流程；去掉「需求分析→计划」主路径 |
| `skills/loop/references/mode-default.md` | 按 §4.1 变薄 |
| `skills/loop/references/mode-auto.md` | 删除/空壳 ②–③ 计划；强化任务包前置条件 |
| `skills/loop/references/acceptance-inference.md` | 降级为「仅补验收」可选 |
| `skills/using-loopengine/SKILL.md` | loop 描述改为执行环；指向 brainstorming/go 做上游 |
| `skills/go/SKILL.md` | 明确：派 loop 时必须带齐验收；loop 不再二次分析 |

**不改**：gate-matrix、self-healing、verification-officer 协议主体；go Step ①.5 仍属编排层。

## 6. 非目标

- 删除 `/loop` 命令或强制人人先 `/go`  
- 新建第四个「执行专用」slash 命令  
- 把 brainstorming 并入 loop  
- 本设计内实现 DAG 并行（见并行前沿专项）

## 7. 测试 / 验收（文档与行为）

1. SKILL/using-loopengine 中无「loop 主路径含需求确认 + spec-driven-development」。  
2. mode-default 无 Ask「需求理解是否正确」。  
3. mode-auto 写明：缺验收 → 失败，不本地补做六维分析。  
4. 与 go/brainstorming 职责表一致（可放在 using-loopengine）。

## 8. 反选项

| 方案 | 否决理由 |
|------|----------|
| 仅改文档仍保留厚流程 | 名实继续分裂 |
| 双模：solo 仍重 intake | 用户已选纯化 A |
| 需求确认三处都留、靠纪律不重复 | 已被证明易漂 |

## 9. 实施分期

| 期 | 内容 |
|----|------|
| **P0** | SKILL + mode-default/auto + using-loopengine 文案与流程纯化 |
| **P1** | go 派发约定（任务包必含验收）交叉引用 |
| **P2** | 可选：模糊输入探测提示（非阻断） |

Approved 后实施；用户可要求跳过冗长 plan 直接 `/loop` 改文档。

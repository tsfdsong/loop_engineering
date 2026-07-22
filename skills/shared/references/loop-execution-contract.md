# Loop Execution Contract（薄契约 · 单点真源）

> **用途**：brainstorming spec 与 spec-driven-development plan 的共享输入契约。  
> **不替代**：`loop` 门禁矩阵、`go` thin-loop 派发、`goal-first` 降级实现细节。  
> **原则**：上游只定义**可判定完成条件**与**何时必须停止/回交**；执行器负责 gate、自愈、degrade。

---

## 1. 分层职责

| 层 | 产物 | 契约字段 |
|----|------|----------|
| **brainstorming** | design spec | Goal · Acceptance · Non-goals · Stop Escalation |
| **spec-driven-development** | implementation plan | 继承 spec + Verification · Termination · Escalation Mapping |
| **goal / loop / go** | 运行时执行 | 消费契约；不发明验收、不静默降标（见 `skills/loop/SKILL.md` · `skills/go/SKILL.md` Thin-loop 派发） |

```text
brainstorming spec（Acceptance Contract）
       ↓
spec-driven-development plan（Verification + Termination）
       ↓
/goal 或 /loop 或 /go → 编码 ↔ 验证 ↔ 自愈/降级 → handoff
```

---

## 2. Spec 级字段（brainstorming 必填）

### 2.1 Goal

一句话**可执行**目标。禁止选型问句（「要不要做 X」）、禁止模糊动词（「优化」「完善」）无判据。

```markdown
## Goal

实现用户列表第 2 页分页，翻页后展示正确数据。
```

### 2.2 Acceptance Contract

每条验收必须**可观察、可判定**；优先映射到未来可跑的验证命令或检查动作。

| 规则 | 说明 |
|------|------|
| 句式 | 「当 … 时，… 应为 …」或「运行 … 应得到 …」 |
| 禁止 | 「正常工作」「体验良好」「无明显问题」 |
| 数量 | 简单任务 1–3 条；复杂任务按里程碑分组 |

```markdown
## Acceptance Contract

- [ ] 访问 `/users?page=2` 时，列表展示第 11–20 条用户
- [ ] `pytest tests/users/test_list.py::test_page_2 -v` 退出码 0
- [ ] 第 1 页与第 2 页无重复 user id
```

### 2.3 Non-goals

明确**不属于本轮**的范围，防止 loop 执行期 scope creep。

```markdown
## Non-goals

- 不重构全站分页组件
- 不新增用户导出功能
- 不做移动端适配
```

### 2.4 Stop Escalation

设计阶段出现下列情况时**停止假设、回问用户或转上游**，不在 spec 里硬编验收：

| 触发 | 动作 |
|------|------|
| 验收无法写成可判定句 | AskUserQuestion 澄清成功标准 |
| 存在 ≥2 种互斥产品路径且未决 | 回到方案对比，不进入 plan |
| 依赖外部系统/凭证未知 | 标 `blocked`，列所需输入 |
| 范围已超单 spec 可承载 | 拆子项目，各写独立 spec |

```markdown
## Stop Escalation

- 若分页 API 契约未确认 → 停止，先与用户确认接口字段
- 若需改数据库 schema → 拆为独立子 spec，不与本 bugfix 混编
```

**禁止写入 spec**：G0–G10 名称、retry 轮次、self-healing 级别、Goal→loop 降级链全文。

---

## 3. Plan 级字段（spec-driven-development 必填）

Plan **继承** spec 的 Goal / Acceptance / Non-goals，并新增以下**计划级**块（写一次，task 内引用，不逐 task 重复）。

### 3.1 Verification Contract

| 验收条目 | 验证命令/动作 | 预期结果 | 失败时 |
|----------|---------------|----------|--------|
| … | `pytest …` / `npm test` / snapshot 断言 | exit 0 / 具体输出 | 见 Termination |

```markdown
## Verification Contract

| ID | 来源验收 | 命令/动作 | 预期 |
|----|----------|-----------|------|
| V1 | Acceptance #1 | `pytest tests/users/test_list.py::test_page_2 -v` | 0 failures |
| V2 | Acceptance #2 | 手动：page=1 与 page=2 各取 id 集合 | 交集为空 |
```

### 3.2 Termination Contract

只使用以下四种终态（与 `go` handoff / `goal-first` 对齐）：

| 终态 | 含义 | 典型条件 |
|------|------|----------|
| **done** | 目标达成，可交付 | 全部 Acceptance + Verification 通过 |
| **blocked** | 缺外部输入/权限/决策，无法继续 | Stop Escalation 触发且未解除 |
| **degraded** | 以已知降质方式交付（须显式标记） | 降级链产物、部分验收 waived（须用户批准） |
| **handoff-required** | 本子任务边界结束，交上游编排 | 多模块 plan 中单 task 完成；或需 go 汇合/G10 |

```markdown
## Termination Contract

**Done when:** V1–V2 全绿，且 git diff 仅触及 `src/users/list.*` 与对应测试。

**Blocked when:** 后端分页 API 无 `total` 字段且无法从现有响应推断。

**Degraded when:** （本轮不适用）

**Handoff-required when:** 本 plan 仅覆盖后端；前端联调由后续 plan 承接。
```

### 3.3 Escalation Mapping

| 情况 | 交给 |
|------|------|
| 单任务、验收齐全 | `/loop` 或宿主 `/goal`（Goal-first 宿主） |
| 多 task / 跨模块 / 需 worktree 并发 | `/go` |
| Goal achieved | handoff 回 go，`executor=goal` |
| Goal stagnation / budget / unavailable | 降级 `loop`，`degraded_from=goal` |
| loop exhausted（自愈耗尽） | supervisor R2 或 go 重派 / 人工闸门 |
| spec 与实现不一致（架构级） | 暂停执行，回 brainstorming 或 system-review |

```markdown
## Escalation Mapping

- 执行路径：`/loop --level=L2`（单文件 + 测试）
- Goal-capable 宿主可先用 `/goal replace …验收…`，未达成再 loop
- 若需同时改 orders 模块 → 改 `/go`，不强行单 loop
```

---

## 4. 与执行器的映射

| 契约字段 | goal | loop | go |
|----------|------|------|-----|
| Goal + Acceptance | objective 正文 | 任务包前置条件 | thin-loop 任务包硬要求 |
| Verification | evaluator 可引用 | G1–G9 / F1–F5 证据来源 | Step ⑦ 回归 |
| Termination: done | achieved | 交付 / handoff | 子任务 done |
| Termination: blocked | clear + 上报 | 失败回交 | `missing_*` / 暂停 DAG |
| Termination: degraded | — | handoff.degraded | 人工合并闸门 |
| Non-goals | 不在 objective 内扩 scope | 禁止静默降标 | 拆分边界 |

详规：`skills/loop/SKILL.md` · `skills/go/SKILL.md` · `docs/2026-07-21-goal-first-executor-routing-design.md`

---

## 5. 最小反模式

| 反模式 | 后果 |
|--------|------|
| spec 写 G0–G9 全文 | brainstorming 变厚 loop，双真源 |
| 每 task 重复 Termination 四表 | 文档税，执行器仍各猜各的 |
| Acceptance 用主观词 | goal/loop 无法机械判定完成 |
| plan 与 spec 验收不一致 | verification-officer / G10 冲突 |
| 无 Non-goals | loop 顺手改邻域，难终止 |

---

## 6. 自检清单（写完后 30 秒）

**Spec（brainstorming）**
- [ ] Goal 一句话可执行
- [ ] Acceptance 每条可判定，无「正常/良好」
- [ ] Non-goals ≥ 1 条（或显式「无」）
- [ ] Stop Escalation 列出会阻断设计的未知项
- [ ] 未复制 gate 矩阵 / 自愈状态机

**Plan（spec-driven-development）**
- [ ] Verification 表覆盖全部 Acceptance
- [ ] Termination 仅用 done/blocked/degraded/handoff-required
- [ ] Escalation 指明 loop / go / goal 路径
- [ ] Task 引用 V-id，不重复写终态矩阵

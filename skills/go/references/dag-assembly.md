# DAG Assembly（v2.0 · rule-first · D4.1）

> go Step 0 的 DAG 组装 + confidence gate 能力真源。
> 运行时真源：`skills/go/references/dag-rules.yaml` + `skills/go/SKILL.md` Step 0 执行流程。

## rule-first DAG 组装

按规则表决定拓扑（不自由发明 DAG）。三种拓扑类型：

| 拓扑 | 触发条件 | 示例 |
|---|---|---|
| **串行（order）** | 同 family 内默认动作有依赖 | `debug_root_cause → fix_issue → verify_result` |
| **并行（parallel）** | bootstrap 后的多路探查无依赖 | web_qa 的 4 路审计 |
| **串接（combination）** | 白名单组合内，前置输出桥接后置输入 | `refactor → test` 经 `refactored_modules` |

### 串行 vs 并行判断规则

1. 默认串行（`order`）
2. 仅当 family 定义中显式声明 `parallel:` 字段时才并行
3. 并行节点都依赖同一 bootstrap 节点的输出
4. append 节点（report/plan）在拓扑末端聚合所有并行输出

### 拓扑序调度

- 串行：按 `order` 数组下标递增
- 并行：同一 `parallel` 组内任意顺序（真并发）
- append：所有非 append 节点完成后才执行
- 组合：前置 family 全部 append 完成后，桥接字段传给后置 family

### 可并发节点标记

仅以下节点允许并发：
- `web_qa.parallel` 中的 4 路（regression / visual / a11y / perf）
- `parallel_investigation.bootstrap` 的多个 probe 目标
- Step ③ L3 拆分后无依赖的子任务（按 Worker Contract v5 调度）

## confidence gate

来自原 `dag-rules.yaml > global.confidence_bands`：

| 置信度 | 行为 |
|---|---|
| `< 0.70` | AskUserQuestion 澄清 |
| `0.70 - 0.84` | 展示 Plan Preview 并确认 |
| `≥ 0.85` | 自动执行 |

### 置信度评估信号

- family 命中明确度（用户目标直接匹配 family 关键词）
- actions[] 抽取完整度（goal + scope + actions 三要素齐全）
- 是否落在白名单组合（组合命中 → 置信度更高）
- 多 family 但非白名单 → 直接降到 `< 0.70`

## 与 go Step ③ 任务拆分的协同

- **Step 0**（family-first 识别，见 `family-routing.md`）：定 family + 抽 actions[]
- **Step ③ 拆分**（按 L 级别 · L1/L2/L3）：把 actions[] 拆成可执行子任务
- **DAG 组装**（本文件 · 拓扑序）：决定子任务串/并/组合
- **Step ⑤ 调度**（按拓扑序 + Worker Contract v5 + Agent 多 subagent）：物理执行

```text
Step 0 family 识别
    ↓
family.actions[] + scope + goal
    ↓
Step ③ 按 L 级别拆分（L1 不拆 / L2 串行 / L3 + 并行）
    ↓
DAG 组装（本文件 · 拓扑序 + 并行标记 + append 聚合）
    ↓
confidence gate（< 0.70 澄清 / 0.70-0.84 确认 / ≥ 0.85 自动）
    ↓
Step ⑤ 调度（Agent 多 subagent · 见 SKILL.md Step ⑤ 改版）
```

## 组合 DAG 桥接规则

来自原 `dag-rules.yaml > combination_rules`：

| 组合规则 | sequence | bridge 字段 |
|---|---|---|
| `refactor_then_test` | `[refactor, test]` | `handoff.refactored_modules` |
| `review_then_refactor` | `[review, refactor]` | `handoff.review_findings` |
| `debug_fix_then_test` | `[debug_fix, test]` | `handoff.fixed_modules` |
| `design_build_then_test` | `[design_build, test]` | `handoff.built_modules` |
| `web_qa_then_debug_fix` | `[web_qa, debug_fix]` | `handoff.web_qa_findings` |
| `web_qa_then_refactor` | `[web_qa, refactor]` | `handoff.review_findings` |

桥接语义：前置 family 的 append 输出写入 handoff 的 bridge 字段，后置 family 读取该字段作为输入 scope。

## 并行前沿（parallel frontier）

> 调度真源：Approved `docs/2026-07-21-go-dag-parallel-frontier-design.md` §§4–5。
> go Step ⑤ 按前沿迭代派发；Subagent 仅为执行器，**不设**角色注册表。

### 算法

DAG 组装 + confidence gate 通过后：

1. **初始化**：`frontier` = 所有依赖已满足（入度为 0 或前置节点 `DONE`）且状态为 `pending` 的节点。
2. **并行安全判定**：对 `frontier` 内候选写码节点，两两检查写集是否冲突（见下）。
3. **派发**：对通过判定的子集，每个节点 → 独立 worktree + 短任务包 → 宿主并行派执行器（loop 闭环 via 任务包 SKILL 指针）。
4. **汇合**：前沿内全部 `DONE` 或失败策略触发后 → merge/handoff → 重算下一 `frontier`，直到 DAG 耗尽。

```text
family → DAG 组装 → confidence gate
    ↓
frontier = { deps 满足 ∧ pending }
    ↓
并行安全过滤（写集 / worktree）
    ↓
一次派齐可并行节点 → 汇合 → 下一 frontier
```

### 并行安全条件

节点可同前沿并行，当且仅当满足其一：

| 条件 | 说明 |
|---|---|
| **写集不交** | 各节点 `write_set`（或 scope 推断路径）两两无交集 |
| **worktree 隔离** | 各节点在独立 worktree，且无共享可写路径（V4） |

**冲突 → 串行**：写集重叠且无法 worktree 隔离的节点 **禁止** 同前沿；保留依赖序，改串行派发。

可选节点字段（`dag-rules` / Step ③ 输出，最小标注）：

- `parallel_safe: true|false` — 显式声明是否允许与同前沿其他节点并行
- `write_set: [path, ...]` — 预期修改路径，供冲突检测

未标注时：由 scope + family 推断写集；推断不确定 → 保守串行。

### 默认开启与降级

| 场景 | 行为 |
|---|---|
| **≥2 无依赖写码子任务** | 默认尝试并行派发（非仅文档建议） |
| **L1 / 单写码节点** | 跳过并行调度税，直通 loop |
| **宿主无法多 Task** | 降级顺序执行（见 `cursor-dispatch-protocol.md` degradation） |
| **写集冲突** | 同前沿剔除冲突对，按拓扑序串行 |

进度汇报（V5）：前沿并行中须在状态/日志可见「frontier parallel: N nodes」。

### 测修多域并行（P1）

写码前沿之外，**测修（C）** 按独立失败域切片后复用同一前沿概念（设计 doc §5）：

- **触发**：测试门禁或多文件失败，且失败可分成独立域（不同包/用例/子系统，无共享根因假设）。
- **行为**：每域一个短任务包（`systematic-debugging` 或 loop-fix 指针 + 复现命令）→ 并行派执行器；**禁止**多域改同一 worktree。
- **汇合**：全域完成后 **一次** 聚合验证（脚本跑测试）。
- **不并行**：失败明显同源、或修复会互相覆盖 → 单执行器串行。

P0 先落地写码前沿；测修多域并行为 P1 指针，调度接口与写码前沿相同。

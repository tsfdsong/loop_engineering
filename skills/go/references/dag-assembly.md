# DAG Assembly（吸收自 orch v2.0 · v2.0 整合 spec-E · D4.1）

> 本文件承载原 orch 的 DAG 组装 + confidence gate 能力。
> 运行时真源（v2.0 迁移）：`skills/go/references/dag-rules.yaml` + `skills/go/SKILL.md` Step 0 执行流程。

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

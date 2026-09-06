# G9/G10 审查协调（单点真源）

> go 编排的两级审查门职责切分。被 `skills/go/SKILL.md`（Step ⑦.5）与
> `skills/go/references/state-protocol.md` 引用。

## 职责切分

| 门 | 归属 | 对象 | 方法 |
|----|------|------|------|
| **G9** | loop 内 | 单个子任务的 commit | 代码层审查（code-reviewer 方法论） |
| **G10** | go 内（Step ⑦.5） | 整个特性分支 | 系统层审查（system-review 技能，V6 主承载） |

两条门**不重复审查**：G9 管代码正确性，G10 管跨子任务聚合后的系统一致性（需求↔实现↔文档对齐，§4 必检）。

## G10 结果处置

- 🔴 **ERROR** → 暂停交付，报告问题，等待人工决策（不自动合并）
- ⚠️ **WARNING** → 记录到交付报告，不阻断
- G10 通过 → merge → 交付

## v6.1 桥接模式（opt-in）

`export LOOPENGINE_BRIDGES=alpha` 且 `/go --reviewer=subagent-dd` 时：
G10 由 subagent-driven-development 的 final reviewer 承载（3 层问题分级 + Assessment 字段）。
**桥接失败自动降级回 system-review**，不阻断编排。

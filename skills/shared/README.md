# LoopEngine Shared 基础设施（v6.1）

> 本目录是 `go` / `loop` / `subagent-driven-development` 三技能**共享的规范与代码**集中地。
> 通过抽取共性消除重复，但不破坏各技能的独立性（双轨制 + 引用而非重写）。

## 目录结构

```
skills/shared/
├── README.md                              # 本文件（总览）
├── references/                            # 共享规范（5 份）
│   ├── owner-field-spec.md                # 高优：owner 字段定义
│   ├── atomic-write-spec.md               # 高优：原子写规范
│   ├── state-protocol-base.md             # 中优：状态文件通用规范
│   ├── breakpoint-recovery-base.md        # 中优：断点恢复基础协议
│   └── g9-g10-coordination.md             # 中优：G9/G10 协作契约
├── scripts/                               # 共享代码
│   ├── __init__.py
│   └── atomic_write.py                    # 高优：可复用原子写函数
└── examples/                              # 使用示例
    └── owner-usage.md
```

## 抽取原则

| 原则 | 说明 |
|------|------|
| **高复用 > 概念同源** | 只抽取两边**完全相同**的字段/算法，不强求合并相似但不同的实现 |
| **文档级 > 代码级** | 优先抽 spec 文档（markdown），代码仅在必须消除字节级重复时抽取 |
| **引用 > 重写** | 抽取后原文件改引用 shared/，**不**删除原有内容（保留向后兼容） |
| **双轨制保留** | 状态文件维持 go 宏观 + loop 微观的分工，**不合并** |
| **职责正交保留** | complexity-rules vs mode-default / degradation vs self-healing 等方法论差异保留 |

## 各技能引用清单

| 共享 spec | go 引用 | loop 引用 | subagent-dd 引用 |
|----------|:------:|:-------:|:---------------:|
| `owner-field-spec.md` | ✅ state-protocol.md | ✅ state-protocol.md | ❌ |
| `atomic-write-spec.md` | ✅ state-protocol.md / scripts/state_manager.py | ✅ state-protocol.md | ❌ |
| `state-protocol-base.md` | ✅ state-protocol.md | ✅ state-protocol.md | ❌ |
| `breakpoint-recovery-base.md` | ✅ breakpoint-recovery.md | ✅ state-protocol.md | ❌ |
| `g9-g10-coordination.md` | ✅ SKILL.md (Step ⑦.5) | ✅ SKILL.md (G9) | ❌ |
| `scripts/atomic_write.py` | ✅ scripts/state_manager.py | ⚠️ 可选 | ❌ |

## 不在 shared/ 范围

明确**不抽取**的内容（避免过度设计）：

| 内容 | 不抽取原因 |
|------|-----------|
| `state-protocol.md` 两份整文 | 双轨制是有意为之（go 宏观 / loop 微观） |
| `complexity-rules.md`（go L0 关键词）vs `mode-default.md` 6 维评分 | 方法论不同（关键词 vs 评分） |
| `gate-matrix.md` 整文 | loop 独占，go 只通过 handoff 消费 |
| `degradation.md`（go）vs `self-healing.md`（loop） | 职责正交：模型降级 vs 逻辑降级 |
| `frontend-verification.md` / `agent-browser-setup.md` / `experience-library.md` | loop 独占 |
| subagent-dd 三个 prompt template | 平行范式独占 |

## 兼容性

- ✅ v5.4 完全兼容
- ✅ v6.0 完全兼容
- ✅ 既有 .orchestrate-state.json / .loop-state-*.json 字段格式 100% 保留
- ✅ 引用 shared/ 是**增量增强**，不破坏既有加载逻辑

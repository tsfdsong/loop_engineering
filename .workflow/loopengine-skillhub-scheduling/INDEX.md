# deep-research（深度调研） 任务索引

**Slug**: `loopengine-skillhub-scheduling`
**题目**: 调研 LoopEngine skill-hub 的自动调度算法
**模式**: 完整模式（Plan → Search → Reason → Report → Reader Testing → 补充发现 → 反思）
**创建时间**: 2026-06-29
**当前阶段**: ✅ **全部完成**

---

## 阶段进度

| 阶段 | 状态 | 产出文件 |
|------|------|---------|
| Plan | ✅ 完成 | `00-plan.md` |
| Search | ✅ 完成 | `10-search.md` |
| Reason (WDM) | ✅ 完成 | `20-reason-wdm.md` |
| Reason (Munger) | ✅ 完成 | `20-reason-munger.md` |
| Report | ✅ 完成 | `30-report.md` |
| Reader Testing | ✅ 完成 | `90-reader-test.md` |
| **补充发现** | ✅ **完成** | `95-supplemental-findings.md` |
| **反思报告** | ✅ **完成** | `98-session-reflection.md` |
| **调度准确度测试** | 🧪 **待你实测** | `96-scheduling-accuracy-test.md` |

---

## Checkpoint 文件

```
.workflow/loopengine-skillhub-scheduling/
├── INDEX.md                      ← 本文件
├── 00-plan.md                    ← 阶段 1 产出
├── 10-search.md                  ← 阶段 2 产出
├── 20-reason-wdm.md              ← 阶段 3a 产出
├── 20-reason-munger.md           ← 阶段 3b 产出
├── 30-report.md                  ← 阶段 4 产出
├── 90-reader-test.md             ← 阶段 5 产出
├── 95-supplemental-findings.md   ← 补充发现
├── 96-scheduling-accuracy-test.md ← 调度准确度测试模板
├── 98-session-reflection.md      ← 反思报告
└── 99-final-state.json           ← 最终状态
```

---

## 关键发现

### 调度算法 3 层架构
1. **v5.4 兼容**：关键词表 + 冲突裁决 + 6 步兜底
2. **v6.0 复合编排（alpha mock）**：5 类预设 + 规则判定 + LLM 验证
3. **v6.1 三技能协同**：go / loop / subagent-dd 决策树

### 关键事实补充
- v5.4 baseline 27 条 = 9 核心技能 × 3 用例，**不**覆盖复合任务
- trace 格式已支持 `total_tokens` 字段，未来可实测性能
- `orchestrator-protocol.md` 已重命名为 `plan-orchestrator-protocol.md`

### 真正空白
- ❌ 端到端试跑（需真实生产环境）
- ❌ 性能实测（trace 系统已支持，但无测试数据）

---

## 调研完成度

**90%** — 仅缺"端到端试跑"和"性能实测"，需真实生产环境验证。

---

## 跨会话恢复

新会话中输入：`继续 .workflow/loopengine-skillhub-scheduling/`
（已完成，恢复会自动提示任务已结束）

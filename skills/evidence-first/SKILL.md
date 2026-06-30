---
name: evidence-first
description: "Use when comparing options, evaluating designs, making architectural decisions, or any 'X vs Y' / 'should I' / 'why' question. Triggers on '分析', '比较', '评估', '选型', '为什么'. Do NOT use for: pure implementation (use refactoring/testing), or brainstorming new ideas (use brainstorming)."
metadata:
  version: "1.0"
  type: skill
  origin: "2026-06-29 v5.4 兼容性事故"
  trigger_keywords: "分析/比较/评估/为什么/设计/重构/选型/该不该/应不应该"
  mandatory_before: "任何长篇论述（> 5 段）"
---

# Evidence-First Protocol（事实优先协议）

> **铁律**：**没有事实清单 = 禁止论述**。
> 任何"为什么 X""X 和 Y 哪个好""该不该 X""X 的价值"类问题，必须先查事实，再回答。

## 1. 起源

2026-06-29 v5.4 兼容性事故：AI 在回答"为什么需要 v5.4 兼容"时，基于"v5.4 是老版本"的**错误假设**，套用通用软件工程话术，给出 5 条**不实理由**（用户生态 / 企业 SLA / SemVer / 法律责任等），被用户当场识破。

**事故根因**：
1. 没看 git log，不知道 v5.4 是当天定稿的基线
2. 套用"通用兼容性原则"代替"项目事实"
3. 长篇大论掩盖事实不清
4. 没有"我错了/我不清楚"的意识

**事故教训**：**没有事实依据的专业论述 = 高级胡说**。

## 2. 5 项事实清单（必查）

任何项目分析、比较、评估前，**必须**先输出 5 项事实：

| # | 必查项 | 命令/位置 | 用途 |
|---|--------|----------|------|
| 1 | **最近 10 次提交** | `git log --oneline -10` | 了解项目活跃度和最近方向 |
| 2 | **项目自我描述** | `README.md` / `AGENTS.md` | 项目的"自述"，避免外部推断 |
| 3 | **版本声明** | `package.json` / `pyproject.toml` / `VERSION` | 了解当前版本基线 |
| 4 | **最近 changelog / 设计文档** | `docs/` / `CHANGELOG.md` | 了解最近的设计决策 |
| 5 | **main 分支活跃度** | `git log --since="3 months ago" --oneline \| wc -l` | 判断项目是否活跃 |

**未完成 5 项事实清单 = 禁止进入分析论述**。

## 3. 三类标注（每句话必标）

每一条论述中的**每一句话**必须标注类型：

| 标注 | 含义 | 优先级 | 示例 |
|------|------|:------:|------|
| **[F]** | **事实** — 已通过 git/file/docs 验证 | 🟢 最高 | [F] v5.4 SKILL.md 备份存在（ls 验证） |
| **[H]** | **假设** — 基于通用经验的合理推测 | 🟡 中 | [H] 用户可能依赖 v5.4 行为（未验证） |
| **[P]** | **原则** — 通用工程原则/最佳实践 | 🔴 最低 | [P] SemVer 规定次版本兼容（通用原则） |

**冲突优先级：F > H > P**（事实推翻假设，假设推翻原则）。

## 4. 自检 4 问（长篇论述前必答）

回答前自问：

1. **我有 [F] 事实依据吗？**（至少 1 个 [F] 标注才能长篇论述）
2. **[H] 假设明确标注了吗？**（不能用"应该""可能"伪装成事实）
3. **错了损失大吗？**（高损失场景必须 [F] 主导）
4. **能说"我不清楚"吗？**（不确定时优先说不知道）

**4 问中任一失败** = 缩小论述范围 / 标注不确定 / 主动询问用户。

## 5. 不确定时的处理（铁律）

| 场景 | 正确做法 | 错误做法 |
|------|---------|---------|
| 不了解项目状态 | "让我先查 git log / 文件" | 凭印象推断 |
| 假设与事实冲突 | "事实推翻假设" | 坚持假设 |
| 通用原则套用 | "通用原则是 X，但本项目是 Y" | 套模板不验证 |
| 用户纠正后 | "你说得对，我之前错在 X" | 辩解/转移话题 |
| 真的不知道 | **"我不清楚"** | 编造"通常""一般""应该" |

## 6. 触发场景（必须加载本技能）

- 用户问"为什么是 X" / "X 有什么用" / "X 有什么价值"
- 用户问"X 和 Y 哪个好" / "X vs Y" / "选 X 还是 Y"
- 用户问"该不该 X" / "应不应该 X"
- 用户问"评估/分析/设计/重构"类
- AI 自己准备给出**长篇论述（> 5 段）**时

## 7. 输出格式模板

```markdown
## 事实清单

1. [F] ...（已验证）
2. [F] ...（已验证）
3. [F] ...（已验证）
4. [H] ...（未验证的假设）
5. [P] ...（通用原则参考）

## 自检 4 问

1. 我有 [F] 依据吗？✅
2. [H] 明确标注了吗？✅
3. 错了损失大吗？中（关键决策需 [F] 主导）
4. 能说"我不清楚"吗？✅

## 分析

[基于事实的回答，每句话标注类型]

## 结论

[可追溯到事实的结论]
```

## 8. 详细规范

- 5 项事实清单详解 → `references/fact-checklist.md`
- [F]/[H]/[P] 标注规范 → `references/claim-types.md`
- 自检 4 问详解 → `references/self-check.md`
- 不确定时处理 → `references/no-hallucination.md`
- 追溯链规范 → `references/traceability.md`

## 9. 好坏对比案例

- 坏案例（事故现场）→ `examples/bad-v54-compat-answer.md`
- 好案例（重写版）→ `examples/good-v54-compat-answer.md`

## 10. 兼容性

- ✅ 与现有 45 个技能（v6.1.1 合并后）完全兼容
- ✅ 可与 `verification-before-completion`（完成时验证）配合使用
- ✅ 可与 `systematic-debugging`（调试）配合使用
- ✅ 形成完整链路：evidence-first（开始）→ systematic-debugging（过程）→ verification-before-completion（完成）

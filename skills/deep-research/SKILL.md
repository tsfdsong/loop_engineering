---
name: deep-research
display_name: 深度调研
description: "Use for **data-driven** research and reporting — 调研 / 对比 / 选型 / 综述 / 报告 / 市场分析 / 竞品分析 / 技术文献综述 / 内部代码库调研 / 'research X' / 'compare A vs B' / 'survey X' / 'summarize X' / '帮我了解 X'。Based on external sources (WebFetch / WebSearch / jcodemunch), **NOT user conversation alone** (that's brainstorming). 4-stage plan→search→reason→report with WDM + Munger inversion. **Fully local**, $0 cost. **NOT for — go to brainstorming instead**: 做什么 / 怎么做 / 思路 / 架构 / 创意 / 方案 / 设计 / 创建新功能 / 添加组件 / 头脑风暴 / 'I want to do X'. Also NOT for: 实施计划 (writing-plans), 架构/系统审查 (system-review), 文档协同撰写 (doc-coauthoring), 编码 (loop / go)."
---

# Deep Research（深度调研）— 4 阶段本地化调研闭环

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

---

## 核心定位

| 维度 | deep-research（深度调研）（本技能） | brainstorming | recursive-research（外部） |
|------|----------------------------|---------------|------------------------------------------|
| 目标产出 | 带引用的调研报告 / PRD 草稿 / 决策依据 | 设计文档（spec） | 报告 |
| 数据流向 | **本地 + 用户的 MCP 工具栈** | 本地 | 外部 API（Gemini 等） / 本地 + MCP |
| 成本 | **0** | 0 | $2-5/任务（外部 API） |
| 方法论 | 4 阶段 + WDM + Munger 反向 + Reader Testing | 苏格拉底式对话 | 各自不同 |
| 跨会话 | ✅ 本地磁盘 checkpoint | ❌ | ⚠️ 取决于具体工具 |
| 适合频率 | 高频（不增加边际成本） | 任意 | 低频（成本敏感） |

**与 brainstorming 的边界**：
- ✅ **本技能负责**：调研、对比、综述、决策依据、PRD 草稿
- ❌ **不负责**：纯创意发散、架构设计、方案探索（这些走 brainstorming）
- ⚠️ **重叠场景**：需求澄清——若重点是"对已有信息整理"走本技能，若重点是"探索未知方案"走 brainstorming

---

## 4 阶段流程

```
Plan（计划）→ Search（搜索）→ Reason（推理）→ Report（报告）
   ↑                                              ↓
   └──────────── Reader Testing（独立反馈环）─────┘
```

### 阶段 1: Plan

| 维度 | 详情 |
|------|------|
| **输入** | 用户的调研问题 / 需求 |
| **产出** | `00-plan.md` — 结构化查询计划（2-5 个子问题 + 预期产出 + 验收标准） |
| **工具** | brainstorming 提炼意图 + product-manager 框架（如 RICE / Jobs-to-be-Done） |
| **完成判据** | 子问题清单 + 每个子问题的"什么样的回答算合格" |

### 阶段 2: Search

| 维度 | 详情 |
|------|------|
| **输入** | `00-plan.md` 中的子问题 |
| **产出** | `10-search.md` — 原始资料（来源 + 摘要 + URL + 来源标签） |
| **工具** | WebFetch / WebSearch / jcodemunch（代码调研）/ repomix（打包代码库） |
| **来源分级** | **动态分级**（AI 根据场景判断 T1/T2/T3/Reject）—— 在 `10-search.md` 中为每个来源打标签 |
| **完成判据** | 每个子问题至少有 1 个 T1 或 T2 来源支撑 |

### 阶段 3: Reason

| 维度 | 详情 |
|------|------|
| **输入** | `10-search.md` 全部资料 |
| **产出** | `20-reason-wdm.md`（WDM 决策矩阵） + `20-reason-munger.md`（反向自检） |
| **工具** | Claude 推理 + headroom 压缩大段内容 + jcodemunch 分析（代码场景） |
| **WDM 步骤** | ① 列出 ≥ 3 个可行方案；② 设定加权标准；③ 1-5 评分；④ 比较总分 |
| **Munger 反向** | 对胜出方案问：它会如何失败？它有什么偏见？我忽略了什么？ |
| **完成判据** | WDM 矩阵有结论 + Munger 反向记录了至少 3 个"我不知道什么" |

### 阶段 4: Report

| 维度 | 详情 |
|------|------|
| **输入** | Reason 阶段全部产出 |
| **产出** | `30-report.md` — 最终报告（含引用 + 关键发现 + 行动建议） + `INDEX.md` |
| **工具** | headroom 整理 + Claude 撰写 |
| **引用格式** | 优先 Markdown 链接，重要来源标注 T1/T2/T3 |
| **完成判据** | 报告有结论 + 引用 + 行动建议 + 触发了 Reader Testing |

### Reader Testing（独立反馈环）

| 维度 | 详情 |
|------|------|
| **触发** | Report 完成后自动触发 |
| **机制** | 在当前会话内用 `system-reminder` 模拟"无上下文读者" |
| **模板** | `<system-reminder>假设你是该领域一无所知的读者，请列出 3-5 个"你需要进一步解释才能理解"的问题。</system-reminder>` |
| **产出** | `90-reader-test.md` — 读者提问清单 + 你的回答 |
| **完成判据** | 至少回答了 3 个"我不知道"类问题 |

---

## Checkpoint 机制

### 文件结构

```
<项目根目录>/.workflow/<slug>/
├── 00-plan.md            # 阶段 1 产出
├── 10-search.md          # 阶段 2 产出（含 T1/T2/T3 标签）
├── 20-reason-wdm.md      # 阶段 3 WDM 部分
├── 20-reason-munger.md   # 阶段 3 Munger 部分
├── 30-report.md          # 阶段 4 最终报告
├── 90-reader-test.md     # Reader Testing 记录
├── 99-final-state.json   # 最终状态（用于跨会话恢复）
└── INDEX.md              # 总目录 + 摘要
```

### 跨会话恢复

在新会话中输入：`继续 .workflow/<slug>/`

**自动行为**：
1. 检测 `<项目根目录>/.workflow/<slug>/99-final-state.json`
2. 读 `INDEX.md` 恢复摘要上下文
3. 提示："上次在 `<阶段名>` 阶段，完成了 `<已完成子任务>`，剩 `<未完成子任务>`"
4. 等待用户确认后继续

### Checkpoint 触发点

- ✅ 每个阶段完成时**自动写入**对应文件
- ✅ 关键决策点（WDM 评分、Munger 反向）**单独存档**
- ✅ 会话中断时**不丢失**已完成的阶段

---

## 快速模式（可选）

对于简单调研任务（如"查一下 X 库的 API"），可跳过阶段 3 的 WDM/Munger：

| 维度 | 完整模式 | 快速模式 |
|------|---------|---------|
| 阶段 | Plan → Search → Reason → Report → Reader Testing | Plan → Search → Report |
| 适合 | 决策类调研、PRD 草稿 | 信息查询、轻量综述 |
| 成本 | 高（时间 + 上下文） | 低 |

**启动方式**：`/deep-research 快速 调研 X`

---

## 关键原则

1. **数据不出本地**——所有 WebFetch 调用通过用户的 MCP，不调用外部 API
2. **每个阶段有完成判据**——不达判据不进入下一阶段
3. **引用优先 T1 来源**——找不到 T1 才用 T2，依此类推
4. **Munger 反向必做**——决策前必须问"它会如何失败"
5. **Reader Testing 必做**——作者以为的清晰 ≠ 读者眼中的清晰

---

## 限制说明

- ❌ **不替代 brainstorming** — 创意发散、方案设计、架构探索仍走 brainstorming
- ❌ **不替代 writing-plans** — 本技能不写"实施计划"，产出的是"调研报告"或"PRD 草稿"
- ❌ **不替代 doc-coauthoring（Anthropic 官方）** — 若你安装了 doc-coauthoring 且场景是"协同撰写文档"，优先用那个
- ❌ **不替代 system-review** — 审查项目/架构仍走 system-review
- ⚠️ **不调用任何外部 LLM API**（OpenAI / Gemini / Anthropic）—— 仅使用你的 Claude + MCP 工具栈
- ⚠️ **不保证学术严谨** — 动态分级 + Munger 反向是工程级保障，**不是**学术同行评审

---

## 相关技能

- `brainstorming` — 创意探索、方案设计（本技能的前置）
- `product-manager` — PM 框架（RICE / Kano / MoSCoW）
- `to-prd` — 对话→PRD 合成（本技能的产出可作为 to-prd 的输入）
- `writing-plans` — 实施计划（本技能的产出可作为 writing-plans 的输入）
- `system-review` — 项目/系统审查
- `evidence-first` — 事实优先分析协议

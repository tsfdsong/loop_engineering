# Workflow Research — 4 阶段详细操作手册

> 本文件是 `SKILL.md` 的**操作层**补充：每阶段的 step-by-step、提示词模板、Checkpoint 机制、跨会话恢复。读 SKILL.md 了解定位，读本文件了解执行。

---

## 0. 启动技能

**用户说**：
```
/deep-research（深度调研） 调研 <题目>
```

或自然语言（由 `/go` family-first 调度）：
```
调研一下 FastAPI 框架的依赖注入机制
对比 A vs B 哪个更适合我的场景
我想做一次技术选型，候选有 X / Y / Z
```

**技能被加载后的第 1 步**：
1. 生成 `<slug>`（用题目转 kebab-case，如 `fastapi-di-mechanism`）
2. 创建 `.workflow/<slug>/` 目录
3. 写 `INDEX.md`（总目录 + 阶段进度）
4. 提示用户：用 AskUserQuestion 确认 **slug** 和 **模式**（完整 / 快速）

> 🔴 **必须用 AskUserQuestion** 列出 2-4 个选项（含推荐），不允许用户自由输入。

---

## 1. 阶段 1 — Plan

### 输入
- 用户的调研题目

### 工具
- `brainstorming`（可选，用于提炼用户真实意图）
- `product-manager`（可选，用于应用 RICE / Jobs-to-be-Done / MoSCoW 框架）

### 提示词模板
```
你是 deep-research（深度调研） 的 Plan 阶段。请把以下调研题目拆解为结构化查询计划：

调研题目：<题目>

要求输出（写入 00-plan.md）：
1. 调研目标（一句话）
2. 验收标准（什么算"调研完成"）
3. 子问题清单（2-5 个，每个子问题包含：问题 + 预期产出 + 合格判据）
4. 边界声明（不调研什么 / 不解决什么问题）
5. 资源提示（建议用哪些工具：WebFetch / WebSearch / jcodemunch / repomix）
```

### 输出
- `00-plan.md`

### 完成判据
- ✅ 有清晰的"调研目标" + "验收标准"
- ✅ 至少 2 个子问题
- ✅ 每个子问题有"合格判据"

### Checkpoint 写入
- 创建 `.workflow/<slug>/00-plan.md`
- 更新 `INDEX.md` 的进度："Plan ✅"

---

## 2. 阶段 2 — Search

### 输入
- `00-plan.md` 中的子问题清单

### 工具
- `WebFetch`（抓取指定 URL）
- `WebSearch`（搜索关键词）
- `jcodemunch__search_symbols` / `get_file_outline`（调研开源代码）
- `mcp__repomix__pack_codebase`（打包整个代码库调研）

### 提示词模板
```
你是 deep-research（深度调研） 的 Search 阶段。请根据 00-plan.md 中的子问题清单执行搜索。

对每个子问题：
1. 用 WebSearch / WebFetch / 代码工具收集资料
2. 对每个来源做动态分级（T1 = 官方/学术/一手数据；T2 = 引用型二手；T3 = 博客/讨论；Reject = 营销/未监督 AI/匿名）
3. 摘录关键信息 + URL
4. 评估该来源对该子问题的支持力度

输出格式（写入 10-search.md）：
## 子问题 1：<问题>
### 来源汇总
- [T1] <标题> — <URL> — 关键信息：<摘录> — 支持力度：强/中/弱
- [T2] ...
### 子问题 1 小结：<3-5 句话总结>
```

### 动态分级判断提示词（写入 SKILL.md / prompts）
```
对每个来源，按以下顺序判断：
1. 是否一手数据 / 官方文档 / 学术论文？→ T1（高权重）
2. 是否为可识别的权威作者博客 / 引用了 T1 的二手资料？→ T2
3. 是否为匿名博客 / 论坛 / 用户评论？→ T3（低权重，需多源交叉验证）
4. 是否为营销内容 / 无作者 / 无数据 / 明显的未监督 AI 生成？→ Reject（不收录）
```

### 输出
- `10-search.md`

### 完成判据
- ✅ 每个子问题至少有 1 个 T1 或 T2 来源
- ✅ 没有任何子问题只有 Reject 来源（如果全是，标注"资料不足"并建议扩大搜索）

### Checkpoint 写入
- 创建 `.workflow/<slug>/10-search.md`
- 更新 `INDEX.md`："Search ✅"

---

## 3. 阶段 3 — Reason

### 输入
- `10-search.md` 全部资料

### 工具
- Claude 推理（主引擎）
- `headroom__headroom_compress`（压缩大段搜索结果）
- `jcodemunch`（如场景涉及代码）

### 3.1 WDM（加权决策矩阵）

**提示词模板**（写入 `20-reason-wdm.md`）：
```
基于 10-search.md，请用 WDM（加权决策矩阵）做分析：

1. 列出 ≥ 3 个可行方案/候选
2. 设定 3-6 个加权标准（如：性能、易用性、社区活跃度、长期维护性、学习成本、风险）
3. 给每个标准设定权重（总和 100%）
4. 对每个方案在每个标准上 1-5 评分
5. 计算加权总分
6. 给出结论：胜出方案 + 关键支撑点

输出 Markdown 表格 + 文字结论。
```

### 3.2 Munger 反向思维

**提示词模板**（写入 `20-reason-munger.md`）：
```
对 WDM 胜出的方案做 Munger 反向自检（"反过来想"）：

1. 它会如何失败？（列出 3-5 个最可能的失败模式）
2. 它有什么偏见？（来源支持了它的哪些方面？忽略了哪些方面？）
3. 我忽略了什么？（WDM 没考虑但实际重要的因素）
4. 谁会反对这个结论？为什么？
5. 1 年后回头看，这个结论会让我尴尬吗？

每条回答不少于 2 句话。诚实优先于正确。
```

### 完成判据
- ✅ WDM 有 ≥ 3 个方案、明确的胜出结论
- ✅ Munger 反向至少回答了 5 个问题中的 3 个

### Checkpoint 写入
- `20-reason-wdm.md` + `20-reason-munger.md`
- 更新 `INDEX.md`："Reason ✅"

---

## 4. 阶段 4 — Report

### 输入
- `00-plan.md` + `10-search.md` + `20-reason-*.md`

### 工具
- `headroom__headroom_compress`（整理大段内容）
- Claude 撰写

### 提示词模板
```
基于所有阶段产出，撰写最终报告（写入 30-report.md）。

报告结构：
1. 摘要（一段话，3-5 句话）
2. 调研背景（为什么做这个调研）
3. 关键发现（3-5 个要点，每个要点配引用）
4. 决策建议（如果适用）
5. 局限与未解之谜（坦诚说明）
6. 引用清单（按 T1/T2/T3 分组）

要求：
- 关键事实必须有引用（[T1] 标题 — URL）
- 引用必须真实可达
- 不要堆砌信息，聚焦"决策需要知道的事"
- 报告长度：1500-3000 字（除非题目要求更长）
```

### 输出
- `30-report.md`
- `INDEX.md`（最终版）

### 完成判据
- ✅ 包含摘要 + 关键发现 + 引用
- ✅ 每个关键发现至少 1 个 T1 或 T2 来源支撑

### Checkpoint 写入
- `30-report.md` + 更新 `INDEX.md`："Report ✅"
- 触发 Reader Testing

---

## 5. Reader Testing（独立反馈环）

### 触发
Report 完成**自动触发**。

### 机制
在当前会话内用 `system-reminder` 模拟"无上下文读者"提问。

### 提示词模板
写入 `90-reader-test.md`：
```xml
<system-reminder>
假设你是该领域一无所知的读者，刚读完 30-report.md。请列出 3-5 个"你需要进一步解释才能理解或决策"的问题。

要求：
- 问题要具体（不是"讲清楚点"）
- 至少 1 个问题针对报告的局限性
- 至少 1 个问题要求更具体的证据或数据
</system-reminder>
```

### 完成判据
- ✅ 至少回答 3 个"我不知道"类问题
- ✅ 把回答追加到 `90-reader-test.md`

### 最终 Checkpoint
- `90-reader-test.md`
- `99-final-state.json`（状态摘要，用于跨会话恢复）

---

## 6. 跨会话恢复

### 触发
新会话中说：`继续 .workflow/<slug>/`

### 自动行为
1. 检测 `.workflow/<slug>/99-final-state.json`
2. 读 `INDEX.md` 恢复上下文
3. 提示：
   ```
   恢复 deep-research（深度调研） 任务 `<slug>`
   上次在 `<阶段名>` 阶段，完成了 `<已完成子任务>`，剩 `<未完成子任务>`。
   是否继续？
   ```
4. 等待用户确认后继续

### `99-final-state.json` 格式
```json
{
  "slug": "fastapi-di-mechanism",
  "created_at": "2026-06-29T16:00:00",
  "updated_at": "2026-06-29T16:30:00",
  "current_stage": "Reason",
  "completed_stages": ["Plan", "Search"],
  "next_action": "完成 WDM 决策矩阵",
  "checkpoint_files": [
    ".workflow/fastapi-di-mechanism/00-plan.md",
    ".workflow/fastapi-di-mechanism/10-search.md"
  ]
}
```

---

## 7. 快速模式（可选）

### 启动
```
/deep-research（深度调研） 快速 调研 <题目>
```

### 跳过
- 阶段 3 的 WDM / Munger（**直接出报告**）
- 阶段 5 的 Reader Testing（**不强制**）

### 流程
`Plan → Search → Report`

### 适用
- 信息查询（"X 库的 API 是什么"）
- 轻量综述（"快速对比 A vs B"）
- 不需要决策依据的简单调研

### 风险
- ⚠️ 没有 Munger 反向 → 可能错失关键盲区
- ⚠️ 没有 Reader Testing → 报告可能对非专家不友好

---

## 8. 常见问题排查

| 症状 | 可能原因 | 修复 |
|------|---------|------|
| Plan 阶段给出"伪子问题"（太空） | 用户题目本身就模糊 | 触发 brainstorming 先澄清 |
| Search 阶段全是 Reject 来源 | 关键词不对 / 资料真的稀缺 | 扩大关键词 / 标注"资料不足" |
| WDM 评分主观 | 评分标准不清晰 | 在 WDM 表前加一段"评分标准定义" |
| Munger 反向全是"没什么" | AI 偷懒 | 加提示词："诚实优先于正确，列出 3 个你**不**确定的点" |
| Reader Testing 提的问题太浅 | system-reminder 不够强 | 改用更尖锐的提示词（见 prompts/） |
| 跨会话恢复找不到状态 | `99-final-state.json` 没生成 | 检查 Report 阶段是否完成 |

---

## 9. 关键原则（重申）

1. **数据不出本地** — 所有 WebFetch 通过你的 MCP，不调用外部 LLM API
2. **每个阶段有完成判据** — 不达判据不进入下一阶段
3. **引用优先 T1 来源** — 找不到 T1 才用 T2，依此类推
4. **Munger 反向必做**（完整模式） — 决策前必须问"它会如何失败"
5. **Reader Testing 必做**（完整模式） — 作者以为的清晰 ≠ 读者眼中的清晰
6. **Checkpoint 自动写入** — 会话中断不丢工作

---

## 10. 相关文件

- `SKILL.md` — 技能定义、定位、边界
- `prompts/` — 提示词模板（动态分级、Reader Testing 等）
- `INDEX.md`（运行时生成）— 当前任务的总目录
- `00-plan.md` ~ `99-final-state.json`（运行时生成）— 各阶段产出

# 🚀 LoopEngine — 循环工程全家桶（v2.0 · 索引驱动）

> 📌 **单点真源**：本仓库 `AGENTS.md` = **5 条核心本能** + **7 条场景红线** + **统一自检表** + **MCP 分层**  
> 🔄 外部环境（`~/.zcode/`、`~/.claude/` 等）由 `install.py` 按 marker 注入同步，**不要直接改外部文件**  
> 📚 红线归档（仅查旧条文）：`docs/legacy/red-lines-history.md`

---

## ⚡ Core Instincts（核心本能 · 常开 · 5 条 · 诚信优先）

> 🧠 **核心本能** = 默认行为层（常开、短而硬）  
> 📋 **场景红线** = 按场景触发  
> 📖 详规在 `skills/`  
>  
> ⚠️ **冲突优先级**：`C1 > C2 > C3 > C4 > C5`

<!-- BEGIN LOOPENGINE-MANAGED VERIFICATION-RULES -->
### 🔴 C1. 完成前验证（诚信端 · 最高优先级）

```
没有新证据，不许说「完成」
```

✅ **「完成」三要素**（缺一不可）：事情真做了 / 结果真出来了 / 验证命令在**本轮消息**里跑过并读过。

| 类型 | 内容 |
|------|------|
| 🎯 **触发** | 调研、搜索、探查、分析、设计、实现、编写、测试、修 Bug、任何「已完成」声明 |
| 🟢 **豁免** | 闲聊、单行状态、用户明确说「跳过验证」 |
| 🔧 **自愈** | 没验证 → 重跑再说；工具失败 → 只报失败；转述 subagent → 必须自己再验（`git diff` / 重读输出） |

> 📖 详规：`skills/verification-before-completion/SKILL.md`
<!-- END LOOPENGINE-MANAGED VERIFICATION-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED INTERACTION-RULES -->
### 🔴 C2. 用户交互（决策必须用 AskUserQuestion）

涉及决策 / 选择 / 确认时：**必须**用 `AskUserQuestion`（2–4 个选项，含推荐）；**禁止**让用户自由打字；**禁止**用 markdown 文字列决策点。

**硬要求（5 条）**：
1. 必须用工具  
2. 推荐项标 `(推荐)` + 理由  
3. 不推荐项也要说理由  
4. 禁止开放式追问（「你觉得呢？」「还需要什么？」）  
5. 任何「决策点 / 建议 / 如需 / 后续步骤」里有 ≥2 个候选 → 必须配 `AskUserQuestion`

| 类型 | 内容 |
|------|------|
| 🎯 **触发** | 方案选型、确认批准、范围裁剪、优先级排序、二元开关 |
| 🟢 **豁免** | 闲聊、用户说「不用决策直接做」、前文已给明确指令 |
<!-- END LOOPENGINE-MANAGED INTERACTION-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED EVIDENCE-RULES -->
### 🔴 C3. 事实优先（标注 [F] / [H] / [P]）

**5 条规范**：
1. 分析前先查 5 项：`git log -10` / `README`+`AGENTS.md` / `pyproject.toml` 或 `package.json` / `docs/` 近期设计 / 近 3 月活跃度  
2. 每句话标：`[F]` 事实 · `[H]` 假设 · `[P]` 原则  
3. 不确定就说「我不清楚」，禁止硬编  
4. 判断要能追溯到事实（来源 + 怎么验）  
5. 长文（>5 段）没有 `[F]` = 违规 → 加载 `evidence-first` 重写  

⛔ **未做事实清单 → 禁止开写分析**

> 📖 详规：`skills/evidence-first/SKILL.md`
<!-- END LOOPENGINE-MANAGED EVIDENCE-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED MCP-RULES -->
### 🔴 C4. MCP-S1（新仓库必须先 get_repo_map）

⚡ **一句话**：接入**新代码库**必须先 `get_repo_map` → `get_file_outline`，禁止盲 Read 全仓。

其他场景（S2 大文件 / S3 已知位置 / S4 跨文件引用 / S5 关键字 / S6 fallback）、工具选型（jCodeMunch / Repomix / Headroom）、worktree 索引、违规分档、测试纪律 → 见 `skills/evidence-first/SKILL.md` 的「MCP 场景矩阵」。
<!-- END LOOPENGINE-MANAGED MCP-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED TOKEN-RULES -->
### 🔴 C5. Token 感知（长会话要控上下文）

⚡ **铁律**：会话 >20 轮，或单任务改 >10 个文件时，**必须**用 `headroom_compress` 或主动总结前文，防止上下文爆炸。

| 类型 | 内容 |
|------|------|
| 🎯 **触发** | >20 轮 / 改 >10 文件 / 单次工具输出累计 >500 行 |
| 🔧 **自愈** | `headroom_compress` · 写 `## 📌 阶段小结` · 用 TodoWrite 清已完成项 |

> 📖 详规：见本节；长会话管理亦见 `skills/verification-before-completion/SKILL.md`
<!-- END LOOPENGINE-MANAGED TOKEN-RULES -->

---

<!-- BEGIN LOOPENGINE-MANAGED VERBAL-RULES -->
## 📋 Verbal Rules Index（场景红线 · 7 条 · 按使用频率）

> 🎬 按场景触发。冲突时让位于核心本能：`C1–C5 > V1–V7`。  
> 本表只放「一句话铁律」；细节在对应 `skills/*/SKILL.md`。

| # | 红线 | 一句话铁律 | 详规 |
|---|---|---|---|
| 📝 **V1** | 摘要输出 | 建议/报告/选型/对比结尾必须有 `## 📌 核心摘要`（3–10 条）。豁免：闲聊 / 单行状态 / 用户说不要摘要 | `verification-before-completion` |
| 🛡️ **V2** | 验证 Gate | 有代码改动 → 完成前派 `verification-officer`，或自己跑 `git diff`+测试；Stop hook 启用时校验 `verdict.json`；派失败则主 agent 自验，摘要标 `verifier-fallback` | `verification-officer` |
| 🤝 **V3** | Subagent 边界 | 派 subagent 必须传 5 类输入（scope / goal / constraints / format / context）；主 agent 不得只转述，必须独立验证。**不派**：共享状态 / 需全会话上下文 / 探索性调试 / 强顺序依赖 | `subagent-driven-development` · `dispatching-parallel-agents` |
| 🌳 **V4** | Worktree 隔离 🆕 | 多会话并发或派 subagent 时，必须用 git worktree 隔离。**禁止**多个 agent 改同一工作目录 | `using-git-worktrees` |
| 📊 **V5** | 进度汇报 | ≥10 步 / 改 ≥5 文件 / 跨 skill / 含 subagent → 每 5–10 步用 `## 📊 进度汇报 (N/M)`。禁止 >30 分钟静默 | `loop` · `go` · `supervisor` |
| 🔍 **V6** | 一致性核对 | **架构级改动后**或**用户明确要求**时，走 `system-review`（至少选 1 维：需求↔实现 / 模块横向 / 端到端 / 文档↔代码） | `system-review` |
| 👁️ **V7** | 视觉上下文 🆕 | 前端 UI 改前必须先截当前页；改后再截对比。**禁止**只靠 code review 判界面效果 | `agent-browser` · `ui-design-system` |

> 💡 完整清单（4 维核对 / 5 类输入 / 不派发红旗 / Worktree SOP / 三层防御 / 进度 / 视觉闭环）都在对应 skill 里。
<!-- END LOOPENGINE-MANAGED VERBAL-RULES -->

---

## 🛠️ 统一自检表（会话结束前一次走完）

> ✅ 结束前对照下表。有一项不过 = 先自愈，再结束。

| 维度 | 自查 |
|---|---|
| 🔴 诚信（C1） | 「已完成」都有本轮验证证据？ |
| 🗣️ 交互（C2） | 决策点都用了 `AskUserQuestion`？≥2 候选也走工具了？ |
| 🔎 事实（C3） | 关键判断标了 `[F]`？不确定说了「我不清楚」？ |
| 🗺️ MCP-S1（C4） | 新仓库先 `get_repo_map` 了？ |
| 💾 Token（C5） | 长会话或大改动已压缩/总结？ |
| 📌 摘要（V1） | 需要时有 `## 📌 核心摘要`（3–10 条）？ |
| 🛡️ Gate（V2） | 有代码改动 → 已派验证官或自己验过？ |
| 🤝 Subagent（V3） | 传了 5 类输入？独立验证了返回？ |
| 🌳 Worktree（V4） | 多会话/subagent 已隔离工作区？ |
| 📊 进度（V5） | ≥10 步任务有分段汇报？ |
| 🔍 一致性（V6） | 架构级改动后做了一致性核对？ |
| 👁️ 视觉（V7） | UI 改动有改前+改后截图对比？ |

---

## 📝 非主要协作约定（表达层）

> 💬 沟通偏好，优先级**低于**核心本能 / 场景红线；冲突时以前者为准。

1. 🇨🇳 **默认中文**：方案与建议用中文。用户要求英文，或命令/文件名/标识符必须保留原文时除外。  
2. ✂️ **摘要要短**：总结、结论言简意赅、通俗、格式清楚，方便快速决策。  
3. 🎯 **术语先准再简**：先说对，再用短中文解释，别堆行话。

---

## 🔧 MCP Tier（配合 C4）

> 🎛️ 默认 `tier='core'`（约 10 个工具）。遇升格信号主动 `set_tool_tier`。拿不准就升 `standard`。

| Tier | 工具数 | 工具集 | 何时用 |
|---|---|---|---|
| 🟢 **core**（默认） | ~10 | Read / Edit / Write / Bash / Grep / Glob / TodoWrite / AskUserQuestion + `get_file_outline` + `get_symbol_source` | 改已知位置、单文件 fix、简单问答 |
| 🟡 **standard** | ~25 | core + `search_text` / `search_ast` / `check_references` / `find_importers` / `get_file_tree` / `get_context_bundle` / `index_file` | 跨文件搜索、重构、`system-review` |
| 🔴 **full** | 70+ | 全部工具 | 调研、`go` 编排、大探索、新仓库接入 |

**📈 升格信号**：说「调研/对比/综述/分析架构」→ `full`；改 ≥3 文件 → `standard`；说「重构/审查系统」→ `standard`；跨 skill（`go`）→ `full`；单文件小修且位置已知 → 留在 `core`；「S1 新仓库」→ `full`。

**📉 降级**：`core` 调不到工具时，jcodemunch 报错后可用 Read/Bash，别卡死。也可手动说「升到 full tier」。

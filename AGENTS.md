# LoopEngine — 循环工程全家桶 (v2.0 · Index-Driven)

> **单点真源**：仓库 AGENTS.md = 5 Core Instincts + 7 Verbal Rules + Unified Checklist + Tier
> 外部执行环境（~/.zcode/、~/.claude/ 等）由 `install.sh` marker 注入同步，本文件不直接修改外部
> 完整红线演进史：`docs/legacy/red-lines-history.md`
>
> **v2.0 重构**（2026-07-17）：10 条扁平红线 → **5 Core（always-on）+ 7 Verbal（场景触发）**；详规下沉到 `skills/*/SKILL.md`；新增 C5 Token 感知 / V4 Worktree / V7 视觉 三条红线；引入 MCP Tier 机制。

---

## ⚡ Core Instincts (Always-On · 5 条 · 诚信优先序)

> Core Instincts = 默认行为直觉层（always-on，不冗长）；Verbal Rules = 场景触发规则层；详规在 `skills/`。
> 冲突时优先级：**C1 > C2 > C3 > C4 > C5**

<!-- BEGIN LOOPENGINE-MANAGED VERIFICATION-RULES -->
### 🔴 C1. 完成前验证（诚信端 · 最高优先级）

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

"完成"三要素（三者缺一 = 不得宣称完成）：任务已实际执行 / 结果已实际输出 / 验证命令已**本轮消息**内运行并读取。

**触发**：调研 / 搜索 / 探查 / 分析 / 设计 / 实现 / 编写 / 测试 / Bug 修复（红绿循环）/ 任何"已完成"声明。
**豁免**：闲聊 / 单行状态 / 用户明确"跳过验证"。
**违规自愈**：未跑验证 → 重跑 + 客观陈述；工具失败仍宣称完成 → 只陈述失败；转述 subagent 而未独立验证 → 必须独立验证（VCS diff / 输出重读）。

> 详规：`skills/verification-before-completion/SKILL.md`
<!-- END LOOPENGINE-MANAGED VERIFICATION-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED INTERACTION-RULES -->
### 🔴 C2. 用户交互（决策必须 AskUserQuestion）

涉及决策/选择/确认的交互，**必须**用 `AskUserQuestion` 工具（2-4 选项含推荐），**禁止**自由文本输入、**禁止**用 markdown 文字列决策点。

**5 条硬要求**：① 必须用工具；② 推荐项标 `(推荐)` + 理由；③ 不推荐项说明理由；④ 禁止开放式追问（"你觉得呢？"/"还需要什么？"）；⑤ **决策点硬约束**：任何"## 🎯 决策点 / 建议 / 如需 / 后续步骤"含 ≥2 候选时必须配 `AskUserQuestion`。

**触发场景**（5 类）：方案选型 / 确认批准 / 范围裁剪 / 优先级排序 / 二元开关。
**豁免**：闲聊 / 用户明确"不要求决策，直接做" / 用户前文已给明确指令。
<!-- END LOOPENGINE-MANAGED INTERACTION-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED EVIDENCE-RULES -->
### 🔴 C3. 事实优先（[F]/[H]/[P] 标注）

**5 条规范**：① 分析前必查 5 项事实（`git log -10` / `README`+`AGENTS.md` / `pyproject.toml`/`package.json` / `docs/` 近期设计文档 / 3 月活跃度）；② 每句话标 `[F]` 事实 / `[H]` 假设 / `[P]` 原则；③ 不确定 = 说"我不清楚"，禁止凑答案；④ 判断必须可追溯到事实（附来源+验证方式）；⑤ 长篇论述（>5 段）无 `[F]` = 红线违规，自动加载 `evidence-first` 重写。

**违规判定**：未完成事实清单 = 禁止进入分析论述。

> 详规（5 项必查 + 反选项 + PoC 时间盒）：`skills/evidence-first/SKILL.md`
<!-- END LOOPENGINE-MANAGED EVIDENCE-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED MCP-RULES -->
### 🔴 C4. MCP-S1（接入新代码库必须 get_repo_map）

**铁律（1 句话）**：**S1 接入新代码库**必须先 `get_repo_map` → `get_file_outline`，禁止盲 Read 全仓。

其他 5 场景（S2 大文件 / S3 已知位置 / S4 跨文件引用 / S5 跨文件关键字 / S6 fallback）+ 工具选型（jCodeMunch / Repomix / Headroom）+ worktree 索引流程 + 违规 4 档 + 测试纪律 5 条，全部移入 `skills/evidence-first/SKILL.md` 的 "MCP 场景矩阵" 段。
<!-- END LOOPENGINE-MANAGED MCP-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED TOKEN-RULES -->
### 🔴 C5. Token 感知（长会话上下文管理 · 新增）

**铁律**：长会话（>20 轮）或单任务改动 >10 文件时，**必须**用 `headroom_compress` 或主动总结前文。避免上下文爆炸导致输出质量下降（各种能力模型均受益）。

**触发**：会话 >20 轮 / 单任务改动 >10 文件 / 单次工具输出累积 >500 行。
**自愈**：达阈值时主动 `headroom_compress` / 用 `## 📌 阶段小结` 总结已完成段 / 用 TodoWrite 清理已完成项。

> 详规：本节自含（D3.1 会加强到 skills/verification-before-completion/SKILL.md 的"长会话管理"段）
<!-- END LOOPENGINE-MANAGED TOKEN-RULES -->

---

## 📋 Verbal Rules Index (7 条 · 使用频率优先序)

> 场景触发规则层。冲突时让位于 Core Instincts（C1-C5 > V1-V7）。

<!-- BEGIN LOOPENGINE-MANAGED SUMMARY-RULES -->
### V1. 摘要输出

决策依据类输出末尾必须有 `## 📌 核心摘要`（**3 ≤ bullet ≤ 10**）。

**触发**：建议/推荐 / 调研/审查/复盘报告 / changelog / 架构选型 / 问题诊断 / 方案对比 / 多步执行汇报。
**豁免**：闲聊 / 单行错误 / 执行类纯状态 / 用户明确"不要摘要"。
**模板**：`## 📌 核心摘要` + 3-10 bullet（核心结论 / 建议方案 / 风险边界）。

> 详规：本节自含（摘要模板见上方 · 详规下沉到 skills/verification-before-completion/SKILL.md 由 D3.1 完成）
<!-- END LOOPENGINE-MANAGED SUMMARY-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED VERIFICATION-GATE-RULES -->
### V2. 验证 Gate（降级兼容）

有代码改动 → 完成前必须派 `verification-officer` 或独立跑 `git diff`+测试；Stop hook 启用时自动校验 `verdict.json`；**模型 fallback**：派失败时主 agent 必须独立验证并在摘要标注 `verifier-fallback`。

**三层防御**：D 证据（`.verify-state/<SID>/verdict.json`）+ B 验证官（`skills/verification-officer/`）+ A Stop hook（`hooks/verify-gate.sh`，exit 2 阻断）。
**触发**：任何含 Edit/Write/MultiEdit 代码改动。**豁免**：纯对话 / 纯 Read / 纯 Bash 执行类。
**模型兼容**：能力较弱模型派失败 → 独立跑 `git diff`+测试 + 客观陈述 + 摘要首行标 `verifier-fallback`。Stop hook 阻断 ≥3 次软警告放行（防无限循环）。

> 详规：`skills/verification-officer/SKILL.md`
<!-- END LOOPENGINE-MANAGED VERIFICATION-GATE-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED SUBAGENT-RULES -->
### V3. Subagent 边界

派 subagent 必须传 **5 类输入**（scope/goal/constraints/format/context）；主 agent 不得仅转述，必须独立验证。

**5 类必接**：specific scope / clear goal / constraints（时间·token·工具白名单）/ output format（JSON·Markdown·状态枚举）/ context snippets（禁止 subagent 重复探索）。
**4 不派发**（任一满足禁并行）：共享状态 / 需全 session 上下文 / 探索性调试 / 顺序依赖。
**4 状态协议**：DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT。

> 详规（派遣 API + 12 条 Red Flags）：`skills/subagent-driven-development/SKILL.md` + `skills/dispatching-parallel-agents/SKILL.md`
<!-- END LOOPENGINE-MANAGED SUBAGENT-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED WORKTREE-RULES -->
### V4. Worktree 隔离（新增）

多会话并发或派 subagent 时，必须用 git worktree 隔离工作区。**禁止**多 agent 改同一 working directory（冲突 / git status 污染 / commit 互相覆盖）。

**触发**：`/go` 编排多 subagent / `dispatching-parallel-agents` 派 ≥2 / 跨会话恢复。
**合规**：每个 subagent 独立 worktree（`.worktrees/<task>/`），完成后 merge 或 PR 合入主干。

> 详规：`skills/using-git-worktrees/SKILL.md`
<!-- END LOOPENGINE-MANAGED WORKTREE-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED PROGRESS-RULES -->
### V5. 进度汇报

≥10 步 / 多文件（≥5）/ 跨 skill（orch ≥2）/ 含 subagent 任务，每 5-10 步用 `## 📊 进度汇报 (N/M)` 模板。禁止 >30 分钟静默。
**豁免**：单步 / 短任务（<5 步 / <1 分钟）/ 用户明确"不需要进度"。
**模板**：`## 📊 进度汇报 (N/M)` + 已完成 / 当前阶段 / 下一步 / 阻塞 / 预计剩余。
与 V1 协调：进度 = 中途节奏，摘要 = 结束结构化，两者不冲突。

> 详规：`skills/loop/SKILL.md` + `skills/go/SKILL.md`
<!-- END LOOPENGINE-MANAGED PROGRESS-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED CONSISTENCY-RULES -->
### V6. 一致性核对

**架构级改动后**或**用户显式要求**时，按 system-review 流程做一致性核对（4 维度选 ≥1）。

**触发**：累计 3 子任务 / 1 跨模块改动 / 1 架构级改动 / 用户要求。
**4 维度**（用 AskUserQuestion 选 · multiSelect）：① 需求↔实现（标 [GAP]/[EXTRA]/[OK]）② 模块间横向（接口契约/字段命名/状态机）③ 端到端链路（入口追出口找断点）④ 文档↔代码（README/API/CHANGELOG 一致性）。
**处置**：每个不一致项走 AskUserQuestion（立即修复/登记后续/标记已知边界/忽略）。
**豁免**：单步任务 / 用户"跳过" / 纯调研 / 单文件修复。

> 详规（检查清单 + 报告模板）：`skills/system-review/SKILL.md`
<!-- END LOOPENGINE-MANAGED CONSISTENCY-RULES -->

<!-- BEGIN LOOPENGINE-MANAGED VISUAL-RULES -->
### V7. 视觉上下文（新增）

前端 UI 改动前必须先截当前页面图（agent-browser 或 Playwright MCP）；改完截图对比验证。**禁止**纯靠 code review 判断 UI 效果（肉眼不可见的像素回归 / 布局偏移 / z-index 层级）。

**触发**：改组件样式/布局/交互 / CSS/Tailwind / 路由/页面结构 / 响应式/主题/暗色模式。
**合规**：改前截图（baseline）→ 改动 → 改后截图 → 对比（`web-visual-diff` 或人工）。

> 详规：`skills/agent-browser/SKILL.md` + `skills/web-visual-diff/SKILL.md`
<!-- END LOOPENGINE-MANAGED VISUAL-RULES -->

---

## 🛠️ Unified Checklist (会话末一次性走)

> 每轮会话结束前对照 12 项自检。任一项未达标 = 必须自愈后再结束。

| 维度 | 自查项 |
|---|---|
| 诚信（C1）| 所有"已完成"声明都有本轮验证证据？ |
| 交互（C2）| 决策点都用 AskUserQuestion？含 ≥2 候选的建议段也走工具？ |
| 事实（C3）| 关键判断有 [F] 标注？不确定的说"我不清楚"？ |
| MCP-S1（C4）| 接入新代码库先 get_repo_map 了？ |
| Token（C5）| 长会话（>20 轮）或 >10 文件任务已压缩/总结前文？ |
| 摘要（V1）| 触发场景末尾有 ## 📌 核心摘要？bullet 3-10 个？ |
| Gate（V2）| 有代码改动 → 已派 verification-officer 或独立验证（fallback）？ |
| Subagent（V3）| 派 subagent 传了 5 类输入？独立验证了返回？ |
| Worktree（V4）| 多会话/subagent 场景已用 worktree 隔离工作区？ |
| 进度（V5）| ≥10 步任务有分段汇报？ |
| 一致性（V6）| 架构级改动后做了一致性核对？ |
| 视觉（V7）| 前端 UI 改动已截图对比（改前+改后）？ |

---

## 🔧 MCP Tier 机制（C4 配套）

> 本会话默认 `tier='core'`（~10 工具）。遇升格信号主动 `set_tool_tier`。不确定时升 `standard`。

| Tier | 工具数 | 工具集 | 触发场景 |
|---|---|---|---|
| **core**（默认）| ~10 | Read/Edit/Write/Bash/Grep/Glob/TodoWrite/AskUserQuestion + `get_file_outline` + `get_symbol_source` | 修改已知位置、单文件 fix、简单问答 |
| **standard** | ~25 | core + `search_text`/`search_ast`/`check_references`/`find_importers`/`get_file_tree`/`get_context_bundle`/`index_file` | 跨文件搜索、重构、system-review |
| **full** | 70+ | 所有工具 | 调研、go 编排、大规模探索、新代码库接入 |

**升格信号**：用户说"调研/对比/综述/分析架构"→ full；任务 ≥3 文件改动 → standard；用户说"重构/审查系统"→ standard；跨 skill 编排（orch）→ full；单文件小修行号已知 → core（不升格）；"S1 接入新代码库"→ full。

**降级**：core 调不到工具时 jcodemunch 报错后 AI 自然降级用 Read/Bash（不卡死）。用户可手动说"升到 full tier"立即全开。

---

## 🛠️ 工具/模型双无关性（硬约束）

本插件坚持**宿主工具无关** + **模型无关**：不预设特定工具（ZCode/Claude Code/Codex/Gemini/Copilot/Pi 均支持）或特定模型（适配能力较弱到较强各种模型）。降级链用三档抽象（Primary/Secondary/Tertiary），用户在 `.loopengine.yaml` 自配。能力较弱模型从冗余提示+fallback 路径受益；能力较强模型享受更轻量的决策分母。

---

## 安装 / 更新

**macOS / Linux / Windows Git Bash**：
```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

**Windows PowerShell**（纯 PS 无需 Git Bash）：
```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$le = "$env:TEMP\le-install-$([DateTime]::UtcNow.Ticks).ps1"
irm https://github.com/tsfdsong/loop_engineering/raw/main/install.ps1 -OutFile $le
& $le; Remove-Item $le -Force
```

**更新**（v1.2.0 起 install.sh 智能合一：未装→安装 / 旧版→升级 / 同版→5 秒等待）：
```bash
bash <(curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh)
```

装完即用。详见 `docs/INSTALL.md`。

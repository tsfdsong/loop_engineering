---
name: skill-hub
description: 技能调度中心 —— 根据用户意图自动路由到最合适的技能。v6.2.1 回滚合并 8（loop + loop-library），恢复 loop 自研核心技能；v6.2 其他 7 组合并保留（api-development/testing/production-readiness/software-architecture/refactoring 扩展/clean-code 扩展/code-engineering）；v5.4 / v6.0 / v6.1 行为 100% 兼容。
metadata:
  version: "6.2.1"
  base_compat: "5.4"        # v5.4 输入输出行为 100% 兼容
  base_compat_v6: "6.0"     # v6.0 复合任务编排行为 100% 兼容
  base_compat_v6_1: "6.1"   # v6.1 合并行为 100% 兼容
  installed_skills: 36
  shared_dirs: ["shared"]   # v6.1 抽取的共享基础设施目录，不计入 installed_skills
  skill_count_note: |
    installed_skills: 36 = v6.1 (45) - v6.2 合并删除 (7) + v6.2.1 回滚合并 8 (1) - 36。
    skills/ 目录实际条目数 = 38（36 个技能 + shared/ + skill-hub/ 自身）。
    v6.2.1 回滚（commit rollback/merge-8）：
      - loop + loop-library → loop-engineering → 回滚为 loop（+1）
      - loop-library（superpowers）彻底废弃删除
    v6.2 合并明细（7 组保留 + 1 组回滚）：
      - api-design + api-security + auth-implementation → api-development (-2)
      - testing-patterns + TDD + e2e-testing → testing (-2)
      - release-it + production-code-audit → production-readiness (-1)
      - clean-architecture + poeaa + ddia → software-architecture (-2)
      - legacy-code + framework-migration → refactoring (扩展，0)
      - pragmatic-programmer → clean-code (扩展，0)
      - philosophy + async-python → code-engineering (-1)
    v6.1.1 合并明细（4 组）：
      - refactoring-guru → refactoring (-1)
      - ddd-distilled + implementing-ddd + ddd-tactical-patterns → domain-driven-design (-3)
      - code-complete + code-quality-principles → clean-code (-2)
      - requesting-code-review + receiving-code-review → code-reviewer (-2)
  cross_plugin_skills: 1
  cross_plugin_refs: "skill-creator (官方 skill-creator 插件)"
  purpose: auto-routing + composite-orchestration (opt-in) + cross-skill-bridge (opt-in)
  orchestrator_env: "LOOPENGINE_ORCHESTRATOR=alpha 启用；=off 一键回滚"
  bridges_env: "LOOPENGINE_BRIDGES=alpha 启用 subagent-dd 桥接；=disabled 默认关闭"
---

# Skill Hub — 技能自动调度中心

你是技能调度枢纽。用户不指定技能时，**你必须根据其意图自动调用最合适的单个技能**。

## 核心规则

0. **🔴 MCP 红线（最高优先级）** — 详见底部「🔴 MCP 代码理解工具」章节，三处重复强调防遗漏。
1. **分析用户意图** → 匹配下方「意图→技能」映射表
2. **调用 Skill 工具** → 加载匹配的**一个**技能
3. **技能加载后** → 严格遵循该技能的指令
4. **多种技能适用时** → 按「冲突裁决」规则选主技能，只加载一个
5. **无匹配技能时** → 进入「语义兜底」规则（见底部）
6. **遇到 Bug/报错** → 优先调 systematic-debugging
7. **声称完成时** → 调 verification-before-completion

---

## 🔴 用户交互红线（全局适用）

> **任何涉及用户决策、方案选择、确认的交互，必须遵循以下 4 项硬要求。**

1. **必须使用 `AskUserQuestion` 工具** — 列出 2-4 个选项（含推荐），让用户通过选择框选择，**不允许要求用户输入自由文本**
2. **推荐项必须标注 `(推荐)` 并说明理由** — 第一个选项为推荐项，描述中说明为什么推荐
3. **不推荐项必须说明理由** — 每个非推荐选项的描述中说明不推荐或需谨慎的理由
4. **禁止开放式追问** — 不允许"你觉得呢？""还需要什么？""你还想做吗？"等需要用户组织语言回答的提问

**违反以上任一条 = 视为阻塞 Bug，必须自愈修复。**

> 此规则适用于 skill-hub 及所有子技能（已在各自 SKILL.md 中引用）。

---

## 技能全景 & 调度规则

### 📝 代码质量（2个 · v6.2 合并：clean-code + code-engineering)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`clean-code`** ⭐ | 干净代码、可读性、命名、代码规范、**软件构造、commit规范、DRY、正交** | **代码质量超级技能**——Martin + McConnell + 自家规范 + pragmatic-programmer 四合一 |
| **`code-engineering`** ⭐ | 复杂度、深模块、信息隐藏、**异步、asyncio、协程** | **软件工程超级技能**——Ousterhout 哲学 + async-python 双源 |

**冲突裁决**：说"代码太乱/代码规范/commit规范/DRY"→ clean-code（v6.2 起含 4 源）；说"系统太复杂/异步开发"→ code-engineering（v6.2 新合并）

### 🏗️ 架构设计（2个技能 · v6.2 合并 clean-architecture + poeaa + ddia)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`software-architecture`** ⭐ | 分层、依赖方向、**企业架构、ORM、MVC、分布式、复制、分区、一致性、流处理** | **架构设计超级技能**——Clean Architecture + POEAA + DDIA 三合一 |
| **`domain-driven-design`** ⭐ | 领域、限界上下文、聚合根、通用语言、**战术模式、入门、落地** | **DDD 超级技能**——Vernon 入门 + Evans 原书 + self 战术 + Vernon 落地四合一 |

**冲突裁决**：说"架构分层/企业模式/分布式"→ software-architecture（v6.2 起含 3 源）；说"领域模型/DDD"→ domain-driven-design（v6.1.1 起含 4 源）

### 🔧 重构（1个超级技能 · v6.2 合并 legacy-code + framework-migration)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`refactoring`** ⭐ | 重构、坏味道、**遗留代码、没测试、框架迁移、升级、现代化** | **重构超级技能**——Fowler 原书 + refactoring.guru 速查 + legacy-code + framework-migration 四合一 |

**冲突裁决**：说"这个函数太长/老系统没测试/升级框架"→ refactoring（v6.2 起 4 源合一）

### 🧪 测试（1个超级技能 · v6.2 合并 testing-patterns + TDD + e2e)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`testing`** ⭐ | 单元测试、Mock、Jest、**TDD、红绿重构、端到端、E2E、回归** | **测试超级技能**——Jest 模式 + 严格 TDD + 端到端自动化三合一 |

**冲突裁决**：说"写测试/TDD/端到端"→ testing（v6.2 起 3 源合一）

### 🐛 调试（1个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`systematic-debugging`** | 调试、报错、Bug、不工作、排查、修一下、修好了吗 | 遇到任何 bug 或测试失败时，**优先调用此技能** |

### 🔍 事实优先（1个，独占 · v6.1 新增 · 2026-06-29）

> **起源**：2026-06-29 v5.4 兼容性事故 — AI 基于错误假设套用通用话术被用户当场识破。
> **强制触发**：任何项目分析/比较/评估/设计/重构前**必须**自动加载。

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`evidence-first`** | 分析、比较、评估、为什么、有什么用、什么价值、设计、重构、选型、该不该、应不应该、vs | 项目分析前必查 5 项事实 + 标注 [F]/[H]/[P] + 自检 4 问 |

**铁律**：
- 长篇论述（> 5 段）无 [F] 标注 = 🔴 红线违规
- 用 [H]/[P] 伪装 [F] = 🟠 严重违规
- 不确定 = 说"我不清楚"，禁止凑答案

**调度位置**：在 systematic-debugging 之前、verification-before-completion 之后，形成完整链路：
```
evidence-first（开始 · 事实优先）
  → systematic-debugging（过程 · 调试）
  → verification-before-completion（完成 · 验证）
```

### 🔌 API 开发（1个超级技能 · v6.2 合并 api-design + api-security + auth-implementation)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`api-development`** ⭐ | API 设计、REST、GraphQL、**API 安全、限流、JWT、OAuth、认证、权限、CORS、CSRF** | **API 全栈超级技能**——设计 + 安全 + 认证三合一 |

> 注：本项目**不**包含文档生成类技能（`code-documentation-doc-generate`、`api-documentation-generator`）和文档处理类技能（`docx`、`pdf`）——它们与软件开发流程非直接相关，已被剥离。需要时自行安装对应官方插件。

### 🔍 代码审查（1个 · v6.1.1 合并 requesting + receiving)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`code-reviewer`** ⭐ | CR、代码审查、review 代码、检查代码、**请求审查、提交审查、收到审查意见、处理反馈** | **代码审查超级技能**——AI 自动审查 + 请求审查 + 接收反馈三合一（被 loop G9 调用） |

**冲突裁决**：说"审查这段代码/请求审查/收到审查反馈"→ code-reviewer（v6.1.1 起三合一）；说"审查项目/架构/系统"→ `system-review`

### ✅ 验证（1个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`verification-before-completion`** | 完成了、修好了、通过了、验证、确认 | 声称任务完成前，**必须先验证**而非口头确认 |

### 🚀 工程流程（5个 · v6.2 合并 production-readiness + async-python)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`github-actions-templates`** | CI/CD、流水线、部署、GitHub Actions | CI/CD 工作流 |
| **`production-readiness`** ⭐ | 上线前检查、生产审计、**发布、稳定性、故障、断路器、超时、重试、限流** | **生产就绪超级技能**——production-code-audit + release-it 二合一 |
| **`context-driven-development`** | AI 上下文、长对话 | 优化 AI 编码上下文 |
| **`using-git-worktrees`** | worktree、隔离分支、多分支并行 | Git worktree 隔离工作区 |
| **`finishing-a-development-branch`** | 合并、PR、分支完成、收尾 | 开发完成后决定如何合并/PR |

### 📋 规划与执行（5个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`brainstorming`** | 创意、设计、头脑风暴、想法、方案 | 编码前的需求探索、方案设计、可行性分析（**已收窄**——调研/讨论/分析/评估/选型/对比等词交由 evidence-first / system-review / product-manager 处理） |
| **`writing-plans`** | 写计划、规划、任务拆分、实现方案 | 有明确需求后写实现计划 |
| **`executing-plans`** | 执行计划、按计划实现 | 有写好的计划后分步执行 |
| **`subagent-driven-development`** | 并行任务、多任务同时、分头执行 | 当前会话中并行执行独立任务 |
| **`dispatching-parallel-agents`** | 并行、多个独立任务、分派 | 派发多个独立任务到并行 agent |

### 📋 产品管理（2个）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`product-manager`** | PRD、产品文档、需求规范、竞品分析、RICE、Kano、MoSCoW、用户故事 | **规范化**需求 |
| **`to-prd`** 🔵 | 生成 PRD、整理需求、输出需求文档 | **收尾输出**——将讨论结果合成为 PRD（🔵 用户显式：`disable-model-invocation: true`，AI 不自动调度，需用户主动 `/to-prd` 调用） |

> ⚠️ `brainstorming` 覆盖了产品需求的**发散阶段**（需求探索、想法发散、创意讨论），此处不再重复列出。

### 🛠️ 技能管理（3个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`agent-skill-architecture`** | 技能设计、技能审查、改造技能、新建技能 | **设计/审查 Agent 技能时强制执行架构规范** |
| **`writing-skills`** | 创建技能、编写技能、编辑技能 | 创建或编辑 agent 技能 |
| **`skill-creator`** (外部) | 创建技能、新建技能 | 创建新技能的引导流程（ZCode 官方 `skill-creator` 插件） |

> 注：`skill-creator` 由 ZCode 官方 `skill-creator` 插件提供，需先安装该插件。本项目**不**包含 `find-skills`（元技能，与开发流程无关，已剥离）。

### 🗄️ 数据库（1个）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`database-design`** | 数据库、表设计、索引、SQL、迁移 | 数据库设计与优化 |

### 🛠️ 工具类（3个）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`drawio-skill`** | 画图、流程图、架构图、时序图 | 图表可视化 |
| **`agent-browser`** | 浏览器、网页、截图、自动化 | 浏览器自动化 |
| **`using-loopengine`** | LoopEngine、体系介绍、上手引导 | **LoopEngine 体系引导** |

### 🔴 MCP 代码理解工具（红线规则 · 不可违反）

> **红线规则：任何需要理解代码结构的操作，必须先用 MCP 工具，禁止直接 Read 全文件。**
> 实测可节省 ~90% token。此规则优先级高于所有其他操作指令。

**适用范围（不仅限于"修改代码前"）**：
- 修改代码、调研代码、解释代码、分析架构
- 查找函数/类/变量定义、查找引用位置
- 了解项目结构、浏览目录、理解文件内容
- **一句话：只要目的是"理解代码"，就必须 MCP 优先**

**违规判定**：
- 连续 3 次以上直接 Read 全文件而未使用任何 MCP 工具 → 红线违规
- 每次会话结束后自查：MCP 工具调用次数应 ≥ Read 调用次数

| MCP 工具 | 用途 | 适用场景 | Token 节省 |
|------|------|------|:--:|
| `mcp__jcodemunch__get_repo_map` | 项目结构全景图（符号级） | 需要了解项目整体结构、定位文件 | ~80% |
| `mcp__jcodemunch__get_file_outline` | 文件符号大纲（函数/类/变量列表） | 需要了解文件内容结构，无需读全文 | ~85% |
| `mcp__jcodemunch__search_symbols` | 语义搜索符号（按名称/签名/摘要） | 查找特定函数、类、变量定义 | ~90% |
| `mcp__jcodemunch__get_file_tree` | 目录树（可选含文件摘要） | 浏览项目目录结构 | ~95% |
| `mcp__jcodemunch__find_references` | 查找符号的所有引用位置 | 了解修改影响范围 | ~85% |
| `mcp__jcodemunch__get_blast_radius` | 修改影响面分析 | 重构前评估风险 | ~90% |
| `mcp__repomix__pack_codebase` | 打包代码库（结构化输出） | 需要完整代码上下文时 | ~70% |
| `mcp__headroom__headroom_compress` | 压缩大段内容（hash 检索） | 需要缓存大段内容供后续引用 | ~95% |

**使用规则（强制执行）**：

1. **任何理解代码的操作，必须先用 MCP 工具** — 禁止直接 Read 全文件（红线）
2. **标准流程**：`get_repo_map`（定位项目全景）→ `get_file_outline`（理解文件结构）→ `search_symbols`（找关联符号）→ `Read`（仅精确读取目标行）→ `Edit`
3. **Read 仅用于**：MCP 工具全部不可用、需要精确行内容、文件小于 50 行
4. **自查机制**：每次会话结束前，检查 MCP 调用次数是否 ≥ Read 调用次数

### 🧭 路由类（2个 · v6.2.1 回滚合并 8：loop 保留)

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`loop`** | `/loop`、loop:、循环工程、闭环开发 | 闭环编码 —— 功能开发+门禁+自愈（v4.1 自研核心技能）|
| **`skill-router`** | 不知道该用哪个、帮我选技能、推荐技能 | **交互式**技能推荐（问答引导） |

> 注：loop-library（superpowers）已彻底废弃删除。v6.2 合并 8 错误地与自研 loop 合并，已回滚。

### 🔍 审查类（2个）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`system-review`** | 审查系统、审查架构、审查项目、检查矛盾、检查一致性、系统审查、系统审计、审查技能、优化项目 | 系统级项目审查 —— 三步方法论（横向自洽性→纵向架构深度→持续改进）+ ATAM/arc42 业界参考 |
| **`code-reviewer`** | CR、代码审查、review 代码、检查代码 | AI 自动审查代码质量 |

**冲突裁决**：审查**项目/架构/系统**层面 → `system-review`；审查**单文件/单 PR**代码 → `code-reviewer`。两者互补不互斥。

---

## 自动调度流程

```
用户请求
    │
    ▼
分析意图 ──→ 匹配上方映射表
    │
    ├── "/loop" → 加载 loop 技能
    ├── "/go" → 加载 go 技能
    ├── 精确匹配 1 个 → 调用 Skill 工具加载该技能
    ├── 匹配多个 → 按「冲突裁决」规则选 1 个
    ├── Bug/报错 → systematic-debugging
    ├── 声称完成 → verification-before-completion
    ├── 无匹配 → 进入「语义兜底」
    └── 语义兜底也失败 → 直接执行，不强行调用
```

## 语义兜底规则 🔄

**当关键词表无匹配时，按以下优先级做二次判断**（参考 Superpowers 的 LLM 语义路由）：

1. **含"审查系统/审查架构/检查矛盾/系统审计/优化项目"** → `system-review`（系统级审查）
2. **含"调研/对比/选型"** → `brainstorming`（需求探索与方案设计）；**含"分析/探索/研究/评估"** → `evidence-first`（事实优先协议）；**含"审查"** → `system-review`（系统级审查）或 `code-reviewer`（单文件 PR）
3. **含"修/改/更新/优化/改进/完善" + 具体对象** → `refactoring`（重构改进）
4. **含"怎么/如何/为什么"** → `brainstorming`（探索性问题）
5. **含"能不能/可不可以/是否"** → `brainstorming`（可行性分析）
6. **以上都不匹配** → 直接执行，不强行调用

## 关键指令

> **MCP 红线**：见底部「🔴 MCP 代码理解工具」章节（最高优先级，三处重复强调防遗漏）。

1. **每次只加载一个技能**（除非显式 `/composite` 走 Orchestrator 串/并行链）。
2. **不要等用户说技能名**。用户说"这个函数太长了"，你就应该调用 `refactoring`。
3. **遇到 Bug 优先调试**。第一反应是 `systematic-debugging`。
4. **完成前必须验证**。用户说"修好了/完成了"，先调 `verification-before-completion`。
5. **优先精准技能**。`api-security-best-practices` 优先于更宽泛的安全技能。
6. **简洁告知**。加载技能时一句话说明为什么选它。
7. **语义兜底优先**。关键词无匹配时，先用语义兜底规则判断，不要直接放弃。

**_这个技能是你与 45 个技能（v6.1.1 合并后）之间的桥梁。每次对话开始时自动参考此调度规则。_**

---

## 🆕 v6.0 新增：复合任务编排（Orchestrator 模式 · alpha 阶段）

> **本节为 v6.0 新增内容，alpha 阶段需显式启用。** v5.4 单技能路由行为 100% 兼容（v5.4 输入输出 trace 一致，已通过 `tests/golden-traces/v54-baseline.json` 黄金轨迹回归测试）。
> **当前实现状态**：alpha mock —— 设计文档完整，3 个测试脚本通过（composite-recognition 96.7% / orchestrator-execution 100% / failure-defenses 100%），但**真实编排引擎未实现**（测试均为规则模拟）。生产使用前需先实现真实 Orchestrator。

### 启用方式

```bash
# 显式启用 Orchestrator（alpha）
export LOOPENGINE_ORCHESTRATOR=alpha

# 一键回滚到 v5.4 行为
export LOOPENGINE_ORCHESTRATOR=off
```

### 5 类复合任务自动识别

| 任务类型 | 默认技能链 | 编排方式 | 触发关键词 |
|---------|----------|:--:|----------|
| 调研+决策 | brainstorming → system-review → writing-plans | 串行 | 调研 + 决策/选型/对比 |
| 分析+建议 | system-review → brainstorming | 串行 | 审查/分析 + 改进/建议 |
| 诊断+修复 | systematic-debugging → verification-before-completion | 串行 | 报错/Bug + 修复 |
| 设计+实现 | brainstorming → writing-plans → executing-plans | 串行 | 设计 + 实现/开发 |
| 规划+并行 | subagent-driven-development | **并行** | 并行/多任务 + 调研 |

> 规划+并行类复用 `subagent-driven-development` 技能作为并行执行器，不再额外引入 `dispatching-parallel-agents`（避免职责重叠）。

### 显式触发

使用 `/composite <type>` 前缀强制指定复合任务类型：

```
/composite 1 调研下 A 和 B 方案的优缺点
/composite 5 并行调研 fastapi, django, flask
```

### 详细规范

- 5 类复合任务定义 → `references/composite-task-types.md`
- 复杂度评估规则 → `references/complexity-evaluator.md`
- **Plan Orchestrator 协议**（编排技能 · 2026-06-29 重命名）→ `references/plan-orchestrator-protocol.md`
  - 原 `orchestrator-protocol.md` 仍保留作向后兼容（v6.0 期间）
- Trace 格式 → `references/trace-format.md`

> **命名澄清**（2026-06-29 system-review Fix #4）：`plan-orchestrator-protocol.md` 是 skill-hub 编排**技能**的协议；`skills/go/scripts/orchestrator.py` 是 `/go` v4.0 编排**代码任务**的实现（Task Orchestrator）。两者职责清晰划分。

### 一键回滚

任何时候可关闭 Orchestrator 回退到 v5.4：

```bash
export LOOPENGINE_ORCHESTRATOR=off
```

回滚不影响：53 个 SKILL.md / MCP 集成 / 已安装功能。

---

## 🆕 v6.1 新增：三技能协同契约（go / loop / subagent-dd）

> **本节为 v6.1 新增内容，alpha 阶段需显式启用。** v5.4 单技能路由 100% 兼容，v6.0 复合任务 5 类表 100% 兼容。
> **核心目的**：在 v6.0 复合任务编排基础上，显式建模 go（编排层）/ loop（执行层）/ subagent-dd（平行范式）三者的调用边界与桥接模式。

### 启用方式

```bash
# 默认（不启用桥接）
export LOOPENGINE_BRIDGES=disabled    # 默认值

# 启用桥接（alpha）
export LOOPENGINE_BRIDGES=alpha       # 加载 subagent-dd 桥接组件
```

### 三技能定位（不可替代）

| 技能 | 抽象层 | 核心能力 | 不可替代点 |
|------|--------|---------|----------|
| **`go`** v4.0 | 编排层 | 多任务拆分 + DAG + worktree 真并发 + 全局回归 | 唯一具备真并发 + 跨模块集成 |
| **`loop`** v4.1 | 执行层 | 单任务闭环 + 自动化门禁 + 自愈 A/B/C/🎨 | 唯一带自动自愈分级 + 经验库 |
| **`subagent-driven-development`** | 平行执行范式 | 多任务串行 + 人工子代理双阶段审查 | 唯一具备"spec ✅ → code quality"强顺序 + TDD 强制 |

**铁律**：三者**不互相替代**，调度时按下文决策树选型。

### 协同决策树

```
收到任务
  │
  ├─ 有现成 writing-plans 计划？
  │   ├─ 是 → subagent-driven-development
  │   └─ 否 ↓
  │
  ├─ 跨模块 / 需要 DAG / 需要 worktree 真并发？
  │   ├─ 是 → go
  │   │       └─ 默认调 loop --auto 执行子任务
  │   │       └─ 可选 --reviewer=subagent-dd 增强 G10
  │   └─ 否 ↓
  │
  ├─ 端到端单任务闭环 + 自动化门禁 + 自愈？
  │   ├─ 是 → loop
  │   │       └─ 默认走 --default 模式（自适应 L1/L2/L3）
  │   │       └─ 可选 --reviewer=subagent-dd 增强 G9
  │   └─ 否 ↓
  │
  └─ 临时多问题域并行调研（无 plan）？
      └─ 是 → dispatching-parallel-agents
```

### 调用边界（硬约束）

**go → loop 单向调用**：
- `go` Step ⑤ 调度子任务 → 每个 worktree 内调 `loop --auto`
- `loop` 在 `go` worktree 内执行，**不创建嵌套 worktree**
- `loop` 不重复 `go` 的 6 维度需求分析
- `loop` **不**重复调 `system-review`（G10 在 go Step ⑦.5 一次性触发）

**subagent-dd 平行范式**：
- `subagent-dd` **仅在主会话层级**调用
- 派发的 subagent **不**再触发 Orchestrator 路径
- `subagent-dd` **不**与 `dispatching-parallel-agents` 互触发

**subagent-dd vs dispatching-parallel-agents 边界**：
- 有现成 plan → `subagent-driven-development`
- 临时多问题域并行调研 → `dispatching-parallel-agents`
- 冲突时：`subagent-dd` 主导，`dispatching-parallel-agents` 不触发

### 状态协议共享（双轨制 + 共享 spec）

| 状态文件 | 抽象层 | 负责技能 | 存放位置 |
|---------|--------|---------|---------|
| `.orchestrate-state.json` | 宏观（任务树） | go | 项目根目录 |
| `.loop-state-<slug>.json` | 微观（单任务） | loop | worktree 内 |

**双轨制铁律**：两份状态文件**不合并**（合并破坏分层），但**共享 owner/原子写/断点恢复规范**（详见 `skills/shared/references/`）。

### 桥接模式（v6.1 核心新增 · opt-in）

**go G10 桥接**（Step ⑦.5 系统审查）：
```bash
# 默认（v6.1 行为不变）
/go 实现订单管理功能
  └─ G10 = system-review 审查整特性分支

# 启用桥接
LOOPENGINE_BRIDGES=alpha /go --reviewer=subagent-dd 实现订单管理功能
  └─ G10 = subagent-dd final reviewer（3 层问题分级）
```

**loop G9 桥接**（commit 前代码审查）：
```bash
# 默认（v6.1 行为不变）
/loop 实现分页功能
  └─ G9 = code-reviewer 审查单次提交

# 启用桥接
LOOPENGINE_BRIDGES=alpha /loop --reviewer=subagent-dd 实现分页功能
  └─ G9 = subagent-dd 三阶段循环
       （implementer → spec reviewer → code quality reviewer）
```

**6 个桥接契约**（`subagent-driven-development/bridges/contract.py`）：
1. `dispatch_implementer` — 派遣实现者（4 状态枚举）
2. `dispatch_spec_reviewer` — 派遣规格审查（二元 ✅/❌）
3. `dispatch_code_quality_reviewer` — 派遣质量审查（3 层 Issues）
4. `model_select` — 模型选型信号
5. `handle_implementer_status` — 4 状态应对动作
6. `review_gate` — 强顺序约束（spec ✅ → code quality）

### 补全冲突裁决句式（v6.1 增强）

| 重叠组 | 裁决句式 |
|--------|---------|
| **API 开发** | "设计 API 形态" → `api-design-principles`；"写 API 文档" → `api-documentation-generator`；"API 安全审查" → `api-security-best-practices` |
| **技能管理** | "调度技能" → `skill-hub`；"路由到具体技能" → `skill-router`；"发布到市场" → `skill-publisher`；"新建技能" → `skill-creator` |
| **工具类** | "浏览器操作" → `agent-browser`；"修 bug" → `systematic-debugging`；"验证完成" → `verification-before-completion` |
| **审查类** | "审查项目/架构/系统" → `system-review`；"审查单文件/单 PR" → `code-reviewer` |
| **规划与执行** | "需求探索" → `brainstorming`；"写实现计划" → `writing-plans`；"执行计划（多任务串行 + 双审）" → `subagent-driven-development`；"执行计划（跨会话）" → `executing-plans`；"临时问题域分头调研" → `dispatching-parallel-agents` |
| **产品管理** | "产品定位/路线图" → `product-manager`；"写 PRD 文档" → `to-prd` |

### 详细规范

- 三技能调用契约 → `references/skill-relationships.md`
- 共享基础设施 → `skills/shared/references/`
- 桥接组件 → `subagent-driven-development/bridges/contract.py`

### 一键回滚

任何时候可关闭桥接回退到 v6.0（Orchestrator 仍可用）：

```bash
export LOOPENGINE_BRIDGES=disabled
```

回滚不影响：v5.4 单技能路由 / v6.0 复合任务 / MCP 集成 / 已安装功能。

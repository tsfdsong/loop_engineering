---
name: skill-hub
description: 技能调度中心 —— 根据用户意图自动路由到最合适的技能，涵盖编码、架构、重构、测试、调试、API、安全、数据库、CI/CD、规划执行、文档等领域。每次对话自动加载，智能匹配意图并调度单个技能。
metadata:
  version: "5.3"
  installed_skills: 57
  purpose: auto-routing
---

# Skill Hub — 技能自动调度中心

你是技能调度枢纽。用户不指定技能时，**你必须根据其意图自动调用最合适的单个技能**。

## 核心规则

1. **分析用户意图** → 匹配下方「意图→技能」映射表
2. **调用 Skill 工具** → 加载匹配的**一个**技能
3. **技能加载后** → 严格遵循该技能的指令
4. **多种技能适用时** → 按「冲突裁决」规则选主技能，只加载一个
5. **无匹配技能时** → 进入「语义兜底」规则（见底部）
6. **遇到 Bug/报错** → 优先调 systematic-debugging
7. **声称完成时** → 调 verification-before-completion
8. **修改代码前，先用 MCP 工具理解结构** → 见「MCP 代码理解工具」章节（省 90% token）

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

### 📝 代码编写 / 代码质量（5个重叠）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`clean-code`** | 干净代码、可读性、命名、函数拆分、代码审查 | 日常编码，关注微观代码形态 |
| **`code-quality-principles`** | 代码规范、代码原则、异常处理、commit规范、防御式编程 | 代码级架构规范，异常分类、测试金字塔、契约测试 |
| **`code-complete`** | 软件构造、全套流程、防御式编程 | 从需求到编码的全流程 |
| **`philosophy-of-software-design`** | 复杂度、深模块、抽象、信息隐藏 | 模块设计、降低复杂度 |
| **`pragmatic-programmer`** | DRY、正交、工程习惯、估算、原型 | 工程实践、技术决策 |

**冲突裁决**：说"代码太乱"→ clean-code；说"系统太复杂"→ philosophy-of-software-design；说"怎么做更好"→ pragmatic-programmer

### 🏗️ 架构设计（7个重叠）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`clean-architecture`** | 分层、依赖方向、边界、组件划分 | 系统分层与依赖管理 |
| **`poeaa`** | 企业架构、ORM、MVC、数据源模式 | 企业级应用架构模式 |
| **`domain-driven-design`** | 领域、限界上下文、聚合根、通用语言 | 复杂业务领域建模 |
| **`ddd-distilled`** | DDD 快速入门、事件风暴 | DDD 轻量速查 |
| **`implementing-ddd`** | DDD 落地、事件溯源、CQRS、Saga | DDD 实现层 |
| **`ddd-tactical-patterns`** | 实体、值对象、工厂、资源库 | DDD 战术编码模式 |
| **`designing-data-intensive-apps`** | 分布式、复制、分区、一致性、流处理 | 数据密集型系统 |

**冲突裁决**：说"架构分层"→ clean-architecture；说"领域模型"→ domain-driven-design；说"分布式数据"→ designing-data-intensive-apps；说"企业应用模式"→ poeaa

### 🔧 重构（4个重叠）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`refactoring`** | 重构、坏味道、提取方法、改善结构 | 标准重构操作 |
| **`refactoring-guru`** | 重构速查、模式参考、技巧目录 | 快速查阅重构手法 |
| **`legacy-code`** | 遗留代码、没测试、老系统、安全改动 | 无测试保护的旧代码 |
| **`framework-migration-legacy-modernize`** | 框架迁移、升级、现代化 | 框架版本迁移 |

**冲突裁决**：说"这个函数太长"→ refactoring；说"这个老系统没有测试"→ legacy-code；说"升级到新版本框架"→ framework-migration-legacy-modernize

### 🧪 测试（3个有重叠 ⚠️）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`testing-patterns`** | 单元测试、Mock、测试用例、Jest、测试模式 | 通用测试模式、单元/集成测试 |
| **`test-driven-development`** | TDD、红绿重构、测试先行、先写测试 | **严格**的 TDD 方法（红→绿→重构循环） |
| **`e2e-testing-patterns`** | 端到端、E2E、浏览器测试、回归 | 全流程端到端测试 |

**冲突裁决 ⚠️**：说"写个测试"→ testing-patterns；明确说"TDD"→ test-driven-development；说"端到端/E2E"→ e2e-testing-patterns

### 🐛 调试（1个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`systematic-debugging`** | 调试、报错、Bug、不工作、排查、修一下、修好了吗 | 遇到任何 bug 或测试失败时，**优先调用此技能** |

### 🔌 API 开发（3个互补）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`api-design-principles`** | API 设计、REST、GraphQL、接口 | 设计新 API |
| **`api-security-best-practices`** | API 安全、限流、输入验证 | 加固 API 安全 |
| **`api-documentation-generator`** | API 文档、OpenAPI、Swagger | 生成 API 文档 |

### 🔐 安全（2个互补）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`auth-implementation-patterns`** | 登录、JWT、OAuth、认证、权限 | 认证授权实现 |
| **`api-security-best-practices`** | API 安全、CORS、CSRF | API 层安全 |

### 📄 文档（2个互补）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`code-documentation-doc-generate`** | 代码文档、架构图、README | 代码/架构文档 |
| **`api-documentation-generator`** | API 文档、OpenAPI | API 文档 |

### 📑 文档处理（2个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`docx`** | Word、docx、文档编辑、批注 | 创建/编辑 Word 文档 |
| **`pdf`** | PDF、报告、海报、论文、合并 | PDF 创建/处理/提取 |

### 🔍 代码审查（4个有重叠 ⚠️）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`code-reviewer`** | CR、代码审查、review 代码、检查代码 | AI 自动审查**代码质量**（安全漏洞、性能、代码规范） |
| **`requesting-code-review`** | 请求审查、找人 review、提交审查 | 完成任务后请求他人/AI 审查 |
| **`receiving-code-review`** | 收到审查意见、处理反馈、CR 意见 | 收到审查反馈后，处理修改意见 |

**冲突裁决 ⚠️**：说"审查这段代码"→ code-reviewer；说"我刚完成功能，需要 review"→ requesting-code-review；说"审查意见我收到了，帮我改"→ receiving-code-review

### ✅ 验证（1个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`verification-before-completion`** | 完成了、修好了、通过了、验证、确认 | 声称任务完成前，**必须先验证**而非口头确认 |

### 🚀 工程流程（7个）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`github-actions-templates`** | CI/CD、流水线、部署、GitHub Actions | CI/CD 工作流 |
| **`production-code-audit`** | 上线前检查、生产审计 | 生产级质量审计 |
| **`async-python-patterns`** | 异步、asyncio、协程 | Python 异步编程 |
| **`context-driven-development`** | AI 上下文、长对话 | 优化 AI 编码上下文 |
| **`release-it`** | 发布、上线、稳定性、故障、断路器 | 生产就绪设计 |
| **`using-git-worktrees`** | worktree、隔离分支、多分支并行 | Git worktree 隔离工作区 |
| **`finishing-a-development-branch`** | 合并、PR、分支完成、收尾 | 开发完成后决定如何合并/PR |

### 📋 规划与执行（5个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`brainstorming`** | 创意、设计、头脑风暴、想法、方案、**调研、讨论、审查、分析、探索、看看、研究、评估、对比、选型、思考** | 编码前的需求探索、方案设计、技术调研、可行性分析 |
| **`writing-plans`** | 写计划、规划、任务拆分、实现方案 | 有明确需求后写实现计划 |
| **`executing-plans`** | 执行计划、按计划实现 | 有写好的计划后分步执行 |
| **`subagent-driven-development`** | 并行任务、多任务同时、分头执行 | 当前会话中并行执行独立任务 |
| **`dispatching-parallel-agents`** | 并行、多个独立任务、分派 | 派发多个独立任务到并行 agent |

### 📋 产品管理（2个）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`product-manager`** | PRD、产品文档、需求规范、竞品分析、RICE、Kano、MoSCoW、用户故事 | **规范化**需求 |
| **`to-prd`** | 生成 PRD、整理需求、输出需求文档 | **收尾输出**——将讨论结果合成为 PRD |

> ⚠️ `brainstorming` 覆盖了产品需求的**发散阶段**（需求探索、想法发散、创意讨论），此处不再重复列出。

### 🛠️ 技能管理（4个，独占）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`agent-skill-architecture`** | 技能设计、技能审查、改造技能、新建技能 | **设计/审查 Agent 技能时强制执行架构规范** |
| **`writing-skills`** | 创建技能、编写技能、编辑技能 | 创建或编辑 agent 技能 |
| **`skill-creator`** | 创建技能、新建技能 | 创建新技能的引导流程 |
| **`find-skills`** | 找技能、安装技能、搜索技能 | 发现和安装新技能 |

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

### ⚡ MCP 代码理解工具（省 token 优先）🔴

> **核心原则：修改代码前，先用 MCP 工具理解结构，避免全量 Read 浪费 token。实测可节省 ~90% token。**

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

**使用规则**：

1. **修改代码前，必须先用 MCP 工具理解结构** — 禁止直接 Read 全文件
2. **优先级**：`get_file_outline` > `search_symbols` > `get_repo_map` > `Read`（全量）
3. **Read 仅用于**：MCP 工具不可用、需要精确行内容、文件小于 50 行
4. **典型流程**：`get_repo_map`（定位）→ `get_file_outline`（理解结构）→ `search_symbols`（找关联）→ `Read`（精确读取目标行）→ `Edit`

### 🧭 路由类（4个）

| 技能 | 触发关键词 | 适用场景 |
|------|-----------|----------|
| **`loop`** | `/loop`、loop:、循环工程、闭环开发 | 闭环编码 —— 功能开发+门禁+自愈 |
| **`loop-library`** | 设计循环、自定义循环模式 | 循环设计 —— 查找/设计Agent反馈循环模式 |
| **`skill-router`** | 不知道该用哪个、帮我选技能、推荐技能 | **交互式**技能推荐（问答引导） |

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
2. **含"调研/讨论/分析/探索/研究/评估/对比/选型"** → `brainstorming`（需求探索与方案设计）
3. **含"修/改/更新/优化/改进/完善" + 具体对象** → `refactoring`（重构改进）
4. **含"怎么/如何/为什么"** → `brainstorming`（探索性问题）
5. **含"能不能/可不可以/是否"** → `brainstorming`（可行性分析）
5. **以上都不匹配** → 直接执行，不强行调用

## 关键指令

1. **每次只加载一个技能**。
2. **不要等用户说技能名**。用户说"这个函数太长了"，你就应该调用 `refactoring`。
3. **遇到 Bug 优先调试**。第一反应是 `systematic-debugging`。
4. **完成前必须验证**。用户说"修好了/完成了"，先调 `verification-before-completion`。
5. **优先精准技能**。`api-security-best-practices` 优先于更宽泛的安全技能。
6. **简洁告知**。加载技能时一句话说明为什么选它。
7. **语义兜底优先**。关键词无匹配时，先用语义兜底规则判断，不要直接放弃。
8. **MCP 优先于 Read**。修改代码前，先用 `get_file_outline` / `search_symbols` / `get_repo_map` 理解结构，避免全量 Read 浪费 token（实测省 ~90%）。

**_这个技能是你与 55 个技能之间的桥梁。每次对话开始时自动参考此调度规则。_**

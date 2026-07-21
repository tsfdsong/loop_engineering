---
name: go
description: |
  TRIGGER: 跨模块工程任务 / worktree 隔离 / 自动拆分 + 系统审查 / '/go' / '编排' / 'worktree 并发' / '多模块'（不用于：单任务闭环用 loop，纯研究用 deep-research）
  RULE: V4 + V5 主承载 — worktree 隔离 + 派发后按进度汇报
  DETAIL: 本 SKILL.md（编排流程）+ references/
metadata:
  version: "4.1"
  type: slash-command
  mode: multi-tool-orchestration-auto
---

# /go — 全自动编排

你是 `/go` 命令的自动执行引擎。

## ⚠️ 硬规则(不可违反)

> **必须先深入分析项目实际环境,才能推荐方案并执行。这是强制性前置条件。**

违反意味着:
- 禁止: 不读项目文档就推荐方案
- 禁止: 不扫描现有模块就决定"新增一个模块"
- 禁止: 不了解技术栈就选型
- 禁止: 不检查现有代码就写新代码(导致重复造轮子)

**你可以不等人确认,但你不能不分析项目就做决定。**

## 🔴 硬约束(不可违反)

1. **禁止污染 main/master/test 分支**：所有编码工作在 `go-<slug>` feature 分支上进行
2. **Worktree 隔离**：并发子任务通过 git worktree 物理隔离，零文件冲突
3. **测试闸门**：合并后自动跑测试，失败则阻断
4. **分支保护**：保护分支上有未提交改动时，/go 直接拒绝执行
5. **G9/G10 审查**：每个子任务 commit 前通过 G9 代码审查（loop 内），整个特性分支交付前通过 G10 系统审查（go Step ⑦.5）
6. **🔴 MCP 红线（最高优先级）**：遵循 AGENTS.md §1（v6.11 S1-S6 场景矩阵）的单点真源。本技能**不重复承载**红线全文，仅作行为约束：探查代码结构按 S1-S6 选层，S3 修改已知位置可直接 Read(offset/limit) 属合规。违规判定以 AGENTS.md §1.5 为准。

## 命令格式

```
/go 功能描述，验收条件1，验收条件2，...
/go-fast 功能描述                # 强制 L1 直通档
/go-full 功能描述                # 强制 L3 完整档
```

## 核心原则:全程自动化

> **所有需要确认的地方,系统自动推荐方案、自动执行、自动记录推荐理由。**
> 不使用硬闸门暂停等用户——全部改为**审计闸门**(自动通过+记录理由,可追溯但不等停)。

**自动决策三原则**:
1. **推荐**: 分析项目上下文→给出最优方案
2. **执行**: 验证通过后直接执行,不等人确认
3. **记录**: 决策理由写入 `decision_log`,交付报告追溯

**分层协作**:

| 层级 | 职责 | 如何协作 |
|------|------|---------|
| go(编排层) | Feature分支→项目上下文分析→DAG/并行前沿→Worktree并发→合并→测试闸门 | 为 loop 提供隔离 worktree + 完备任务包 |
| loop(执行层) | 单任务薄闭环:编码↔门禁↔自愈↔交付 | 在 go worktree 内执行,不创建嵌套 worktree |

go 负责「拆任务、算前沿、分对工具」；loop 负责「把每个已验收任务做对」。go 不碰执行层细节。

---

## Thin-loop 派发契约（go → loop / `--auto`）

> go 派发 loop 时，loop 是**薄执行器**，不是迷你编排器。契约与 `skills/loop` + `skills/using-loopengine` 职责表对齐。

**任务包硬要求（缺一不可）**：

1. **可执行目标（goal）** — 已落到可实施表述（非「要不要做 X」选型问句）
2. **验收条件（acceptance）** — 可测、可判过/不过的清单

**loop 禁止重做（由 go / brainstorming / writing-plans 承担）**：

- 产品级需求确认 / brainstorming「需求分析」轮
- writing-plans 级实施计划拆分
- 编排级复杂度 Ask / family 路由

**不完整包 → 失败，禁止假装**：

- 任务包缺 goal 或 acceptance → **不得**派发 loop，也不得假设 `--auto` 会「发明」验收
- 回写失败理由（如 `missing_goal_or_acceptance`），回到 go 补齐后再派
- go 在 Step ②/③ 产出验收；派发前自检包完备性

---

## Step 0: 意图识别（v2.0 · family-first · D4.1）

> go 在 Step 0 承担 family 识别 + DAG 组装，再委托 direct_skill / loop / 真并发执行。

用户目标进入后：

1. **family-first 识别**（8 类：review / debug_fix / design_build / research_compare / web_qa / parallel_investigation / refactor / test）
2. 单 family → 抽取 `actions[]` + `scope` + `goal`
3. 多 family → AskUserQuestion 澄清（不混编，除非落在 `dag-rules.yaml > global.allowed_combinations` 白名单内）
4. **confidence gate**（< 0.70 澄清 / 0.70-0.84 确认 / ≥ 0.85 自动）
5. **委托路由（side-effect-first）**：
   - read（只读分析 / 审查 / 调研）→ `direct_skill`
   - single write（单任务写代码 / 修复）→ `loop`
   - multi write（跨模块 / 多子任务实施）→ 继续 Step ① L0 复杂度评估 → Step ⑤ 真并发

详见：
- `references/family-routing.md`（8 family 定义 + 默认 actions[] + 组合白名单）
- `references/dag-assembly.md`（rule-first 拓扑 + confidence gate + **并行前沿** + 与 Step ③/⑤ 协同）

**设计原则（family-first · v2.0）**：
1. Family-first（先 family 再 action）
2. Action, not skill（意图落到稳定 action）
3. Rule-first（LLM 理解意图，规则表决定拓扑）
4. Side-effect-first（按副作用委托执行器）
5. Single family（或白名单组合，否则澄清）
6. Confidence gate

---

## 执行流程

```
/go 触发
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step 0  意图识别（family-first · D4.1）          │
├─────────────────────────────────────────────────┤
│ • family-first 识别 8 family（references/        │
│   family-routing.md）                            │
│ • 多 family → AskUserQuestion 澄清               │
│ • 单 family → 抽 actions[] + scope + goal        │
│ • confidence gate（references/dag-assembly.md）  │
│ • 委托：read→direct_skill / single→loop /        │
│   multi→继续 Step ⓪                             │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ⓪  断点续跑检测(启动时最先执行)              │
├─────────────────────────────────────────────────┤
│ • 检查 .orchestrate-state.json                   │
│ • 存在且未完成 → 自动续跑(不等用户确认)           │
│   (详见 references/breakpoint-recovery.md)        │
│ • 不存在 → 进入 Step ①                           │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ①  L0 复杂度评估(纯规则 · 零 token)         │
├─────────────────────────────────────────────────┤
│ • 读取 references/complexity-rules.md 规则       │
│ • 检查命令标志(-fast→L1, -full→L3)              │
│ • 否则按信号评估(关键词/文件数/跨工具)            │
│ • 输出: 评估为 [级别], 理由: [...]               │
│ • 📝 记录到 decision_log                        │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ①.5  项目上下文分析 / 落地约束分析(硬规则)   │
│           （≠ brainstorming 产品「需求分析」）      │
├─────────────────────────────────────────────────┤
│ ⚠️ 必须完成以下全部6个维度分析,否则禁止进入Step②  │
│ ⚠️ 本步分析「仓库能落地什么」——不是产品需求调研   │
│                                                 │
│ 【维度1: 项目身份识别】                            │
│  • 扫描项目文档(自动发现,不硬编码文件名):           │
│    - CLAUDE.md / AGENTS.md / README.md / CONTRIBUTING.md │
│    - docs/ 下所有 .md 文件(设计文档/调研报告/方案)  │
│    - deploy/ 下 docker-compose.yml(如有,部署架构)   │
│  • 从中提取: 项目是什么、做什么、怎么部署           │
│  • 产出: 项目类型(全栈Web/纯后端/CLI/库/技能仓库/  │
│    单页应用/其他) + 部署方式(无/Docker/Serverless) │
│                                                 │
│ 【维度2: 技术栈扫描】                              │
│  • 自动探测 manifest(不预设):                       │
│    Python(pyproject.toml/setup.py/requirements*) │
│    Node(package.json) · Go(go.mod) · Rust(Cargo.toml)│
│    多语言/无 manifest → 标注并降级为目录结构推断    │
│  • 识别: 主语言 + 框架 + DB/缓存/存储(如适用)      │
│  • 产出: 完整技术栈清单 + 版本约束                 │
│    (非 Web 项目标注"无前端/无DB")                  │
│                                                 │
│ 【维度3: 现有模块盘点】                            │
│  • 自动发现源码根(不硬编码路径):                    │
│    - 探测 src/ app/ lib/ cmd/ skills/ 等常见根     │
│    - Web 项目: backend/app/* + frontend/src/*     │
│    - 单仓多包/库: 顶层包目录                       │
│    - 技能仓库/纯文档: 按子目录/文档章节划分"模块"  │
│  • 识别: 已有哪些业务模块/包/技能/章节?            │
│  • 产出: 模块清单 + 模块职责描述                   │
│    (无源码项目 → 以文档/配置单元为"模块")          │
│                                                 │
│ 【维度4: 功能匹配分析(★最关键)】                   │
│  • 新功能与哪个现有模块最相关?                     │
│  • 是否可以扩展现有模块(优先)?                     │
│  • 还是需要新建模块?                              │
│  • 哪些已有接口/表/工具函数可以直接复用?           │
│  • 产出: 匹配结论 + 复用清单 + 新建清单            │
│                                                 │
│ 【维度5: 架构约束检查】                            │
│  • 从维度1-4探测结果**动态生成**检查项(不预设):     │
│    - DB 项目: async/sync? ORM? 迁移工具?          │
│    - Web 后端: 分层模式(router→service→model)?    │
│    - Web 前端: 框架+UI库+TS模式?                  │
│    - 库/CLI: 包结构/入口约定/命名规范?             │
│    - 技能仓库: SKILL.md frontmatter 规范?         │
│    - 通用: 测试框架? lint/format 配置?             │
│  • 如某类不适用 → 标注"N/A"并说明,不视为缺失       │
│  • 产出: 架构约束清单(按实际项目类型裁剪) +        │
│    违背风险提醒                                   │
│                                                 │
│ 【维度6: 风险排查 + 方案生成】                      │
│  • 方案A(推荐): 基于维度4+5分析的最优路径          │
│  • 方案B: 备选路径(何时选?权衡了什么?)             │
│  • 风险评估: 改了核心链路?有数据迁移?              │
│  • 产出: 推荐方案 + 替代方案 + 风险清单            │
│                                                 │
│ ▸ 完成后自动生成《项目上下文分析报告》写入 decision_log │
│ ▸ 报告结构(按维度1探测结果填充,N/A 项明确标注):    │
│   项目: [项目名] · 类型: [全栈Web/后端/CLI/库/     │
│         技能仓库/其他] · 部署: [Docker/无/...]    │
│   技术栈: [主语言 + 框架 + DB/缓存/存储(无则N/A)] │
│   现有模块: [列表或"N/A(无源码)"]                  │
│   匹配分析: 扩展 [模块名] · 复用 [接口/表/工具]    │
│   推荐方案: [方案A]                                │
│     采纳理由: [基于维度4+5的推理]                  │
│   替代方案: [方案B] · 未采纳理由: [...]            │
│   风险: [高/中/低] · [具体风险]                    │
│                                                 │
│ ▸ 全部6个维度产出完整 → ✅ 准入Step②               │
│ ▸ 任一维度缺失 → ❌ 禁止进入Step②                  │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ②  状态初始化 + 方案提交(📝审计闸门)        │
├─────────────────────────────────────────────────┤
│ • 创建 .orchestrate-state.json                  │
│   (格式见 references/state-protocol.md)          │
│ • 记录 Step①.5 产出的《项目上下文分析报告》全部内容 │
│ • 验收条件 = 用户指定 + 自动推理补全             │
│   （派发 loop 前必须已有可执行 goal + acceptance） │
│ • 📝 审计闸门: 自动通过,决策全部记录             │
│   准入条件: Step①.5的6个维度全部产出完整 ✅      │
│   准入失败 → 回到Step①.5补全缺失维度            │
│ • 无需等待用户确认,直接进入 Step③               │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ③  任务拆分(按 tier 裁剪)                  │
├─────────────────────────────────────────────────┤
│ • 🟢 L1: 不拆分,单任务直接执行                  │
│ • 🟡 L2: 按模块拆 2-5 个子任务,串行依赖         │
│ • 🔴 L3: 深度垂直拆分 + 依赖 DAG                │
│   无依赖任务标记可并发(拓扑序调度)              │
│ • 拆分方案自动执行,写入状态文件                  │
│ • 每个子任务包必须含 goal + acceptance（thin-loop）│
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ⑤  调度执行（DAG 并行前沿 · Worktree）       │
├─────────────────────────────────────────────────┤
│ 详见 references/dag-assembly.md（并行前沿算法与拓扑详情）。│
│ 本步行为摘要（P0）：                                  │
│                                                 │
│ ▸ 并行前沿调度（写码默认开启 · ≥2 写安全独立节点）: │
│   1. DAG 组装完成后，计算 **ready frontier**     │
│      = 依赖已满足（入度 0 / deps done）的节点集  │
│   2. 前沿内写集 / worktree 冲突检测：             │
│      - 无共享写集且可 worktree 隔离 → 并行派发   │
│      - 写集重叠或无法隔离 → **同前沿改串行**     │
│   3. 对每个写安全节点：独立 worktree + 完备任务包 │
│      → 宿主并行派 **执行器**（loop / --auto）    │
│   4. 前沿汇合（全完成或失败策略）→ merge/交接    │
│      → 再算下一前沿                              │
│   5. 🟢 L1 / 单节点 → **不**走并行调度税，直通 loop │
│                                                 │
│ ▸ Subagent = 执行器 only：                        │
│   - 按图调度，引用 skills/loop 等文档路径         │
│   - **不做** Subagent 角色注册表 / agents/registry │
│   - **不**发明新 slash command（仍用 /go）        │
│                                                 │
│ ▸ Worker Contract / Cursor 桥接（实现细节）:      │
│   1. 创建 feature 分支 go-<slug>                 │
│   2. 每任务隔离 worktree + WorkerTaskPacket      │
│      （goal + acceptance 必填）                  │
│   3. 同前沿多节点一次多派（cursor / zcode adapter）│
│   4. 顺序 merge → merge_resolve packet 解冲突    │
│   5. 安全闸: pytest/npm test → 通过才继续        │
└─────────────────────────────────────────────────┘
    │ 所有子任务完成
    ▼
┌─────────────────────────────────────────────────┐
│ Step ⑤ 并发形态（v2.0 · Agent 多 subagent）      │
├─────────────────────────────────────────────────┤
│ > 真物理并发 = 宿主 Task/Subagent + worktree；   │
│   调度概念只有「并行前沿」，无角色产品层。         │
│                                                 │
│ 用 Agent 工具同时派（多执行器 subagent）：        │
│ • supervisor（持续监控 · 状态文件                │
│   .supervisor-state.json 通信）                 │
│ • loop A/B/C（各自 worktree · 物理并发 ·         │
│   每 loop 一个执行器 subagent · 非「loop 角色」） │
│                                                 │
│ 并发工作流（前沿一次派齐可并行节点）：            │
│   go 主流程（算 frontier → Agent 工具同派）       │
│     ├─→ supervisor（监控）                        │
│     ├─→ loop A（worktree A · 执行器）             │
│     ├─→ loop B（worktree B · 执行器）             │
│     └─→ …（仅当前前沿内写安全节点）               │
│          ↓                                       │
│   supervisor 状态文件通信（.supervisor-state.json）│
│          ↓                                       │
│   前沿完成 → 下一前沿；全完成或 r4_pending=true  │
│          ↓                                       │
│   go 主流程 merge → G10 → 交付                   │
│                                                 │
│ 降级路径（如 Agent 多 subagent 跑不起来）：        │
│ • 退路 1：supervisor 作为 go 内嵌监控子循环        │
│   （形态 A · 不真并发）                           │
│ • 退路 2：worktree 顺序 merge（v1.x 现状 · 保底） │
│                                                 │
│ 详见 skills/supervisor/SKILL.md +               │
│     references/dag-assembly.md                  │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ⑥  上下文交接(机制⑥ · 已在⑤逐步完成)        │
├─────────────────────────────────────────────────┤
│ 确认所有交接链完整,生成完整交接链报告            │
│ handoff 包含: gate_result(loop门禁摘要)          │
│ (详见 references/handoff-protocol.md)            │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ⑦  全局集成回归(机制⑦)                     │
├─────────────────────────────────────────────────┤
│ • 全量测试套件(覆盖所有子任务合集)               │
│ • 跨模块接口契约自动校验                          │
│ • 前后端联调(loop 门禁覆盖了单任务,go做跨任务)   │
│                                                 │
│ 通过 → 自动进入交付                              │
│ 失败 → 自动回退失败子任务重做(不等人)            │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ⑦.5 系统审查(📝 审计闸门 · 每个特性分支 1 次)  │
├─────────────────────────────────────────────────┤
│ • 调用 skills/system-review 技能,深度自动判断: │
│   - 改动 < 3 文件且未跨模块 → 仅 Step 1 自洽性  │
│   - 改动 ≥ 3 文件或跨模块 → Step 1 + 2 架构深度 │
│   - 跨架构级改动 → 全三步(自洽性+深度+持续改进)  │
│ • 检查范围: git diff main..feature-branch 累积变更 │
│ • 报告: 自洽性问题/架构问题/改进路线图(append)  │
│ • 🔴 系统审查 ERROR → 暂停交付, 报告问题, 等待人工 │
│ • ⚠️  WARNING → 记录到交付报告, 不阻断             │
│ • 📝 与 loop 的 G9 不重复:                       │
│   - G9 (loop 内) = 单子任务代码层审查            │
│   - G10 (go 内) = 整个特性分支系统层审查          │
│                                                 │
│ 🆕 v6.1 桥接模式（opt-in）:                       │
│   export LOOPENGINE_BRIDGES=alpha                 │
│   /go --reviewer=subagent-dd ...                  │
│   └─ G10 = subagent-dd 的 final reviewer          │
│        (3 层问题分级 + Assessment 字段)            │
│   └─ 桥接失败自动降级到 system-review             │
│   └─ 详见 shared/references/g9-g10-coordination.md │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Step ⑧  交付(📝审计闸门 · 自动合并)               │
├─────────────────────────────────────────────────┤
│ • 自动生成交付报告(含完整决策追溯):              │
│                                                 │
│   📊 交付报告                                    │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│   ┌─ 项目上下文分析                              │
│   │  项目类型: 全栈Web · 技术栈: React+FastAPI   │
│   │  已有模块: points/orders/users                  │
│   │                                             │
│   ├─ 推荐方案                                    │
│   │  方案: 扩展现有 API(方案A)                   │
│   │  理由: 复用 points 表,避免新模块,影响最小    │
│   │                                             │
│   ├─ 替代方案(未采纳)                            │
│   │  方案B: 新建独立模块                          │
│   │  未采纳: 与现有架构不一致,引入额外依赖       │
│   │                                             │
│   ├─ 执行摘要                                    │
│   │  子任务: 3/3 完成 · 门禁: 全绿              │
│   │  降级: 无 · 回归: 通过                       │
│   │                                             │
│   └─ 质量分层                                    │
│      loop门禁全绿: 2个任务(高)                   │
│      ZCode直通: 0个任务                         │
│      DeepSeek降级: 0个任务                      │
│                                                 │
│ • 🛑 degraded=true 强制人工闸门(v6.x 硬约束):     │
│   任一子任务 degraded=true → 禁止自动合并,        │
│   必须由人工在交付报告中签字 review 后方可合并。  │
│   理由: 降级链产物质量分层已知偏低,自动进 main    │
│   违反"完成前验证红线"诚信端要求。                │
│ • 📝 自动合并到主分支(条件:门禁全绿+回归通过+     │
│   无 degraded=true 任务)                          │
│   (留 --interactive 标志供用户可选手动模式)       │
│ • 清理 .orchestrate-state.json                   │
└─────────────────────────────────────────────────┘
    │
    ▼
✅ 完成
```

---

## 自动决策原则

| 场景 | v2.0 / v4.1 行为 |
|------|----------|
| L0评估 | 纯规则自动评估→记录理由 |
| **项目上下文分析** | **硬规则: 6维度强制分析(项目身份/技术栈/模块盘点/功能匹配/架构约束/风险方案)→产出报告（≠产品需求分析）** |
| **方案推荐** | **基于6维度分析结论 → 给出最优方案 + 替代方案 → 记录采纳和未采纳理由** |
| 拆分确认 | 自动拆分+拓扑排序→直接写入状态；子任务包含 goal+acceptance |
| 子任务执行 | 派 loop --auto（thin-loop 契约）；门禁矩阵+自愈闭环；缺验收则失败回交 |
| 并行前沿 | DAG ready 节点写安全则同前沿并行；写集冲突则串行；L1/单节点无调度税 |
| 降级兜底 | loop exhausted → ZCode直连 → DeepSeek,逐级降级不打断 |
| 全局回归 | 自动跑→通过→交付→失败→自动回退重做 |
| 合并决策 | 门禁全绿+回归通过+无 degraded=true →自动合并(否则人工闸门) |

**唯一仍需人工的地方**(安全闸门,非工具限制):
- 合并后测试失败 → 保留 feature 分支,等待人工排查

---

## 降级兜底(自动无缝)

```
首选: ZCode + loop --auto(门禁全绿,质量最高)
  ↓ exhausted/quota?
备选: ZCode CLI 直连(无门禁保护,但快速)
  ↓ 429/quota?
兜底: DeepSeek API(标记 degraded,低质量但可交付)
```

自动触发:捕获 429/quota_exceeded → 立即切下一级,执行不打断。

---

## 三档执行级别

| 维度 | 🟢 L1 直通 | 🟡 L2 标准 | 🔴 L3 完整 |
|------|:---:|:---:|:---:|
| 拆分 | ❌ | ✅ 串行 | ✅ +并行前沿 |
| 项目上下文分析 | 一句话 | 技术选型 | 完整 6 维 |
| loop门禁 | 基础验证 | 门禁矩阵 | 矩阵+自愈 |
| 降级 | ❌ | ✅ | ✅ |
| GLM-5.2推理 | off | high | max |
| 合并 | 自动合并 | 自动合并 | 自动合并(加审计摘要) |

---

## 关键约束

1. **⚠️ 硬规则: 必须先完成项目上下文分析 / 落地约束分析(6维度),才能推荐方案并执行。** 不读项目文档、不扫描现有模块、不检查架构约束 = 禁止进入Step②。本步≠ brainstorming 产品「需求分析」。
2. **全自动执行**。所有决策遵循推荐→执行→记录,不等人确认。
3. **审计可追溯**。所有自动决策 + 项目上下文分析报告写入 decision_log。
4. **结合项目上下文**。落地分析+方案推荐+验收条件都基于项目实际代码(不凭空猜测)。
5. **Thin-loop 契约**。派 loop / `--auto` 必须带可执行 goal + acceptance；包不完整则失败回交，禁止假设 loop 会发明验收或重做需求/计划。
6. **并行前沿默认**。DAG ready 且写安全的独立节点同前沿并行；写集/worktree 冲突则串行；L1/单节点无并行调度税。Subagent 仅执行器，无角色注册表。
7. **L0 纯规则零 token**。不为"省token"而花token。
8. **断点恢复优先**。启动第一件事是检测断点。
9. **降级执行不打断**。配额耗尽自动切 DeepSeek。
10. **原子性保障**。in_progress 任务记 git HEAD,中断恢复 reset 到 HEAD。
11. **编排层不碰执行层**。go传最小信号（完备任务包）,Worker Contract adapter 自行管理执行细节。

---

## Cursor 文件桥接（v5.0 · profile=cursor）

当 `orchestrator.py` 在 Cursor 子进程运行、无法直接调用 `Task` 工具时：

1. `CursorSubagentAdapter` 将 `WorkerTaskPacket` 写入 `.go/dispatch/queue/<task_id>.*`
2. stdout 输出 `GO_WORKER_DISPATCH_REQUEST {...}` sentinel
3. **宿主 Cursor agent** 读取 `prompts/<task_id>.md`，用 **Task** 派发 subagent
4. subagent 在 `workspace.root` 内完成后，宿主将 `WorkerResult` 写入 `results/<task_id>.result.json`
5. orchestrator 轮询到 result 后继续 commit / merge

| 环境变量 | 说明 |
|----------|------|
| `LOOPENGINE_GO_RUNTIME=cursor` | 强制 Cursor adapter |
| `LOOPENGINE_CURSOR_DISPATCH=file` | 强制文件桥接 |
| `LOOPENGINE_CURSOR_DISPATCH_POLL_SEC` | 轮询超时（秒） |

详见 `references/cursor-dispatch-protocol.md`。

---

## 参考文档

| 文档 | 内容 |
|------|------|
| `references/family-routing.md` | 🆕 D4.1 · 8 family 识别 + 组合白名单 |
| `references/dag-assembly.md` | 🆕 D4.1 · rule-first DAG 组装 + confidence gate + **并行前沿** |
| `references/complexity-rules.md` | L0 复杂度评估规则 |
| `references/state-protocol.md` | 双轨制状态文件协议 |
| `references/breakpoint-recovery.md` | 断点恢复三重保障 |
| `references/handoff-protocol.md` | 上下文交接协议 |
| `references/handoff-schema.json` | family 阶段 handoff JSON Schema |
| `references/cursor-dispatch-protocol.md` | Cursor Task 文件桥接协议 |
| `references/worker-task-packet.schema.json` | Worker Contract 输入 schema |
| `references/degradation.md` | DeepSeek 降级兜底 |
| `routing-rules.yaml` | 工具路由规则配置 |

---

## §N. 端到端示例（v2.0 强化）

### 示例 1：跨模块新功能（L3 · go + supervisor + 3 loop 并发）

**用户输入:** `/go 实现订单管理功能 · 验收：创建订单/查询订单/取消订单`

**go 流程（10 步）：**

1. **Step 0 意图识别** → family=design_build（单 family · confidence 0.92 · 自动档）
2. **Step ① L0 评估** → L3（跨模块 + 多接口 · 触发深度拆分 + 真并发）
3. **Step ①.5 6 维项目上下文分析**（落地约束 · ≠产品需求分析）：
   - 维度1 项目身份：全栈 Web（FastAPI + React）· Docker 部署
   - 维度2 技术栈：Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL
   - 维度3 现有模块：users / products / points（无 orders）
   - 维度4 功能匹配：**复用 existing users 表**（FK user_id）+ **新建 orders 模块**
   - 维度5 架构约束：遵循 router→service→model 分层 · 用 Alembic 迁移
   - 维度6 风险方案：方案 A 新建 orders 模块（推荐 · 与现有分层一致）/ 方案 B 扩展 products（未采纳 · 职责混淆）
4. **Step ③ 拆分** → 3 子任务 DAG（每包含 goal + acceptance）：
   - T1: orders schema + Alembic migration（**独立** · 无依赖）
   - T2: orders API CRUD（创建/查询/取消）· **依赖 T1**
   - T3: orders 单元 + 集成测试 · **依赖 T2**
5. **Step ⑤ 并行前沿派发**（ready 写安全节点一次派齐执行器）：
   - 前沿 1：`supervisor` + `loop T1`（T2/T3 依赖未满足 · 不在前沿）
   - T1 完成后前沿 2：`loop T2`
   - T2 完成后前沿 3：`loop T3`
   - （若另有无依赖写安全节点，与 T1 同前沿并行；写集冲突则串行）
6. **supervisor 监控时序**：
   - T+0:30s → T1 done（schema + migration G0-G9 全绿）
   - T+0:31s → T2 启动
   - T+4:20s → T2 G3 test 失败（cancel 接口边界 case）→ **supervisor R1 重启**（重派 T2 到新 worktree）
   - T+7:50s → T2 再次 exhausted → **supervisor R2 降级**（DeepSeek 接手 cancel 接口 · 标 degraded=true）
   - T+9:10s → T2 done（degraded）→ T3 启动
   - T+12:40s → T3 done（测试全绿 · 含 cancel 边界 case）
7. **Step ⑥ merge**：顺序 merge T1 → T2 → T3（T2 含 degraded 标记 · 进交付报告）
8. **Step ⑦ 回归**：pytest 全量（含 users + products + orders）→ 全绿
9. **Step ⑦.5 G10 system-review**：架构一致性 ✅（orders 遵循现有分层 · 未污染 users 模块）· WARNING 1 条（cancel 接口建议加幂等键 · 登记后续）
10. **Step ⑧ 交付**：自动 merge to `feature/orders`（因 T2 degraded=true → **触发 🛑 人工闸门** · 交付报告含完整决策追溯 · 等用户签字 review）

**交付报告关键字段：**
- 质量分层：loop 门禁全绿 2 任务（T1/T3 · 高）· DeepSeek 降级 1 任务（T2 · degraded=true）
- 决策追溯：R1 重启 1 次 + R2 降级 1 次（cancel 接口边界 case 复杂度超预期）
- 验收：创建/查询/取消 3 接口全实现 · 测试覆盖 92%

### 示例 2：L1 单文件修复（直通档 · 不拆分）

**用户输入:** `/go-fast 修复登录页 typo "Sign ni" → "Sign in"`

**go 流程（精简 · L1 直通）：**

1. Step 0 意图识别 → family=debug_fix（confidence 0.98 · 自动）
2. Step ① L0 → L1（`-fast` 强制 · 单文件单行）
3. Step ①.5 → 一句话项目上下文分析（项目=Web · 单字符串替换 · 无架构影响）
4. **委托 loop**（side-effect=single write · 包含 goal+acceptance）→ loop --level=L1
5. loop 跑 G0/G1/G9（3 核心门禁）→ 全绿
6. Step ⑧ 自动 merge（无 degraded · 门禁全绿）

**关键差异（vs 示例 1）**：L1 不拆分、**无并行前沿调度税**、不派 supervisor、不跑 G10（改动 <3 文件）。

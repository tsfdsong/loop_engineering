 # AI Agent 工程白皮书（完整版）
 ## Skills · Agent CLI · Loop Engineering · Harness · 协议与治理（2024–2026）
 
 - 版本：v1.0（研究版）
 - 日期：2026-06-26
 - 读者：技术负责人 / 架构师 / 研发工程师 / 平台与工程效率团队 / 安全与治理团队
 - 研究范围：公开资料（官方文档、官方工程博客、协议规范、论文与基准）；不包含具体落地实施与本地项目分析
 
 ---
 
 ## 摘要（Abstract）
 
 2024–2026 年，AI Agent 领域从“能对话”进入“能做事”，并在 2026 年出现显著的工程化拐点：行业重心从 Prompt Engineering 和上下文堆叠，迁移到 **Harness Engineering / Loop Engineering**，即把模型置于一个可持续运行、可验证、可恢复、可治理的闭环系统中。与此同时，**Skills** 从私有 prompt 模板逐渐演化为可移植、按需加载、可版本化的能力包；**Agent CLI** 从终端聊天工具演化为“代理运行时入口”，具备多步执行、工具调用、验证、记忆与自动化能力；**协议层**（MCP、A2A）开始承担生态互操作的底座角色；**安全治理**从模型对齐问题上移到运行时控制问题，出现“把 agent 当作潜在 insider threat”的系统级路线（AI Control）。
 
 本白皮书提供一个统一的工程与产业框架：以 `Loop（闭环）` 为核心，解释 Skills、CLI、工具协议、编排框架、长任务恢复、评测与安全治理如何在 2024–2026 的产业演进中组合成“可生产”的 Agent 技术栈，并给出关键趋势与决策要点。
 
 ---
 
 ## 关键结论（Key Findings）
 
 1. **Agent 的差异化不再主要由模型决定，而由“系统”决定**：工具契约、执行环境（sandbox/shell/filesystem/browser）、验证机制、记忆与状态外置、恢复与续跑、审批与权限、可观测与评测闭环。OpenAI 将此概括为 Harness Engineering，并给出了“agent-first world”的工程实践报告。[1][2][3]
 2. **Loop Engineering 在 2026 形成统一话语**：本质是把“人手动 prompt 驱动”变为“系统定期/事件触发地唤醒 agent，检查结果，记录状态，再决定下一步”。Addy Osmani 给出了可复用的组成原语：automations、worktrees、skills、connectors、sub-agents、external state。[4]
 3. **Skills 正在标准化**：从 Anthropic 的 Agent Skills 体系到开放规范 agentskills.io，再到 OpenAI、Google、Microsoft 的兼容实现，Skills 成为“组织知识与 SOP 的可移植载体”，并采用渐进披露（progressive disclosure）降低上下文常驻成本。[5][6][7][8][9]
 4. **Agent CLI 的本质是 harness 前台**：Claude Code、Codex CLI/App、Gemini CLI、Copilot CLI 等都围绕同一闭环：理解→行动→验证→继续，并发展出 subagents、automations、worktree isolation、policy/approval modes 等工程能力。[10][11][12][13][14][15]
 5. **协议栈开始成型**：MCP 解决 agent-to-tool/context，A2A 解决 agent-to-agent；两者分别覆盖“工具接入”和“协作互操作”，并与 Skills/CLI/Loop 产生互补关系。[16][17][18][19]
 6. **评测正从“答案正确”迁移到“轨迹正确 + 长任务能力 + 成本/风险”**：OSWorld、WebArena、GAIA、AgencyBench 等基准将“真实环境执行、长时任务、工具链可靠性”纳入评价中心。[20][21][22][23]
 7. **安全治理从“内容安全”升级到“运行时控制”**：DeepMind 的 AI Control Roadmap 将 agent 视为潜在 insider threat，强调监控推理/行动/计划、权限分级、实时阻断与响应，并给出覆盖率、召回率、响应时间等系统指标。[24]
 
 ---
 
 ## 目录（Table of Contents）
 
 1. 背景与问题定义
 2. 术语与统一框架：从 Prompt 到 Loop
 3. 产业演进时间线（2022–2026）
 4. 参考架构：Agent 工程栈（Skills/Tools/Memory/Harness/Loop/Protocols）
 5. Skills 深度研究（标准、实现、边界、治理）
 6. Agent CLI 深度研究（产品谱系、运行机制、共性原语）
 7. Loop Engineering 与 Harness Engineering（长任务、恢复、并行与自动化）
 8. 协议与平台：MCP、A2A、Agents SDK、ADK、Microsoft Agent Framework
 9. 评测与基准：从结果到轨迹、从短任务到长任务
 10. 安全与治理：审批、沙箱、运行时控制与防御纵深
 11. 典型场景与案例：Research / Coding / Browser-Computer Use / 企业平台
 12. 趋势展望与建议：未来 12–24 个月的技术路线图
 A. 术语表（Glossary）
 B. 参考文献（References）
 
 ---
 
 ## 1. 背景与问题定义
 
 ### 1.1 为什么“Agent 工程化”在 2026 成为主线
 
 在 2022–2024 年，行业的主问题是“如何让模型更好地回答”，因此形成了大量 prompt 技巧与链式推理范式（如 ReAct）。[25]
 
 但随着模型具备更强的工具调用能力，用户开始把模型放入真实环境：代码仓库、终端、浏览器、企业系统、工单系统、知识库与数据湖。此时挑战迁移为：
 
 - **可靠性**：一次对话能写出看似正确的方案，但能否稳定执行几十步、持续修复、直到验证通过？
 - **可验证性**：如何判断“真的完成了”？如何防止模型自评“看起来对”？
 - **可恢复性**：长任务跨会话、跨窗口时如何续跑？
 - **可治理性**：当 agent 能执行 shell、改文件、发消息、动数据时，如何控制权限、审计、阻断？
 - **可复用性**：组织知识与 SOP 如何沉淀成可加载资产，而不是反复解释？
 
 这些问题共同推动了 harness、loop、skills、自动化、协议与安全控制的系统化发展。[1][2][3][4][24]
 
 ### 1.2 白皮书的研究问题
 
 本白皮书围绕三个核心对象及其关系展开：
 
 - **Skills**：组织知识与可复用能力如何标准化、按需注入代理？
 - **Agent CLI**：终端如何从“聊天界面”变成“代理运行时入口”？
 - **Loop Engineering**：如何把 agent 的多步执行变成系统级闭环（触发、执行、验证、记忆、恢复、治理）？
 
 并进一步回答：这些对象如何由 MCP/A2A 等协议连接、被 Agents SDK/ADK/Agent Framework 等平台支撑、被评测体系衡量、被安全治理体系约束。
 
 ---
 
 ## 2. 术语与统一框架：从 Prompt 到 Loop
 
 ### 2.1 定义：什么是 AI Agent Loop
 
 一个可生产的 agent 不应只被定义为“能多轮对话 + 会调工具”。更接近工程事实的定义是：
 
 **Agent 是一个在环境反馈下持续迭代的闭环系统**，典型循环可抽象为：
 
 1. Observe / State：读取环境状态（文件、网页、日志、数据库、工单等）
 2. Plan：分解任务、选择工具/子任务、设定阶段目标
 3. Act：执行动作（调用 tool / shell / browser / 写文件 / 发请求）
 4. Verify：用外部信号验证（测试、编译、检查、规则、审计、人工审批）
 5. Reflect（可选）：总结失败原因，调整策略
 6. Memory Update：把关键状态外置（进度、决策、产物、证据链）
 7. Repeat / Stop：满足终止条件则停止，否则继续
 
 OpenAI 在 Codex 的工程文章中直接把 “agent loop” 作为核心概念，并说明该 loop orchestrates user、model、tools 的交互直到终止状态。[2]
 
 ### 2.2 定义：Harness 与 Loop Engineering 的区别
 
 - **Harness**：模型推理与真实执行之间的“执行层与治理层”。它决定 agent 能看到什么、能做什么、如何验证、如何压缩上下文、如何审批与记录。OpenAI 将 Codex harness 分解为：核心 agent loop + thread lifecycle/persistence + config/auth + tool execution/extensions。[3]
 - **Loop Engineering**：把“对话式一次运行”提升为“系统级重复运行”。Addy Osmani 将 loop 的组成拆为 automations、worktrees、skills、connectors、sub-agents 与 external state，强调你设计的是“提示 agent 的系统”，而不再是你自己不断提示。[4]
 
 可以把二者理解为：
 
 - Harness 是单次 run 的“执行容器与治理结构”；
 - Loop Engineering 是跨 run 的“触发、续跑、分发、归档与复盘机制”。
 
 ---
 
 ## 3. 产业演进时间线（2022–2026）
 
 ### 3.1 2022–2023：ReAct 与工具调用的范式化
 
 ReAct 将推理与行动交织，证明“边想边做、边观察边修正”比纯生成更适合多步任务。[25]
 
 ### 3.2 2024：真实环境与并行编排的兴起
 
 - SWE-agent 强调 agent-computer interface 对软件任务的决定性作用：仓库导航、编辑、测试执行本身就是 loop 设计的一部分。[26]
 - LLMCompiler 代表“从串行到并行”的转向：Planner + 并行执行，将多工具调用从串行 loop 推向 DAG/并行编排。[27]
 - OSWorld 等基准把 agent 放进真实操作系统环境，暴露 GUI grounding、长轨迹执行与错误恢复的系统性难点。[20]
 
 ### 3.3 2025：平台化与协议化
 
 - OpenAI 推出构建 agents 的平台化能力（Agents SDK 与工具体系），强调编排、状态、guardrails 等系统部件。[28][29]
 - Google 推出 ADK（Agent Development Kit）并公开支持 Sequential/Parallel/Loop 的编排范式。[19][30]
 - Google 推出 A2A，作为 agent-to-agent 协作协议，把 discovery、skills、task lifecycle 等纳入规范。[18]
 - Anthropic 发布 Building effective agents，总结 workflows 与 agents 的构建模式，强调可组合、可调试的系统结构。[31]
 - Anthropic 推出 MCP，使工具/资源/提示以标准协议形式连接到模型与应用。[16]
 
 ### 3.4 2026：Harness/Loop 工程化与安全控制上移
 
 - OpenAI 发布 Codex agent loop 与 Codex harness 系列工程文章，并提出 harness engineering 的系统化工程实践。[1][2][3]
 - OpenAI 发布 Agents SDK 的“model-native harness + native sandbox execution”，并明确支持 MCP、skills、AGENTS.md、shell、apply patch 等在前沿 agent 系统中常见的 primitives。[32]
 - Microsoft 在 Agent Framework 中将 agent harness（shell、filesystem、approval flows、context compaction、memory、skills、background agents）作为生产模式内建，并在 Build 2026 强调 agent harness 与可观测、托管、治理的融合。[33][34]
 - DeepMind 发布 AI Control Roadmap，将 agent 安全定义为系统级控制问题，并提出“监控-阻断-响应”的分层策略与指标。[24]
 - Addy Osmani 提出 Loop Engineering，对上述工程趋势给出统一语言与构件分解。[4]
 
 ---
 
 ## 4. 参考架构：Agent 工程栈（从内核到生态）
 
 本节给出一个“工程栈”视角，用于统一解释 Skills、CLI、Loop、协议与治理。
 
 ### 4.1 分层架构（建议的工程视图）
 
 1. **Model layer（模型层）**：LLM 推理、函数调用、工具选择、规划能力
 2. **Tooling layer（工具层）**：shell、filesystem、browser/computer-use、search、DB、CI、ticketing
 3. **Knowledge & Skills layer（知识与技能层）**：SKILL.md、引用资料、脚本与 SOP、领域约束
 4. **Memory & State layer（记忆与状态层）**：外部状态存储（进度、证据、任务账本、工单）、可恢复 session
 5. **Harness layer（执行与治理层）**：权限、审批、沙箱、上下文压缩、审计日志、工具契约、成本预算
 6. **Orchestration layer（编排层）**：subagents/handoffs、workflow、并行、重试、错误恢复
 7. **Loop layer（循环层）**：automations、定时/事件触发、持续巡检与 triage、run-until-done
 8. **Protocol layer（互操作层）**：MCP（agent-to-tool）、A2A（agent-to-agent）
 9. **Observability & Evals（观测与评测）**：trace、回放、离线评测、线上监控、质量门禁
 10. **Security & Governance（安全与治理）**：policy、风险分级、实时阻断、合规审计、AI control
 
 OpenAI、Microsoft、Google 的官方材料都在不同层面覆盖上述结构：
 
 - OpenAI：强调 harness、sandbox、agent loop、跨 surface（CLI/App/IDE）复用。[2][3][32]
 - Microsoft：强调 harness、approval、context compaction、memory/skills、observability。[33][34]
 - Google：强调 ADK 编排、skills、长任务 pause/resume、以及 A2A/MCP 生态连接。[19][18][16]
 
 ### 4.2 为什么“可生产 Agent”必然是系统工程
 
 从 Codex 的公开工程实践看，提升可靠性的方式往往不是“让模型更努力”，而是把缺失的能力变成 **可被 agent 检查、验证、修改的系统结构**，例如把仓库知识变成系统记录、把验证与审计变成自动化产物、把架构约束变成可执行规则。[1]
 
 这也是 harness engineering 与 loop engineering 共同强调的核心：**工程师的工作从写代码迁移到设计环境、指定意图、构建反馈回路**。[1][4]
 
 ---
 
 ## 5. Skills 深度研究（标准、实现、边界、治理）
 
 ### 5.1 Skills 是什么：从“提示词文件”到“能力包”
 
 不同厂商的实现略有差异，但共同点是：
 
 - Skills 是“教 agent 怎么做”的载体（方法、流程、约束、知识入口）
 - Tools 是“让 agent 能做”的接口（执行与取数）
 - Workflows 是“控制 agent 如何编排去做”的控制流
 
 这种分工在 Microsoft 的 Plugins/Skills/Workflows 三分法中尤其明确：[35][9][36]
 
 ### 5.2 Anthropic Agent Skills：概念推动者
 
 Anthropic 将 Skills 定义为扩展 Claude 功能的模块化能力，并采用渐进披露（metadata 常驻、SKILL.md 触发加载、resources/scripts 按需读取）。[5][6]
 
 Anthropic 工程文章强调：Skills 让组织把 SOP、规则、数据处理方式、审查清单等沉淀为可复用资产，并在适当时刻注入 agent 上下文，而不是每次对话重复解释。[6]
 
 ### 5.3 开放规范 agentskills.io：最小标准化
 
 agentskills.io 提供一个最小规范：
 
 - 核心文件：`SKILL.md`（必须包含 name/description 等）
 - 可选目录：scripts/references/assets
 - 强调可移植与按需加载，避免无限膨胀的 system prompt。[7][8]
 
 ### 5.4 OpenAI Skills：平台化落地（与 Codex/Agents SDK 结合）
 
 OpenAI 官方文档将 Skills 定义为可版本化的文件 bundle，中心清单同样是 `SKILL.md`，并指出 Skills 适用于 hosted shell 与 local shell 场景。[37]
 
 在 Codex 产品体系中，Skills 与 subagents、automations、worktree 等共同构成“可持续运行的编码代理系统”。[38][39][40]
 
 在 2026-04 的 Agents SDK 演进中，OpenAI 明确把 MCP、skills、AGENTS.md 等称为“前沿 agent 系统中正在收敛的 primitives”，并把它们纳入 model-native harness 的标准集成。[32]
 
 ### 5.5 Google ADK Skills：以“上下文工程”为主轴
 
 Google 在 ADK 中定义 Skill 为自包含能力单元，封装 instructions、resources、tools，并声明基于 Agent Skills specification。[30]
 
 Google 的关键论证是：不要把所有规则塞进一个 monolithic prompt；应通过 SkillToolset 等机制实现“按需加载”，显著降低常驻 token 开销。[41][30]
 
 同时 ADK 官方文档也提示部分能力仍处于 experimental 状态（例如脚本执行支持的边界）。[30]
 
 ### 5.6 Microsoft Agent Skills：企业治理导向
 
 Microsoft Agent Framework 把 Skills 定义为可移植包（instructions, scripts, resources），并明确 progressive disclosure 的阶段（advertise、load、read resources、run scripts）。[9][42]
 
 Microsoft 的文档与博客特别强调脚本执行与高风险动作的审批与治理边界，这与其企业场景定位一致。[9][33]
 
 ### 5.7 GitHub Copilot Agent Skills：与开发流绑定
 
 GitHub 的 agent skills 文档说明 skills 是开放标准，可用于 Copilot coding agent、Copilot CLI、VS Code agent mode 等，体现“把技能作为开发流资产”的方向。[43]
 
 ### 5.8 Skills 的工程价值（可验证的收益点）
 
 - **减少重复解释**：把组织知识/规范/流程沉淀为可加载资产。[6][9]
 - **降低上下文常驻成本**：progressive disclosure 是核心机制。[5][41]
 - **提高一致性与可治理性**：可版本化、可审计、可复用。OpenAI/Microsoft 均强调不要把 skill 当成无法治理的 prompt 注入点。[37][9]
 
 ### 5.9 Skills 的风险与治理
 
 Skill 本质上是“可影响 agent 行为的指令与资源”，如果来源不可信，可能诱导越权、数据外泄或危险执行。Anthropic 与 OpenAI 都在官方文档中提示此类风险，需要审核、权限控制、审批门与最小权限原则。[5][37]
 
 ---
 
 ## 6. Agent CLI 深度研究（产品谱系、运行机制、共性原语）
 
 ### 6.1 Agent CLI 的本质：harness 的前台入口
 
 当 CLI 能做以下事情时，它就不再是“聊天工具”，而是代理运行时：
 
 - 读取/编辑文件与多文件变更
 - 执行 shell/脚本/测试
 - 连接工具生态（MCP、插件、连接器）
 - 具备审批模式与沙箱
 - 支持 subagents、自动化、续跑与隔离（worktrees）
 
 ### 6.2 Claude Code（Anthropic）：以“agentic loop”显式定义产品
 
 Claude Code 官方概览与机制文档明确描述其为 agentic coding system，并用 `gather context -> take action -> verify results` 描述 agentic loop。[10][11]
 
 Claude Code 同时提供 permission modes、subagents、agent teams、scheduled tasks 等构件，使其具备典型 loop engineering 所需的 primitives。[12][44][45][13]
 
 ### 6.3 OpenAI Codex CLI / App：跨 surface 复用同一 harness
 
 OpenAI 在 2026 的 Codex 系列工程文中明确：Codex 存在于 web app、CLI、IDE extension、桌面 app 等多种 surface，并由同一个 Codex harness（agent loop 与执行逻辑）驱动。[3]
 
 - “Unrolling the Codex agent loop” 解释了 agent loop 的循环机制与终止条件。[2]
 - “Unlocking the Codex harness” 解释了 App Server 如何暴露 harness 并实现 thread lifecycle/persistence、tool execution/extensions、config/auth 等。[3]
 - Codex 文档体系还提供 subagents、automations、skills 等能力，形成可持续运行的编码代理产品栈。[39][40][38]
 
 ### 6.4 Gemini CLI（Google）：开源 agent + ReAct loop + MCP
 
 Google Cloud 文档将 Gemini CLI 定义为 open source AI agent，并明确它实现 `Reason and Act (ReAct) loop`，可使用内置工具与本地/远程 MCP servers。[14]
 
 Gemini CLI 文档还包含 todos、headless mode、sandbox、trusted folders、hooks、skills、subagents 等，体现“CLI 即 agent 平台底座”的路线。[15]
 
 ### 6.5 GitHub Copilot CLI：GitHub-native 的开发闭环
 
 GitHub 将 Copilot CLI 定义为在终端使用 Copilot 的方式，支持与 GitHub（Issues/PR/Actions）交互。[46]
 
 其 autopilot mode 明确支持多步自主推进，并提供连续步数限制参数以控制风险与成本；delegate 则可把任务交给云端 coding agent 持续推进并以 PR 形式交付。[47][48]
 
 ### 6.6 CLI 产品之间的共性“原语”
 
 将各家实现抽象后，可以得到一组高度一致的原语（也是 loop engineering 的落点）：
 
 - Plan/Execute 模式分离（降低误操作风险）[12][47]
 - Subagents（隔离上下文、并行探索、maker/checker 分离）[12][39]
 - Automations（周期/事件唤醒，持续 triage 与跟进）[13][40][48]
 - Worktree/隔离（避免并行冲突与状态污染）[3][49]
 - Approval/Sandbox（高风险动作审批、隔离执行环境）[12][32][33]
 - Memory/State（会话外持久状态，支持续跑与恢复）[32][33]
 
 ---
 
 ## 7. Loop Engineering 与 Harness Engineering（长任务、恢复、并行与自动化）
 
 ### 7.1 Loop Engineering：由“手动驱动”到“系统驱动”
 
 Addy Osmani 的定义强调：你不再是每一步都在 prompt 的人，而是设计一个会自动发现工作、分发任务、检查结果、记录状态、决定下一步的系统。[4]
 
 其拆解的原语（automations、worktrees、skills、connectors、sub-agents、external state）与各大产品在 2026 的能力面高度对齐。[4][3][13][40][12]
 
 ### 7.2 Harness Engineering：把“缺失能力”固化为系统结构
 
 OpenAI 的 harness engineering 文章给出了非常具体的工程结论：当 Codex 失败时，修复往往不是“换 prompt”，而是问“系统缺什么能力，怎样让它对 agent 可见且可被强制执行”。[1]
 
 它还强调“repository knowledge as system of record”等实践，将规范、架构、验证与可观测固化为仓库的一部分，形成可持续改进的闭环。[1]
 
 ### 7.3 Codex agent loop：可解释的循环实现
 
 “Unrolling the Codex agent loop” 清晰描述了循环：模型要么输出最终回复，要么请求 tool call；agent 执行 tool call 并将观察结果追加进 prompt，然后再次推理，直到模型停止发出 tool call 并产生 assistant message 结束本轮 turn。[2]
 
 这份公开解释的价值在于：它把“agent 的神秘感”还原为工程机制，并指出上下文管理（如 compaction）是 harness 的职责之一。[2]
 
 ### 7.4 长任务（Long-running Agents）：外部状态与可恢复性成为刚需
 
 OpenAI 在 Agents SDK 的演进中强调“长周期任务需要 harness + sandbox”，并提出 harness 与 compute 的解耦以获得安全性、持久性与可扩展性。[32]
 
 Microsoft 在 Agent Framework 中把 context compaction、file-based memory、approval flows、background agents 等变成 harness 内建模块。[33][34]
 
 行业整体趋势是：从“把聊天历史当状态”迁移到“把状态外置”，用文件/任务板/工单/记忆存储作为系统记录。
 
 ### 7.5 并行与隔离：worktrees 的工程意义
 
 Git worktree 允许同一 repo 拥有多个 working tree，天然适合并行任务隔离（不同 HEAD/index/workdir）。[49]
 
 Codex harness 的多 surface 设计中也强调 thread lifecycle/persistence 与隔离；loop engineering 的实践中 worktree 常作为并行 agent 的冲突控制手段。[3][4][49]
 
 ### 7.6 Automations：loop 的“心跳机制”
 
 - Claude Code 提供 scheduled tasks（会话内、受限制的定时触发）。[13]
 - Codex App 提供 automations（包含 thread automations 与独立 automations 的产品化形态）。[40]
 - Copilot CLI 提供 delegate，把长任务交给云端 agent 并以 PR 形式持续推进。[48]
 
 共同点：都在把“代理持续跟进”从手工交互提升为系统级触发与归档机制。
 
 ---
 
 ## 8. 协议与平台：MCP、A2A、Agents SDK、ADK、Microsoft Agent Framework
 
 ### 8.1 MCP：agent-to-tool/context 的开放协议
 
 MCP 的核心是将外部能力以 `tools / resources / prompts` 暴露给 AI 应用，并提供统一的连接与调试方式。[16][17]
 
 MCP 本身不是编排框架，但它成为 tool/context 接入层的事实标准候选，并被多家平台在不同层次集成（如 Agents SDK、Codex harness 等）。[32][16]
 
 ### 8.2 A2A：agent-to-agent 协作协议
 
 A2A 以协议方式解决 agent discovery、能力描述（AgentSkill/Agent Card）、以及 async task lifecycle 等协作问题。[18]
 
 它与 MCP 互补：MCP 面向工具与数据源接入，A2A 面向 agent 之间协作与委托。
 
 ### 8.3 OpenAI Agents SDK：model-native harness + sandbox
 
 OpenAI Agents SDK 的核心概念是 loop，并提供工具调用、编排与运行机制；2026 的演进强调 harness 与 sandbox 的组合与分离，以及对 MCP、skills、AGENTS.md 等 primitives 的标准化支持。[28][32]
 
 ### 8.4 Google ADK：显式的 Sequential / Parallel / Loop 编排 + CLI
 
 ADK 官方 about 页强调 flexible orchestration，支持 Sequential/Parallel/Loop，并提供官方 CLI 贯穿创建、运行、部署等开发体验。[19][30]
 
 ### 8.5 Microsoft Agent Framework：企业栈的 harness + skills + workflows
 
 Microsoft Agent Framework 将 agent harness（执行、审批、上下文管理）与 skills、workflows、可观测与托管能力结合，形成企业生产模式的“全栈 agent 平台”。[33][34][9][36]
 
 ---
 
 ## 9. 评测与基准：从结果到轨迹、从短任务到长任务
 
 ### 9.1 为什么传统“答对率”不足以评价 Agent
 
 在工具与环境中运行的 agent，其失败往往不是“答案错”，而是：
 
 - 误操作（错误命令、错误文件、错误页面）
 - 漂移（目标逐步偏离、错误累积）
 - 无法恢复（卡住、重复、上下文耗尽）
 - 成本失控（无终止条件导致无限循环）
 
 因此需要基于轨迹、环境与长任务的评测框架。
 
 ### 9.2 代表性基准
 
 - OSWorld：真实操作系统任务基准，强调跨应用、GUI grounding、长轨迹执行。[20]
 - WebArena：开放网页环境任务基准，强调真实网页交互与复杂流程。[21]
 - GAIA：强调现实世界问题求解与多步推理/检索/工具使用。[22]
 - AgencyBench：长时任务与大量工具调用的评测，代表“长任务闭环评测”的方向。[23]
 
 ### 9.3 评测方法的行业方向
 
 - 从“最终答案正确”→“轨迹正确与可审计”
 - 从“单任务”→“长任务、可恢复、可持续”
 - 从“离线分数”→“线上观测、闭环优化（measure → improve → ship）”
 
 这些方向也与 harness engineering/loop engineering 的实践完全一致。[1][32][33]
 
 ---
 
 ## 10. 安全与治理：审批、沙箱、运行时控制与防御纵深
 
 ### 10.1 为什么 agent 安全是“运行时问题”
 
 当 agent 具备 shell、filesystem、browser、企业系统连接器能力时，风险不再只是内容不当，而是：
 
 - 越权访问与数据外泄
 - prompt injection 诱导危险工具调用
 - 误操作造成不可逆副作用
 - 自动化循环扩大损害规模
 
 因此需要“执行前/执行中/执行后”的系统控制。
 
 ### 10.2 产品侧治理原语：approval modes 与 sandbox
 
 - Claude Code 提供 permission modes（包括 plan-only、自动审批等不同等级）。[12]
 - OpenAI Agents SDK 强调 controlled sandbox environments，并提出 harness 与 compute 分离以增强安全与持久性。[32]
 - Microsoft Agent Framework 将 approval flows、context compaction、shell/filesystem harness、memory provider 等作为 harness 内建。[33][34]
 
 ### 10.3 DeepMind AI Control Roadmap：把 agent 当作 insider threat
 
 DeepMind 提出 defense-in-depth，假设 agent 可能不对齐或不可完全信任；用监督系统监控推理/行动/计划，按风险分级采取异步审查或实时阻断，并用 coverage、recall、time-to-response 衡量控制系统有效性。[24]
 
 这为企业级 agent 系统提出一个明确方向：**安全控制必须像传统网络安全一样成为基础设施**。
 
 ---
 
 ## 11. 典型场景与案例
 
 ### 11.1 Research Agents：长时检索、证据链与异步执行
 
 - OpenAI deep research：产品化研究型 agent，强调多步检索、综合与长时执行。[50]
 - Google Deep Research Max：强调 extended test-time compute、MCP 接入私有数据、协作式研究计划、长时异步工作流。[51][52]
 
 研究 agent 的共同模式：检索→阅读→综合→引用→缺证提示→再检索/反证→输出。其工程关键是证据链与可控的研究计划，而非“写得像”。[51][50]
 
 ### 11.2 Coding Agents：验证门禁与产物可追溯
 
 - Claude Code：以 agentic loop 定义编码代理系统，并提供 subagents、scheduled tasks、permission modes。[10][11][12][13]
 - Codex：用公开的 agent loop 与 harness 架构把编码代理系统化，强调 thread persistence、工具执行、跨 surface 复用。[2][3][1]
 
 ### 11.3 Browser / Computer Use：结构化工具优先、敏感动作审批
 
 浏览器/桌面环境的非确定性与高风险，使得审批门、隔离执行与回放审计成为硬要求。Anthropic 的 Computer Use 与相关文档体系强调此类风险边界与治理思路。[53]
 
 ### 11.4 企业平台：从原型到生产的“周边系统”
 
 Microsoft Foundry/Agent Framework 在 Build 2026 的材料强调：原型容易，生产难点在 isolation、durable state、runtime、observability、evaluation、distribution 与 governance。[34][33]
 
 这与 harness engineering 的工程观察高度一致：真正的工作在“系统周边”，而不是“模型调用”。[1]
 
 ---
 
 ## 12. 趋势展望与建议（未来 12–24 个月）
 
 ### 12.1 技术趋势（高确定性）
 
 1. **Skills 资产化**：企业会像管理代码与 API 一样管理 skills（SOP、审查清单、运维 runbook、合规策略）。[6][9][7]
 2. **Harness 产品化**：harness 将成为平台竞争核心：安全、持久、可恢复、可观测、可评测。[1][32][33]
 3. **协议栈收敛**：MCP + A2A 分别覆盖工具与协作互操作，生态会进一步围绕它们组合演进。[16][18]
 4. **评测成为开发闭环**：agent 的“可上线性”取决于 eval 与观测基础设施，而非 demo 成功率。[23][33][32]
 5. **运行时安全基础设施化**：AI control 思路会进入企业采购与内控要求，尤其是高权限 agent。[24]
 
 ### 12.2 组织建议（偏工程治理而非实现）
 
 - 把 Agent 项目拆成“可验证闭环”：先定义终止条件与验证门禁，再谈自动化与多代理。
 - 把外部状态当作系统记录：进度、证据、决策、任务账本必须可审计、可恢复、可继承。
 - 把 Skills 当作组织知识库的第一等形态：建立审核、版本、权限与分发机制。
 - 把高风险工具调用纳入审批与权限分级：默认最小权限、默认可回滚、默认可阻断。
 - 先构建观测与评测，再追求更高自治：没有 trace/evals 的自治会放大风险与成本。
 
 ---
 
 # A. 术语表（Glossary）
 
 - Agent Loop：模型与工具在环境反馈下反复迭代的执行闭环。[2]
 - Harness：连接推理与执行的系统层，包含权限、工具、上下文管理、持久化、审批与治理。[3][32]
 - Loop Engineering：把人手动 prompt 替换为系统驱动的周期/事件唤醒与闭环运行。[4]
 - Skills：可复用、可移植、按需加载的能力包（方法、SOP、资源入口、可选脚本）。[5][7][9]
 - MCP：模型连接工具与数据的开放协议（tools/resources/prompts）。[16]
 - A2A：agent-to-agent 协作协议（discovery、skills、task lifecycle）。[18]
 - Subagents：在独立上下文/权限边界下处理子任务的专门代理。[12][39]
 - Worktree：Git 的多工作区能力，用于并行隔离与避免冲突。[49]
 
 ---
 
 # B. 参考文献（References）
 
 > 引用格式：正文使用 [n] 标号；此处给出权威链接与标题。日期以页面公开日期为准（如页面显示）。
 
 [1] OpenAI. *Harness engineering: leveraging Codex in an agent-first world*. 2026-02-11. https://openai.com/index/harness-engineering/
 
 [2] OpenAI. *Unrolling the Codex agent loop*. 2026-01-23. https://openai.com/index/unrolling-the-codex-agent-loop/
 
 [3] OpenAI. *Unlocking the Codex harness: how we built the App Server*. 2026-02-04. https://openai.com/index/unlocking-the-codex-harness/
 
 [4] Addy Osmani. *Loop Engineering*. 2026-06-07. https://addyosmani.com/blog/loop-engineering/
 
 [5] Anthropic. *Agent Skills overview (Agents and tools docs)*. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
 
 [6] Anthropic. *Equipping agents for the real world with Agent Skills*. https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
 
 [7] AgentSkills.io. *Home / Overview*. https://agentskills.io/home
 
 [8] AgentSkills.io. *Specification*. https://agentskills.io/specification
 
 [9] Microsoft Learn. *Agent Skills (Microsoft Agent Framework)*. https://learn.microsoft.com/en-us/agent-framework/agents/skills
 
 [10] Anthropic. *Claude Code Overview*. https://code.claude.com/docs/en/overview
 
 [11] Anthropic. *How Claude Code works*. https://code.claude.com/docs/en/how-claude-code-works
 
 [12] Anthropic. *Claude Code Permission modes*. https://code.claude.com/docs/en/permission-modes
 
 [13] Anthropic. *Claude Code Scheduled Tasks*. https://code.claude.com/docs/en/scheduled-tasks
 
 [14] Google Cloud Docs. *Gemini CLI*. https://docs.cloud.google.com/gemini/docs/codeassist/gemini-cli
 
 [15] Gemini CLI Docs. *Documentation*. https://geminicli.com/docs/
 
 [16] Model Context Protocol. *Introduction / Getting started*. https://modelcontextprotocol.io/docs/getting-started/intro
 
 [17] Model Context Protocol. *Architecture*. https://modelcontextprotocol.io/docs/learn/architecture
 
 [18] A2A Protocol. *Specification*. https://a2a-protocol.org/latest/specification/
 
 [19] Google ADK Docs. *About / Get started*. https://google.github.io/adk-docs/get-started/about/
 
 [20] OSWorld paper (arXiv). *OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments*. https://arxiv.org/abs/2404.07972
 
 [21] WebArena paper (arXiv). *WebArena: A Realistic Web Environment for Building Autonomous Agents*. https://arxiv.org/abs/2307.13854
 
 [22] GAIA paper (arXiv). *GAIA: a benchmark for General AI Assistants*. https://arxiv.org/abs/2311.12983
 
 [23] AgencyBench paper (arXiv). https://arxiv.org/abs/2601.11044
 
 [24] Google DeepMind. *Securing the future of AI agents (AI Control Roadmap)*. 2026-06-18. https://deepmind.google/blog/securing-the-future-of-ai-agents/
 
 [25] ReAct paper (arXiv). *ReAct: Synergizing Reasoning and Acting in Language Models*. https://arxiv.org/abs/2210.03629
 
 [26] SWE-agent paper (arXiv). https://arxiv.org/abs/2405.15793
 
 [27] LLMCompiler paper (arXiv). https://arxiv.org/abs/2312.04511
 
 [28] OpenAI Docs. *Agents SDK guide*. https://developers.openai.com/api/docs/guides/agents
 
 [29] OpenAI. *New tools for building agents*. 2025. https://openai.com/index/new-tools-for-building-agents/
 
 [30] Google ADK Docs. *Skills*. https://google.github.io/adk-docs/skills/
 
 [31] Anthropic. *Building effective agents*. 2024. https://www.anthropic.com/research/building-effective-agents
 
 [32] OpenAI. *The next evolution of the Agents SDK*. 2026-04-15. https://openai.com/index/the-next-evolution-of-the-agents-sdk/
 
 [33] Microsoft DevBlogs. *Agent harness in Agent Framework*. 2026. https://devblogs.microsoft.com/agent-framework/agent-harness-in-agent-framework/
 
 [34] Microsoft DevBlogs. *Microsoft Agent Framework at BUILD 2026: Agent Harness, Hosted Agents, CodeAct, and more*. 2026-06-03. https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/
 
 [35] Microsoft Learn. *Semantic Kernel Plugins*. https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/
 
 [36] Microsoft Learn. *Workflows (Microsoft Agent Framework)*. https://learn.microsoft.com/en-us/agent-framework/workflows/
 
 [37] OpenAI Docs. *Skills (Tools – Skills)*. https://developers.openai.com/api/docs/guides/tools-skills
 
 [38] OpenAI Codex Docs. *Codex Skills*. https://developers.openai.com/codex/skills
 
 [39] OpenAI Codex Docs. *Subagents*. https://developers.openai.com/codex/subagents
 
 [40] OpenAI Codex Docs. *Automations*. https://developers.openai.com/codex/app/automations
 
 [41] Google Developers Blog. *Developer’s Guide to Building ADK Agents with Skills*. https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/
 
 [42] Microsoft DevBlogs. *Give your agents domain expertise with Agent Skills in Microsoft Agent Framework*. https://devblogs.microsoft.com/agent-framework/give-your-agents-domain-expertise-with-agent-skills-in-microsoft-agent-framework/
 
 [43] GitHub Docs. *About agent skills*. https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
 
 [44] Anthropic. *Claude Code Subagents*. https://code.claude.com/docs/en/sub-agents
 
 [45] Anthropic. *Claude Code Agent Teams*. https://code.claude.com/docs/en/agent-teams
 
 [46] GitHub Docs. *About Copilot CLI*. https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-copilot-cli
 
 [47] GitHub Docs. *Copilot CLI Autopilot*. https://docs.github.com/en/copilot/concepts/agents/copilot-cli/autopilot
 
 [48] GitHub Docs. *Delegate tasks to the cloud agent*. https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/delegate-tasks-to-cca
 
 [49] Git SCM. *git-worktree*. https://git-scm.com/docs/git-worktree
 
 [50] OpenAI. *Introducing deep research*. 2025. https://openai.com/index/introducing-deep-research/
 
 [51] Google Blog. *Deep Research Max: a step change for autonomous research agents*. 2026-04-21. https://blog.google/innovation-and-ai/models-and-research/gemini-models/next-generation-gemini-deep-research/
 
 [52] Google Developers. *Gemini Deep Research Agent docs*. https://ai.google.dev/gemini-api/docs/deep-research
 
 [53] Anthropic Docs. *Computer Use tool*. https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool

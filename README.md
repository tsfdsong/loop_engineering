# LoopEngine — 循环工程全家桶

> **loop** 闭环编码 + **go** 全自动编排 + **orch** 多技能编排（v1.0 单职责化），一站式 AI 编程引擎插件。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.3.1-blue)](package.json)
[![orch](https://img.shields.io/badge/orch-v2.0.0-blue)](skills/orch/SKILL.md)
[![specs](https://img.shields.io/badge/specs-external-blue)](docs/spec-repo-link.md)

## 设计文档

所有 spec / plan / ADR 已外部化到独立仓库：[`loop_engineering_specs`](https://github.com/tsfdsong/loop_engineering_specs)

主仓 `install.sh` 默认自动 clone 到 `~/.loopengine/specs/`。可使用 `--skip-specs` 跳过。详见 [`docs/spec-repo-link.md`](docs/spec-repo-link.md)。

---

## 🚀 一键安装/更新（v1.2.0 起 install.sh 智能模式合一）

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

**v1.2.0 起** install.sh = install + update 智能合一：
- 未装 → 首次安装
- 已装旧版 → 升级
- 已装同版 → 5 秒等待（`--force` 跳过，`--dry-run` 只检查不安装）

**v1.3.0+** 自动检测已安装的 AI 编程工具（ZCode / Claude Code / Codex / Gemini CLI / GitHub Copilot / Cursor / Pi）并执行对应安装/更新；Kimi / OpenCode 走各自平台原生命令手动安装（`/plugins install` / 修改 `opencode.json`）。

---

## 🔴 MCP 红线规则（v1.0.1 新增）

> **任何需要理解代码结构的操作，必须先用 MCP 工具，禁止直接 Read 全文件。** 实测可节省 ~90% token。

| 规则 | 内容 |
|------|------|
| **适用范围** | 修改代码、调研代码、解释代码、分析架构、查找定义/引用 |
| **标准流程** | `get_repo_map` → `get_file_outline` → `search_symbols` → `Read`（仅精确行） |
| **唯一例外** | MCP 全部不可用、文件 < 50 行、需精确行内容 |
| **违规判定** | 连续 3 次直接 Read 全文件未用 MCP = 红线事故 |

此规则已写入所有层级：用户级 `~/.zcode/AGENTS.md`、项目级 `AGENTS.md`、orch、go、loop 技能。

### 🔌 MCP 三件套（节省 80% token）

LoopEngine 依赖三个 MCP 工具：

| 工具 | 类型 | 核心能力 | Token 节省 |
|------|------|---------|:---:|
| **jCodeMunch-MCP** | Python | AST 符号级代码检索 | **95%** |
| **Repomix** | Node.js | 代码库打包 + 结构压缩 | **70%** |
| **Headroom-ai** | Python | 上下文压缩层 | **60-95%** |

**安装**（install.sh 已自动完成）：
```bash
pip install --upgrade jcodemunch-mcp headroom-ai
npm install -g repomix
```

**首次使用**（索引项目）：
```bash
jcodemunch-mcp index_folder .
```

**典型场景 token 对比**：

| 场景 | ZCode 自带工具 | MCP 三件套 | 节省 |
|------|----------|--------|:---:|
| 阅读单个函数（300 行） | ~800 token | ~40 token | **95%** |
| 理解项目架构 | ~1,200,000 token | ~370,000 token | **69%** |
| 长会话（50 轮） | ~40,000 token | ~12,000 token | **70%** |
| **典型场景平均** | — | — | **~80%** |

详细配置见 [`docs/mcp-setup-guide.md`](docs/mcp-setup-guide.md)。

---

## 📦 各平台安装命令

| 平台 | 安装命令 | 验证 |
|------|---------|:--:|
| **ZCode** | `curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh \| bash`（推荐一键脚本，自动同步到 `~/.agents/skills/` 优先路径） | ✅ 实机 |
| **Claude Code** | `claude plugin marketplace add https://github.com/tsfdsong/loop_engineering` 然后 `claude plugin install loopengine` | ✅ 实机 |
| **Codex** | 插件市场搜索 `loopengine` | ⏳ |
| **Cursor** | `/add-plugin tsfdsong/loop_engineering`（install.sh 已自动部署 skills+hooks+mcp.json） | ⏳ 应用内 |
| **Gemini CLI** | `gemini extensions install https://github.com/tsfdsong/loop_engineering` | ⏳ |
| **Copilot CLI** | `copilot plugin install loopengine@tsfdsong` | ⏳ |
| **Pi** | `pi install git:https://github.com/tsfdsong/loop_engineering` | ⏳ |

---

## 🧠 三大核心

```
┌───────────────────────────────────────────────────┐
│                     orch                          │
│         多技能编排器 · 显式 /orch 触发              │
│   单技能(80%)走原生 · 多技能(20%)自动识别编排       │
└──────────┬──────────────────────┬─────────────────┘
           │                      │
           ▼                      ▼
┌───────────────────┐   ┌──────────────────────────┐
│      loop         │   │          go              │
│   🔄 闭环编码      │   │   🚀 全自动编排           │
│                   │   │                          │
│  需求 → 计划 →    │   │  拆分子任务 → 并发执行    │
│  编码 → 门禁 →    │   │  → 检查 → 复盘 → 交付     │
│  自愈 → 交付      │   │                          │
│                   │   │                          │
│  /loop 功能 条件   │   │  /go 功能描述             │
└───────────────────┘   └──────────────────────────┘
```

### `/loop` — 闭环编码
```
/loop 实现用户登录，支持邮箱+密码，错误3次锁定30分钟
```
自动走完：需求分析 → 计划拆分 → Git 隔离 → 编码 → 门禁检查 → 自愈修复 → 验证交付。未达验收标准自动迭代，无需人工推动。

### `/go` — 全自动编排
```
/go 开发一个博客系统，含文章管理、评论、分类标签
```
自动：递归拆解任务 → 并发调度 ZCode → 闭环执行每个子任务 → 汇总 → 交付。复杂工程一键完成。

### `orch` — 多技能编排器（自然语言优先）

**单技能任务（80%）**：原生 description 匹配自动处理，无需 `/orch`。  
**多技能任务（20%）**：系统先自动判断是否需要 orch；`/orch` 仅保留为显式强制入口。

| 你说 | 系统行为 |
|------|---------|
| "这个类太大了" | 单技能 → `refactoring` |
| "报错了帮我看看" | 单技能 → `systematic-debugging` |
| "帮我全面审查这个项目并给计划" | 自动识别 `review` family，多技能串行编排 |
| "帮我自动化测试这个网站" | 自动识别 `web_qa` family，并行测试矩阵 |
| "帮我排查并修复这个错误" | 自动识别 `debug_fix` family，修复节点委托 `loop` |

#### v2.0 核心特征

- **自然语言优先**：用户直接说目标，不学编号
- **family-first**：先识别场景家族，再抽取动作
- **rule-first**：规则表决定 DAG，不让 LLM 自由画图
- **side-effect-first**：只读节点直调技能；写入节点委托 `loop` / `go`
- **单 family v1**：第一版不自动跨 family 混编

**v1.0 单职责化**：orch 仅做编排，不维护关键词表 / 冲突裁决 / P0 纪律 / 复杂度评分——这些由 AGENTS.md 或原生 description 匹配承担。详细规范见 [`skills/orch/SKILL.md`](skills/orch/SKILL.md)。

---

## 📚 技能分类（33个内置 · v6.4 真正融合后）

| 分类 | 数量 | 典型技能 |
|------|------|---------|
| 📝 代码质量 | 3 | `clean-code`（**合并**: clean-code + code-complete + code-quality-principles） |
| 🏗️ 架构设计 | 4 | `clean-architecture` `domain-driven-design`（**合并**: + ddd-distilled + ddd-tactical-patterns + implementing-ddd） |
| 🔧 重构 | 3 | `refactoring`（**合并**: + refactoring-guru） `legacy-code` |
| 🧪 测试 | 3 | `test-driven-development` `testing-patterns` `e2e-testing-patterns` |
| 🐛 调试 | 1 | `systematic-debugging` |
| 🔌 API/安全 | 4 | `api-design-principles` `api-security-best-practices` `auth-implementation-patterns` |
| 🔍 代码审查 | 1 | `code-reviewer`（**合并**: + requesting-code-review + receiving-code-review） |
| ✅ 验证 | 1 | `verification-before-completion` |
| 🚀 工程流程 | 7 | `github-actions-templates` `using-git-worktrees` `release-it` |
| 📋 规划执行 | 5 | `brainstorming` `writing-plans` `executing-plans` `subagent-driven-development` |
| 📋 产品管理 | 2 | `product-manager` `to-prd` |
| 🛠️ 技能管理 | 3 | `writing-skills` `skill-creator¹` `agent-skill-architecture` |
| 🗄️ 数据库 | 1 | `database-design` |
| 🛠️ 工具 | 3 | `drawio-skill` `agent-browser` `using-loopengine` |
| 🧭 路由 | 2 | `loop` `loop-library` |
| 🔍 审查 | 2 | `system-review` `code-reviewer`¹⁾ |

> ¹ 跨插件引用：`skill-creator` 由 ZCode 官方 `skill-creator` 插件提供。  
> ² `code-reviewer` 同时在"代码审查"和"审查"两个分类中。  
> ❌ **已剥离**：`find-skills`（元技能，与开发流程无关）、`code-documentation-doc-generate` / `api-documentation-generator`（文档生成，与开发流程非直接相关）、`docx` / `pdf`（文档处理，与开发流程无关）。

---

## ✅ 验证安装

打开新的 AI 会话，发送以下任一命令：

```
/loop 帮我写一个 Hello World
```

```
告诉我 LoopEngine 能做什么
```

如果代理自动加载了对应技能，说明安装成功。

---

## 🏗️ 项目结构

```
loopengine/
├── skills/                  # 33 个内置技能定义（v6.4 真正融合后 · SKILL.md + references）
│   ├── loop/                # 闭环编码引擎
│   ├── go/                  # 全自动编排引擎（v4.0 ZCode 纯血 + Worktree 并发）
│   │   └── scripts/         # Python 编排脚本（orchestrator/zcode_runner/git_ops/state_manager）
│   ├── orch/               # 多技能编排器（v1.0 单职责化 · 会话启动注入）
│   └── ...                  # 其余 32 个技能
├── hooks/                   # 会话启动钩子
│   ├── session-start        # 启动引导脚本（注入 orch）
│   ├── run-hook.cmd         # 跨平台 polyglot 包装器
│   └── hooks*.json          # 各平台钩子配置
├── docs/                    # 文档
│   ├── INSTALL.md           # 安装指南（v1.3.1）
│   ├── mcp-setup-guide.md   # MCP 三件套安装配置
│   ├── lessons-learned.md   # 事故教训库（单一真源）
│   └── loopengineering-design/  # 架构设计图
├── scripts/                 # 平台工具脚本
│   ├── install/             # 跨平台 install 子脚本（v1.3.1 三平台合一）
│   ├── render_plugins.py    # plugin manifest 渲染
│   ├── inject_rules.py      # 7 红线 sentinel 注入
│   └── merge_mcp_config.py  # ZCode + Cursor MCP 合并（v1.3.1）
├── install.sh               # 一键安装 + 智能更新（v1.2.0 起合一，v1.3.0 自动感知）
├── .zcode-plugin/           # ZCode 插件清单
├── .claude-plugin/          # Claude Code 插件清单
├── .codex-plugin/           # Codex 插件清单
├── .cursor-plugin/          # Cursor 插件清单
├── .kimi-plugin/            # Kimi Code 插件清单（手动 `/plugins install` 部署）
├── .opencode/               # OpenCode 插件（手动修改 opencode.json 部署）
├── .pi/                     # Pi 运行时扩展
├── package.json             # npm 包元数据 + Pi 配置
├── gemini-extension.json    # Gemini CLI 扩展清单
├── AGENTS.md / CLAUDE.md    # 代理引导文件（含 7 条红线）
└── GEMINI.md                # Gemini 启动上下文
```

---

## 🔧 原理

LoopEngine 采用与 [Superpowers](https://github.com/obra/Superpowers) 相同的插件架构：

1. **会话启动钩子** → `hooks/session-start` 脚本在 AI 会话启动时触发
2. **启动引导注入** → 将 `orch/SKILL.md` 注入到会话上下文
3. **单技能走原生** → 80% 任务由 LLM 通过 description 语义匹配自动选择技能，无需 `/orch`
4. **多技能走 orch** → 20% 复合任务由系统自动识别场景家族编排（`/orch` 仅作显式强制入口，不再用编号）
5. **🔴 MCP 红线** → 所有理解代码的操作必须先用 MCP 工具（`get_repo_map` → `get_file_outline` → `search_symbols`），禁止直接 Read 全文件，省 ~90% token

### 🔴 7 条全局红线（Step 5 · v1.0.2+ · v1.2.2 同步到全部 7 条）

`install.sh` Step 5 自动把 AGENTS.md 中的 **7 条红线**（用户交互 / MCP / 事实优先 / 摘要输出 / 完成前验证 / 进度汇报 / Subagent 边界）注入到 **7 个 AI 工具的用户级**规则文件，确保全局生效：

| AI 工具 | 注入路径 |
|---|---|
| ZCode | `~/.zcode/AGENTS.md` |
| Claude Code | `~/.claude/CLAUDE.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` |
| Codex | `~/.codex/AGENTS.md` |
| Cursor | `~/.cursor/rules/loopengine-interaction.mdc` |
| Copilot CLI | `~/.copilot/AGENTS.md` |
| Pi | `~/.pi/AGENTS.md` |

**关键设计**：
- **sentinel markers**（`<!-- BEGIN/END LOOPENGINE-MANAGED INTERACTION-RULES -->`）—— 幂等更新，重复运行不重复插入
- **用户保留** —— 你在文件其他位置的自定义内容**不会被覆盖**
- **自动同步** —— 重跑 `install.sh` 时规则自动更新（智能模式）

详见 [`scripts/install/_common.sh` 的 `common_inject_red_lines`](scripts/install/_common.sh) 函数（v1.0.2+ 统一调度 7 条红线）。

### 更新链路

```
源仓库 (GitHub) git pull → 内置包目录 → xcopy 同步 CLI 缓存 → 重启 ZCode → SessionStart hook 注入 → 新会话生效
```

已安装用户执行 `curl .../install.sh | bash` 即可一键同步所有变更（v1.2.0 智能模式）。

---

## 📄 许可

MIT © tsfdsong

# LoopEngine — 循环工程全家桶

> **v2.0**（2026-07-18）：**go** 全自动编排（含 family 识别 · orch 已合并）+ **loop** 闭环编码（门禁按 L 分级）+ **supervisor** 监控看门狗 + **32 skills + 12 红线**（5 Core Instincts + 7 Verbal）+ 工具/模型双无关化。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](AGENTS.md)
[![skills](https://img.shields.io/badge/skills-32-green)](skills/)
[![redlines](https://img.shields.io/badge/redlines-12-red)](AGENTS.md)

---

## 🚀 一键安装/更新（v1.2.0 起 install.sh 智能模式合一 · v1.3.2 新增 PowerShell）

### macOS / Linux / Windows Git Bash

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

### Windows PowerShell（v1.3.2 新增 · 纯 PS，无需 Git Bash）

```powershell
# PowerShell 5.1 需先强制 TLS 1.2（GitHub raw 要求），PowerShell 7+ 可省略此行
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# 单模式：每次都强制覆盖所有文件
# 注意：文件名带时间戳避免 PS 5.1 irm -OutFile 不覆盖同名文件陷阱
$le = "$env:TEMP\le-install-$([DateTime]::UtcNow.Ticks).ps1"
irm https://github.com/tsfdsong/loop_engineering/raw/main/install.ps1 -OutFile $le
& $le
Remove-Item $le -Force
```

> **为什么不用 `irm | iex`？** PS 5.1 下 `irm` 下载的 UTF-8 BOM 字符 + `iex` 把脚本当表达式执行，会报"无法将 ?# 项识别为 cmdlet"。临时文件模式绕过此限制。详细排查见 `docs/INSTALL.md` 故障排查表。

**v1.2.0 起** install.sh = install + update 智能合一：
- 未装 → 首次安装
- 已装旧版 → 升级
- 已装同版 → 5 秒等待（`--force` 跳过，`--dry-run` 只检查不安装）

**v1.3.0+** 自动检测已安装的 AI 编程工具（ZCode / Claude Code / Codex / Gemini CLI / GitHub Copilot / Cursor / Pi）并执行对应安装/更新；Kimi / OpenCode 走各自平台原生命令手动安装（`/plugins install` / 修改 `opencode.json`）。

**v1.3.2** 新增 `install.ps1`（PowerShell 兄弟脚本），与 `install.sh` 行为契约一致，共用 3 个 Python helper（`render_plugins.py` / `inject_rules.py` / `merge_mcp_config.py`）。两个脚本并存，按平台选用：macOS/Linux 用 `.sh`，Windows 纯 PowerShell 用 `.ps1`。

---

## 🔴 MCP 红线规则（v6.11 场景感知）

> **任何需要理解代码结构的操作，必须先用 MCP 工具，禁止直接 Read 全文件。** 实测可节省 ~90% token。

v1.0.2 起从"绝对 MCP 优先"升级为 **6 场景分层**（S1-S6）：

| 场景 | 工作场景 | 推荐工具 | 必须性 |
|------|---------|---------|--------|
| **S1** | 接入新代码库 | `get_repo_map` → `get_file_outline` | **必须** |
| **S2** | 探索大文件（>500 行） | `get_file_outline` + `search_symbols` | 建议 |
| **S3** | 修改已知位置 | `Read` (offset/limit) 或 `get_symbol_source` | 直接合规 |
| **S4** | 跨文件搜索引用 | `check_references` / `find_importers` | 建议 |
| **S5** | 跨文件关键字搜索 | `search_text` / `search_ast` | 替代 grep |
| **S6** | MCP 失败 fallback | `repomix.pack_codebase` → `Read` | 必须 fallback |

此规则已写入所有层级：用户级 `~/.zcode/AGENTS.md`、项目级 `AGENTS.md`、go、loop 技能。

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
| **所有平台** | `curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh \| bash`（推荐 · 自动检测已装工具） | ✅ 实机 |
| **Windows PowerShell** | `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $le="$env:TEMP\le-install-$([DateTime]::UtcNow.Ticks).ps1"; irm https://github.com/tsfdsong/loop_engineering/raw/main/install.ps1 -OutFile $le; & $le; Remove-Item $le -Force` | ✅ 实机 |
| **ZCode** | install.sh 自动注册到 local marketplace + 激活 enabledPlugins（v1.4 activate 回调） | ✅ 实机 |
| **Claude Code** | install.sh 渲染 plugin.json + marketplace.json；也支持 `/plugin install loopengine@tsfdsong` | ✅ 实机 |
| **Cursor** | install.sh 自动部署 skills（扁平平铺）+ .mdc rules（含 alwaysApply frontmatter） | ✅ 实机 |
| **Codex** | install.sh 部署 .codex-plugin/plugin.json + hooks-codex.json | ✅ |
| **Gemini CLI** | install.sh 部署 gemini-extension.json | ✅ |
| **Copilot CLI** | install.sh 注入 AGENTS.md 红线（不走 manifest） | ✅ |
| **Pi** | install.sh 部署 .pi/extensions/ + AGENTS.md 红线 | ✅ |

---

## 🧠 核心架构（v2.0）

```
┌───────────────────────────────────────────────────┐
│                      go                           │
│  🚀 全自动编排 · family-first · worktree 并发      │
│  （含原 orch 的 8 场景家族识别 + DAG 组装）         │
└──────────┬──────────────────────┬─────────────────┘
           │                      │
           ▼                      ▼
┌───────────────────┐   ┌──────────────────────────┐
│      loop         │   │      supervisor          │
│   🔄 闭环编码      │   │   👁 并发子任务监控       │
│  单任务门禁+自愈   │   │  R1-R4 干预链             │
└───────────────────┘   └──────────────────────────┘
```

### `/loop` — 闭环编码
```
/loop 实现用户登录，支持邮箱+密码，错误3次锁定30分钟
```
自动走完：需求分析 → 计划拆分 → Git 隔离 → 编码 → 门禁检查 → 自愈修复 → 验证交付。未达验收标准自动迭代，无需人工推动。

### `/go` — 全自动编排（含 family 路由）
```
/go 开发一个博客系统，含文章管理、评论、分类标签
```
自动：意图识别（8 family）→ 6 维需求分析 → 拆分子任务 → worktree 并发 → 回归 → 系统审查 → 交付。

> **v2.0**：原独立 `orch` 技能已合并进 go Step 0。`/orch` 保留为兼容别名，行为委托 `/go`。

#### family 路由示例（由 go 承担）

| 你说 | 系统行为 |
|------|---------|
| "这个类太大了" | 单技能 → `refactoring` |
| "报错了帮我看看" | 单技能 → `systematic-debugging` |
| "帮我全面审查这个项目并给计划" | `review` family，多技能串行编排 |
| "帮我自动化测试这个网站" | `web_qa` family，并行测试矩阵 |
| "帮我排查并修复这个错误" | `debug_fix` family，修复节点委托 `loop` |

#### v2.0 核心特征

- **family-first**：先识别场景家族（8 类），再抽取 actions
- **rule-first**：规则表决定 DAG（见 `skills/go/references/dag-rules.yaml`）
- **side-effect-first**：只读节点直调技能；写入节点委托 `loop` / `go`
- **单 family 默认**：跨 family 组合见 `family-routing.md` 白名单

详细规范见 [`skills/go/SKILL.md`](skills/go/SKILL.md) 与 [`skills/go/references/family-routing.md`](skills/go/references/family-routing.md)。

---

## 📚 技能分类（32 个内置 · v2.0）

| 分类 | 典型技能 |
|------|---------|
| 自研闭环 | `loop`, `go`, `supervisor`, `using-loopengine` |
| 代码质量 | `clean-code`, `code-reviewer`, `refactoring` |
| 架构/审查 | `software-architecture`, `system-review`, `evidence-first` |
| 测试/调试 | `testing`, `systematic-debugging`, `web-quality` |
| 工程流程 | `using-git-worktrees`, `subagent-driven-development`, `verification-officer` |
| 规划/产品 | `brainstorming`, `spec-driven-development`, `product-manager` |
| 工具 | `drawio-skill`, `agent-browser`, `ui-design-system` |

> 完整列表见 `skills/` 目录（32 个 SKILL.md）。`web-quality` 子能力见 `skills/web-quality/references/`。

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
├── skills/                  # 32 个内置技能定义（SKILL.md + references）
│   ├── loop/                # 闭环编码引擎
│   ├── go/                  # 全自动编排引擎（含 family 路由 · worktree 并发）
│   │   ├── references/      # family/DAG 契约（自 orch v2 迁移）
│   │   └── scripts/         # Python 编排脚本（orchestrator/zcode_runner/git_ops/state_manager）
│   ├── supervisor/          # 并发子任务监控
│   └── ...                  # 其余技能
├── commands/                # Slash commands（plugin 包组件）
│   ├── audit.md             # /audit 6 维度部署审计
│   ├── orch.md              # /orch 兼容别名（委托 /go）
│   ├── loop.md              # /loop 闭环编码
│   └── go.md                # /go 工程化执行
├── hooks/                   # 会话启动钩子
│   ├── session-start        # 启动引导脚本（注入 go runtime bundle）
│   ├── run-hook.cmd         # 跨平台 polyglot 包装器
│   └── hooks*.json          # 各平台钩子配置
├── docs/                    # 文档
│   ├── INSTALL.md           # 安装指南（含 PowerShell）
│   ├── mcp-setup-guide.md   # MCP 三件套安装配置
│   ├── lessons-learned.md   # 事故教训库（单一真源）
│   └── superpowers/         # 设计文档 + specs + plans
├── scripts/                 # 平台工具脚本
│   ├── install/             # 跨平台 install 子脚本（_common.sh 三平台合一）
│   ├── render_plugins.py    # plugin manifest 渲染（v1.4 ToolAdapter 注册表）
│   ├── audit_tools.py       # 6 维度部署审计（v1.4 新增）
│   ├── inject_rules.py      # 红线 sentinel 注入（2 H2 块 · 承载 12 条规则）
│   ├── merge_mcp_config.py  # ZCode + Cursor MCP 合并
│   ├── register_zcode_*.py  # ZCode plugin 激活（marketplace + enabledPlugins）
│   └── render_plugins.py    # ToolAdapter 注册表 + activate 回调
├── tests/                   # 单元测试（unittest · 126 tests）
├── install.sh               # 一键安装 + 智能更新（macOS/Linux/Git Bash）
├── install.ps1              # Windows PowerShell 一键安装（纯 PS 无需 Git Bash）
├── .plugin-template.json    # plugin manifest 模板（单一真源 · version + commands 字段）
├── .zcode-plugin/           # ZCode 插件清单 overlay
├── .claude-plugin/          # Claude Code 插件清单 overlay + marketplace.json
├── .codex-plugin/           # Codex 插件清单 overlay
├── .cursor-plugin/          # Cursor 插件清单 overlay
├── .kimi-plugin/            # Kimi Code 插件清单 overlay（手动 `/plugins install` 部署）
├── .pi/                     # Pi 运行时扩展
├── package.json             # npm 包元数据 + Pi 配置
├── gemini-extension.json    # Gemini CLI 扩展清单
├── AGENTS.md / CLAUDE.md    # 代理引导文件（含 12 条红线 · 5 Core + 7 Verbal）
└── GEMINI.md                # Gemini 启动上下文（@skills/go/SKILL.md）
```

---

## 🔧 原理

LoopEngine 采用与 [Superpowers](https://github.com/obra/Superpowers) 相同的插件架构：

1. **plugin 包** → skills + hooks + commands + mcpServers + plugin.json 五大组件打包
2. **TOOL_ADAPTERS 注册表**（v1.4）→ `render_plugins.py` 用 ToolAdapter dataclass 集中管理各工具的 manifest 渲染策略 + 激活回调
3. **会话启动钩子** → `hooks/session-start` 脚本在 AI 会话启动时触发
4. **启动引导注入** → 将 `go/SKILL.md` + family/DAG references 注入到会话上下文
5. **单技能走原生** → 80% 任务由 LLM 通过 description 语义匹配自动选择技能
6. **多步/跨模块走 /go** → family-first 识别 + worktree 并发编排
7. **🔴 MCP 红线** → 所有理解代码的操作必须先用 MCP 工具（`get_repo_map` → `get_file_outline` → `search_symbols`），禁止直接 Read 全文件，省 ~90% token
8. **🔍 6 维度 Audit**（v1.4）→ `audit_tools.py` 随时可跑 `/audit`，检查部署完整性 + 技能合规 + 红线一致 + MCP 健康 + 版本一致 + Schema 合法

### 🔴 12 条全局红线（v2.0 · install.sh 自动同步到 7 工具）

`install.sh` Step 5 自动把 AGENTS.md 中的 **12 条红线**（5 Core Instincts + 7 Verbal Rules）注入到 **7 个 AI 工具的用户级**规则文件，以 **2 个 H2 sentinel 块**承载（见 `scripts/_lib/redline_markers.txt`）：

| # | 层级 | 说明 |
|---|------|------|
| C1-C5 | Core Instincts | 完成前验证 / 用户交互 / 事实优先 / MCP-S1 / Token 感知 |
| V1-V7 | Verbal Rules | 摘要 / 验证 Gate / Subagent / Worktree / 进度 / 一致性 / 视觉 |

完整条文见 [`AGENTS.md`](AGENTS.md)。install 以 2 个 H2 sentinel 块注入（`scripts/_lib/redline_markers.txt`）。

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

详见 [`scripts/install/_common.sh` 的 `common_inject_red_lines`](scripts/install/_common.sh)（v2.0 · 2 H2 块 / 12 条规则）。

### 更新链路

```
源仓库 (GitHub) curl install.sh → render_plugins.py（ToolAdapter 注册表渲染 manifest）
  → 部署 skills/hooks/commands 到各工具
  → ToolAdapter.activate（ZCode: register marketplace + enabledPlugins）
  → inject_rules.py（12 条红线 · 2 sentinel 块注入）
  → audit_tools.py（6 维度自检）
  → 重启工具会话 → SessionStart hook 注入 → 新会话生效
```

已安装用户执行 `curl .../install.sh | bash` 即可一键同步所有变更（智能模式：未装→安装，已装旧版→升级，同版→等待）。

---

## 📄 许可

MIT © tsfdsong

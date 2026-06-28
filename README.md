# LoopEngine — 循环工程全家桶

> **loop** 闭环编码 + **go** 全自动编排 + **skill-hub** 55技能智能调度，一站式 AI 编程引擎插件。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-blue)](package.json)

---

## 🚀 一键安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

## 🔄 一键更新

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/update.sh | bash
```

脚本自动检测已安装的 AI 编程工具（Claude Code / Codex / Gemini CLI / Copilot CLI / Pi / ZCode）并执行对应安装/更新。

---

## 🔴 MCP 红线规则（v1.0.1 新增）

> **任何需要理解代码结构的操作，必须先用 MCP 工具，禁止直接 Read 全文件。** 实测可节省 ~90% token。

| 规则 | 内容 |
|------|------|
| **适用范围** | 修改代码、调研代码、解释代码、分析架构、查找定义/引用 |
| **标准流程** | `get_repo_map` → `get_file_outline` → `search_symbols` → `Read`（仅精确行） |
| **唯一例外** | MCP 全部不可用、文件 < 50 行、需精确行内容 |
| **违规判定** | 连续 3 次直接 Read 全文件未用 MCP = 红线事故 |

此规则已写入所有层级：用户级 `~/.zcode/AGENTS.md`、项目级 `AGENTS.md`、skill-hub、go、loop 技能。

---

## 📦 各平台安装命令

| 平台 | 安装命令 | 验证 |
|------|---------|:--:|
| **Claude Code** | `claude plugin marketplace add https://github.com/tsfdsong/loop_engineering` 然后 `claude plugin install loopengine` | ✅ 实机 |
| **ZCode** | `git clone https://github.com/tsfdsong/loop_engineering %USERPROFILE%/.zcode/cli/plugins/cache/loopengine-local/loopengine/1.0.0` | ⚠️ 手动 |
| **Codex** | 插件市场搜索 `loopengine` | ⏳ |
| **Cursor** | `/add-plugin tsfdsong/loop_engineering` | ⏳ 应用内 |
| **Gemini CLI** | `gemini extensions install https://github.com/tsfdsong/loop_engineering` | ⏳ |
| **Copilot CLI** | `copilot plugin install loopengine@tsfdsong` | ⏳ |
| **Kimi Code** | `/plugins install https://github.com/tsfdsong/loop_engineering` | ⏳ |
| **OpenCode** | `opencode.json` 中添加 `"plugin": ["loopengine@git+https://github.com/tsfdsong/loop_engineering.git"]` | ⏳ |
| **Pi** | `pi install git:https://github.com/tsfdsong/loop_engineering` | ⏳ |

---

## 🧠 三大核心

```
┌───────────────────────────────────────────────────┐
│                   skill-hub                        │
│           智能路由 · 会话启动自动加载               │
│     收到任务 → 分析意图 → 匹配 55 技能中最准的      │
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

### `skill-hub` — 智能路由（自动生效）
无需手动调用。收到任何任务后自动从 55 个技能中匹配最精准的一个：

| 你说 | 自动加载 |
|------|---------|
| "这个类太大了" | `refactoring` |
| "设计 API 接口" | `api-design-principles` |
| "报错了帮我看看" | `systematic-debugging` |
| "写个单元测试" | `testing-patterns` |
| "画个架构图" | `drawio-skill` |

---

## 📚 技能分类（55个）

| 分类 | 数量 | 典型技能 |
|------|------|---------|
| 📝 代码编写 | 5 | `clean-code` `code-quality-principles` `code-complete` |
| 🏗️ 架构设计 | 7 | `clean-architecture` `domain-driven-design` `ddd-distilled` |
| 🔧 重构 | 4 | `refactoring` `refactoring-guru` `legacy-code` |
| 🧪 测试 | 3 | `test-driven-development` `testing-patterns` `e2e-testing-patterns` |
| 🐛 调试 | 1 | `systematic-debugging` |
| 🔌 API/安全 | 5 | `api-design-principles` `api-security-best-practices` `auth-implementation-patterns` |
| 📄 文档 | 5 | `code-documentation-doc-generate` `docx` `pdf` `api-documentation-generator` |
| 🔍 代码审查 | 3 | `code-reviewer` `requesting-code-review` `receiving-code-review` |
| ✅ 验证 | 1 | `verification-before-completion` |
| 🚀 工程流程 | 7 | `github-actions-templates` `using-git-worktrees` `release-it` |
| 📋 规划执行 | 5 | `brainstorming` `writing-plans` `executing-plans` `subagent-driven-development` |
| 📋 产品管理 | 2 | `product-manager` `to-prd` |
| 🛠️ 技能管理 | 4 | `writing-skills` `skill-creator` `find-skills` `agent-skill-architecture` |
| 🗄️ 数据库 | 1 | `database-design` |
| 🛠️ 工具 | 3 | `drawio-skill` `agent-browser` `using-loopengine` |
| 🧭 路由 | 3 | `loop` `loop-library` `skill-router` |

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
├── skills/                  # 55 个技能定义（SKILL.md + references）
│   ├── loop/                # 闭环编码引擎
│   ├── go/                  # 全自动编排引擎（v4.0 ZCode 纯血 + Worktree 并发）
│   │   └── scripts/         # Python 编排脚本（orchestrator/zcode_runner/git_ops/state_manager）
│   ├── skill-hub/           # 智能路由中心（会话启动注入）
│   └── ...                  # 其余 52 个技能
├── hooks/                   # 会话启动钩子
│   ├── session-start        # 启动引导脚本（注入 skill-hub）
│   ├── run-hook.cmd         # 跨平台 polyglot 包装器
│   └── hooks*.json          # 各平台钩子配置
├── docs/                    # 文档
│   ├── zcode-install-guide.md   # ZCode 桌面版安装指南
│   └── loopengineering-design/  # 架构设计图
├── install.sh               # 一键安装脚本（支持 --update 模式）
├── update.sh                # 一键更新脚本（v1.0.1 新增）
├── .zcode-plugin/           # ZCode 插件清单
├── .claude-plugin/          # Claude Code 插件清单
├── .codex-plugin/           # Codex 插件清单
├── .cursor-plugin/          # Cursor 插件清单
├── .kimi-plugin/            # Kimi Code 插件清单
├── .opencode/               # OpenCode 插件
├── .pi/                     # Pi 运行时扩展
├── package.json             # npm 包元数据 + Pi 配置
├── gemini-extension.json    # Gemini CLI 扩展清单
├── AGENTS.md / CLAUDE.md    # 代理引导文件（含 MCP 红线规则）
└── GEMINI.md                # Gemini 启动上下文
```

---

## 🔧 原理

LoopEngine 采用与 [Superpowers](https://github.com/obra/Superpowers) 相同的插件架构：

1. **会话启动钩子** → `hooks/session-start` 脚本在 AI 会话启动时触发
2. **启动引导注入** → 将 `skill-hub/SKILL.md` 注入到会话上下文
3. **自动路由** → 代理学会根据用户意图自动从 55 个技能中匹配最精准的一个
4. **🔴 MCP 红线** → 所有理解代码的操作必须先用 MCP 工具（`get_repo_map` → `get_file_outline` → `search_symbols`），禁止直接 Read 全文件，省 ~90% token

### 更新链路

```
源仓库 (GitHub) git pull → 内置包目录 → xcopy 同步 CLI 缓存 → 重启 ZCode → SessionStart hook 注入 → 新会话生效
```

已安装用户执行 `curl .../update.sh | bash` 即可一键同步所有变更。

---

## 📄 许可

MIT © tsfdsong

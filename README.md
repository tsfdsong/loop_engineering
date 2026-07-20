# LoopEngine — 循环工程全家桶

> **v2.0**（2026-07-18）：**go** 全自动编排（含 family 识别）+ **loop** 闭环编码（门禁按 L 分级）+ **supervisor** 监控看门狗 + **32 skills + 12 红线**（5 Core Instincts + 7 Verbal）+ 工具/模型双无关化。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](AGENTS.md)
[![skills](https://img.shields.io/badge/skills-32-green)](skills/)
[![redlines](https://img.shields.io/badge/redlines-12-red)](AGENTS.md)

---

## 🚀 一键安装 / 更新 / 卸载（v2.1 · Python 统一入口）

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
# Windows: … | python
# Fallback: curl -o install.py … && python3 install.py install
```

已有 clone：`python3 install.py install` · 卸载：`python3 install.py uninstall`  
详情与 Tier 说明见 [`docs/INSTALL.md`](docs/INSTALL.md)。需要 **Python ≥ 3.10**。

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

**安装**（`install.py` 会写入 MCP 配置；二进制需自行在 PATH）：
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

## 📦 各平台安装

| 平台 | 方式 | 验证 |
|------|------|:--:|
| **所有平台** | `curl …/install.py \| python3`（detect 本机工具） | ✅ |
| **Cursor** | `~/.cursor/plugins/local/loopengine`（官方 plugins，非平铺） | ✅ |
| **Claude Code** | `installed_plugins.json` + local marketplace | ✅ |
| **ZCode** | 官方 cache `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/<ver>/` + marketplace.json + enabledPlugins | ✅ |
| **Codex / Gemini** | Tier-2 整包 + 规则注入 | ✅ |
| **Copilot / Pi** | Tier-3 skills + AGENTS 注入 | ✅ |

详见 [`docs/INSTALL.md`](docs/INSTALL.md)。

---

## 🧠 核心架构（v2.0）

```
┌───────────────────────────────────────────────────┐
│                      go                           │
│  🚀 全自动编排 · family-first · worktree 并发      │
│  （8 场景家族识别 + DAG 组装）                      │
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

> **v2.0**：跨模块/多技能编排请用 `/go`（go Step 0 负责 family-first 路由）。

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
│   │   ├── references/      # family/DAG 契约
│   │   └── scripts/         # Python 编排脚本（orchestrator/zcode_runner/git_ops/state_manager）
│   ├── supervisor/          # 并发子任务监控
│   └── ...                  # 其余技能
├── commands/                # Slash commands（plugin 包组件）
│   ├── audit.md             # /audit 6 维度部署审计
│   ├── go.md                # /go 全自动编排（含 family 路由）
│   └── loop.md              # /loop 闭环编码
├── hooks/                   # 会话启动钩子
│   ├── session-start        # 启动引导脚本（注入 go runtime bundle）
│   ├── run-hook.cmd         # 跨平台 polyglot 包装器
│   └── hooks*.json          # 各平台钩子配置
├── docs/                    # 文档
│   ├── INSTALL.md           # 安装指南（install.py）
│   ├── mcp-setup-guide.md   # MCP 三件套安装配置
│   ├── lessons-learned.md   # 事故教训库（单一真源）
│   └── 2026-07-20-*.md      # plugin-shaped install 设计 / 计划
├── scripts/                 # 平台工具脚本
│   ├── loopengine_install/  # 安装运行时（adapters + lifecycle）
│   ├── render_plugins.py    # plugin manifest 渲染（ToolAdapter；无侧激活）
│   ├── audit_tools.py       # 6 维度部署审计
│   ├── inject_rules.py      # 红线 sentinel 注入
│   ├── merge_mcp_config.py  # DEPRECATED CLI · adapters 主路径
│   ├── install_zcode_plugin.py  # DEPRECATED CLI · 仍导出 compute_seed_hash
│   └── register_zcode_*.py  # ZCode marketplace / enabledPlugins helpers
├── tests/                   # 单元测试（unittest）
├── install.py               # 一键安装 / 更新 / 卸载（唯一入口）
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

### 🔴 12 条全局红线（v2.0 · install.py 自动同步到各工具）

`install.py` 把 AGENTS.md 中的 **12 条红线**（5 Core Instincts + 7 Verbal Rules）注入到各 AI 工具的用户级规则文件，以 **2 个 H2 sentinel 块**承载（见 `scripts/_lib/redline_markers.txt`）：

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
- **自动同步** —— 重跑 `python3 install.py install` 时规则自动更新

详见 `scripts/loopengine_install/adapters/helpers.py`（红线提取 + inject）。

### 更新链路

```
源仓库 (GitHub) curl install.py → loopengine_install（中央包 + Adapter 四件套）
  → 部署 skills/hooks/commands 到各工具官方插件路径
  → MCP merge + AGENTS 注入 + registry（Claude/ZCode）
  → 写入 ~/.loopengine/install-manifest.json
  → 重启工具会话 → SessionStart hook 注入 → 新会话生效
```

已安装用户执行 `curl …/install.py | python3` 或 `python3 install.py install` 即可同步；卸载用 `python3 install.py uninstall`。

---

## 📄 许可

MIT © tsfdsong

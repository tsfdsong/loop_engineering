# Contributing to LoopEngine

> 本文档面向 **LoopEngine 插件的贡献者/开发者**（不是 AI agent · 不是终端用户）。
> - 终端用户安装/使用 → 见 `README.md`
> - AI agent 决策规则 → 见 `AGENTS.md`（仓库根）
> - 完整设计文档 → 见 `docs/superpowers/specs/`

---

## 1. 工具/模型双无关性（硬约束 · v2.0）

本插件坚持**宿主工具无关** + **模型无关**。贡献者提交 PR 时必须遵守：

### 1.1 工具无关（Y 抽象为主+示例为辅）

| 场景 | 允许 | 禁止 |
|---|---|---|
| SKILL.md 主流程 | 用抽象词（"宿主工具"/"主 agent"/"AI 工具"）| 写死 `ZCode` / `Claude Code` / `Cursor` 等具体工具名 |
| MCP 配置说明 | 主推 `.mcp.json`（项目根标准）+ 附录速查表列已测工具 | 写死 `~/.zcode/cli/config.json` 路径 |
| 降级链 | 三档抽象（Primary/Secondary/Tertiary）+ 用户在 `.loopengine.yaml` 自配 | 写死 "降级到 DeepSeek" / "切换到 ZCode config" |
| hooks 注册 | 多目标支持（7-8 个工具）| 只注册 Claude Code 单一工具 |

**附录速查表**（已测工具的用户级配置路径）：见 `skills/go/references/runtime-config.md` + `skills/loop/references/agent-browser-setup.md`。新工具接入时只改附录 · 不改主流程。

### 1.2 模型无关（三档抽象）

降级链用 **Primary / Secondary / Tertiary** 三档抽象 · 用户在 `.loopengine.yaml` 自配具体模型。

| 场景 | 允许 | 禁止 |
|---|---|---|
| degradation.md | 三档抽象 + `.loopengine.yaml` 指向 | 写死 `deepseek-chat` / `GLM-5.2` / `Opus` |
| SKILL.md 性能描述 | "能力较弱模型" / "能力较强模型" | 指名特定模型（MiniMax / GPT / Claude） |
| benchmark | "至少 2 个能力梯度模型" | 指定单一模型测试 |

### 1.3 为什么有这个约束

- **插件定位**：通用工具 + 通用模型 · 在 7-8 个主流 AI 编程工具 + 各种模型上都表现好
- **维护成本**：写死工具/模型 = 每次新工具/新模型出现都要改主流程
- **用户选择权**：用户应能在自己的 `.loopengine.yaml` 配任何工具/模型 · 不被插件绑架

### 1.4 PR 审查清单

提交 PR 前自检：
- [ ] SKILL.md 主流程无具体工具名（附录速查表除外）
- [ ] 降级链用三档抽象（无具体模型名）
- [ ] MCP 配置主推 `.mcp.json`（不写死 `~/.zcode/`）
- [ ] hooks 注册支持多目标（不只单一工具）
- [ ] benchmark 不指定单一模型

---

## 2. 开发流程

### 2.1 本地开发

```bash
git clone https://github.com/tsfdsong/loop_engineering
cd loop_engineering
# 修改 AGENTS.md / skills/ / scripts/
bash install.sh --force  # 本地覆盖模式 · 同步到 ~/.zcode/ 等
```

### 2.2 测试

```bash
# 红线 marker 一致性
python3 scripts/audit_tools.py

# install.sh dry-run
bash install.sh --dry-run
```

### 2.3 提交

- AGENTS.md 改动需同步 `scripts/_lib/redline_markers.txt`（如果是 H2 标题变化）
- skills/ 新增/删除需同步 `package.json` 的技能数（如有）
- commit message 遵循 conventional commits（`feat:` / `fix:` / `refactor:` / `docs:`）

---

## 3. 设计原则（v2.0）

### 3.1 AGENTS.md = 纯 AI 决策规则

AGENTS.md 是 always-on 给 AI agent 看的 · 只承载 AI 决策所需的规则：
- ✅ Core Instincts（5 条诚信优先）
- ✅ Verbal Rules Index（7 条场景触发）
- ✅ Unified Checklist（会话末自检）
- ✅ MCP Tier 机制（工具裁剪）

**不应该**在 AGENTS.md 的内容：
- ❌ 安装命令（→ README.md）
- ❌ 开发者约束（→ 本文件 CONTRIBUTING.md）
- ❌ 设计文档（→ docs/superpowers/specs/）
- ❌ 历史变更记录（→ docs/legacy/）

### 3.2 三文件分工

| 文件 | 受众 | 内容 |
|---|---|---|
| `README.md` | 终端用户 | 介绍 + 安装 + 快速上手 |
| `AGENTS.md` | AI agent | 决策规则（always-on）|
| `CONTRIBUTING.md`（本文件）| 贡献者/开发者 | 开发约束 + 流程 + 设计原则 |

### 3.3 spec / plan / docs 分层

| 路径 | 用途 |
|---|---|
| `docs/superpowers/specs/` | 设计文档（spec）|
| `docs/superpowers/plans/` | 实施计划（plan）|
| `docs/legacy/` | 历史归档（被删内容）|
| `docs/INSTALL.md` | 安装详规 |
| `docs/lessons-learned.md` | 事故教训库 |

---

## 4. 联系

- Issues: https://github.com/tsfdsong/loop_engineering/issues
- Discussions: https://github.com/tsfdsong/loop_engineering/discussions

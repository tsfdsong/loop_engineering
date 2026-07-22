# 🚀 LoopEngine — 循环工程全家桶

**一句话**：用 `/loop` 做单任务闭环，用 `/go` 做多模块编排，外加 32 个技能与 12 条红线。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![skills](https://img.shields.io/badge/skills-32-green)](skills/)
[![redlines](https://img.shields.io/badge/redlines-12-red)](AGENTS.md)

---

## ⚡ 安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
# Windows 可用 python；需要 Python ≥ 3.10
```

已有 clone：`python3 install.py install` · 卸载：`python3 install.py uninstall`  
详规：[`docs/INSTALL.md`](docs/INSTALL.md)

---

## 🧠 怎么用

```
brainstorming / 设计草稿
        ↓
/go   大活：分析 → 拆任务 → 并行 → 汇合
        ↓ 任务包（goal + 验收）
/loop 单任务：编码 ↔ 门禁 ↔ 自愈 ↔ 交付
```

| 命令 | 何时用 |
|------|--------|
| `/loop 目标，验收…` | 目标清楚、单任务落地 |
| `/go 功能描述` | 跨模块、要拆分/并发 |
| brainstorming | 还没想清楚要不要做 / 怎么选 |

**示例：**

```
/loop 修复用户列表分页，第 2 页数据正确
/go 实现订单模块，含创建、查询、取消
```

模糊需求不要硬塞进 `/loop`，先 brainstorming 或 `/go`。

---

## 🔌 MCP（省 token）

理解代码结构时，优先用 MCP，不要盲 Read 全文件。

| 场景 | 工具 |
|------|------|
| 新仓库 | `get_repo_map` → `get_file_outline` |
| 大文件 | `get_file_outline` + `search_symbols` |
| 已知位置小改 | `Read`（带 offset/limit）即可 |
| 跨文件引用 | `check_references` / `find_importers` |
| 关键字 | `search_text` / `search_ast` |

三件套：`jcodemunch-mcp` · `repomix` · `headroom-ai`  
安装与配置：[`docs/mcp-setup-guide.md`](docs/mcp-setup-guide.md)

```bash
pip install --upgrade jcodemunch-mcp headroom-ai
npm install -g repomix
jcodemunch-mcp index_folder .
```

---

## 📦 支持的工具

| 类型 | 工具 |
|------|------|
| 原生插件 | Cursor · Claude Code · ZCode |
| 半插件 | Codex · Gemini |
| 注入型 | Copilot · Pi |

规则由 `install.py` 注入各工具的 AGENTS / 等价文件。条文见 [`AGENTS.md`](AGENTS.md)。

---

## ✅ 验证安装

新开 AI 会话，试一句：

```
/loop 写一个 Hello World
```

或：

```
告诉我 LoopEngine 能做什么
```

能加载对应技能即成功。

---

## 📚 技能分类

| 分类 | 例子 |
|------|------|
| 闭环 | `loop` · `go` · `supervisor` · `using-loopengine` |
| 规划 | `brainstorming` · `spec-driven-development` · `product-manager` |
| 质量 | `clean-code` · `code-reviewer` · `refactoring` |
| 审查 | `system-review` · `evidence-first` · `software-architecture` |
| 测试 | `testing` · `systematic-debugging` · `web-quality` |
| 工程 | `using-git-worktrees` · `verification-officer` · `subagent-driven-development` |

完整列表：`skills/`。入门导览：`skills/using-loopengine/SKILL.md`。

---

## 📁 仓库要点

| 路径 | 作用 |
|------|------|
| `install.py` | 唯一安装入口 |
| `skills/` | 技能定义 |
| `commands/` | `/loop` · `/go` · `/audit` · `/git-commit` |
| `hooks/` | 会话启动注入 |
| `docs/INSTALL.md` | 安装详规 |
| `AGENTS.md` | AI 红线（单点真源） |
| `scripts/` | 安装器、审计、渲染 |

贡献约定：[`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## 📄 许可

MIT © tsfdsong

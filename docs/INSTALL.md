# LoopEngine 安装指南

> **v2.1** — 唯一入口 `install.py`（Python ≥ 3.10），macOS / Windows / Linux 同一条命令。  
> 按各 AI Agent **官方插件模式**部署 skills / hooks，并写入 MCP、AGENTS（规则）与插件注册表。  
> 旧 `install.sh` / `install.ps1` 已退役。

## 一行安装

```bash
# 远程（推荐）
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3

# Windows 若命令是 python：
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python

# Fallback（管道编码异常时）
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py -o install.py
python3 install.py install
```

已有 clone：

```bash
python3 install.py install
python3 install.py install --only=cursor,claude,zcode
python3 install.py install --all
python3 install.py uninstall
python3 install.py install --check
```

| Flag | 含义 |
|------|------|
| （无参数） | 智能安装/升级；detect 本机已装 Agent |
| `--only=a,b` | 只部署指定工具 |
| `--all` | 部署全部已支持工具（Tier-1/2/3） |
| `--force` | 同版也重装 |
| `--dry-run` / `--json` | 只打印计划 |
| `uninstall` | 按 `~/.loopengine/install-manifest.json` 逆序卸载 |

**依赖**：Python ≥ 3.10；远程安装需 `git`（clone 到 `~/.loopengine/src`）。

## 工具 Tier

| Tier | 工具 | 行为 |
|------|------|------|
| 1 原生插件 | Cursor、Claude、ZCode | 官方 plugin 路径 + registry + MCP + AGENTS |
| 2 半插件 | Codex、Gemini | 整包目录 + AGENTS/等价规则注入 |
| 3 注入型 | Copilot、Pi | skills 树 + AGENTS 注入 |

## 安装后布局（要点）

| 项 | 路径 |
|----|------|
| 中央包 | `~/.loopengine/plugins/loopengine/<version>/`（`current` 为 **pointer 文件**，禁止软链） |
| 清单 | `~/.loopengine/install-manifest.json` |
| Cursor | `~/.cursor/plugins/local/loopengine`（真实拷贝）+ 平铺 `~/.cursor/skills/<skill>/`（Agent 发现）|
| Claude | cache + marketplace **各自真实拷贝** + `installed_plugins.json` 键 `loopengine@loopengine-local` |
| ZCode | `~/.zcode/skills/loopengine`（真实拷贝，禁止软链中央包）+ enabledPlugins |
| Cursor MCP | `~/.cursor/mcp.json`（仅 LE 管理的 jcodemunch/repomix/headroom） |

## 自检

```bash
python3 install.py install --check --json
ls ~/.cursor/plugins/local/loopengine/skills/go/SKILL.md
python3 scripts/audit_tools.py   # 含 G 维：registry / 双部署 skills / 禁止 symlink
```

## 常见问题

| 问题 | 处理 |
|------|------|
| 无 Python / 版本过低 | 安装 Python 3.10+；不要回退 Bash 安装 |
| `curl \| python3` 在 Windows 异常 | 用 `-o install.py && python install.py` |
| Cursor 插件里只看见个别 skill | `python3 install.py install --only=cursor --force`（真实拷贝 + 平铺双部署） |
| 想干净卸载 | `python3 install.py uninstall`（保留用户自有 skill / 非 LE MCP） |
| ZCode/Cursor MCP 缺失 | 确认 PATH 有 `jcodemunch`/`repomix` 后重装对应 `--only` |

## 开发者

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_loopengine_install*.py' -v
python3 -m loopengine_install install --dry-run --json
```

设计与计划：`docs/2026-07-20-plugin-shaped-install-design-v2.md`、`docs/2026-07-20-plugin-shaped-install-plan.md`。

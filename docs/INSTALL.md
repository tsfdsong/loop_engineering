# 📥 LoopEngine 安装指南

唯一入口：`install.py`（Python ≥ 3.10）。按各 AI 工具的**官方插件路径**部署，并写入 MCP、AGENTS 规则与注册表。

- Cursor：只装到 `~/.cursor/plugins/local/loopengine`（不要平铺到 `~/.cursor/skills/`）
- 存储：禁止用 symlink 做中央包指针

---

## 一行安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3

# Windows 若命令是 python：
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python

# 管道异常时：
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py -o install.py
python3 install.py install
```

本地已有 clone：

```bash
python3 install.py install
python3 install.py install --only=cursor,claude,zcode
python3 install.py install --all
python3 install.py uninstall
python3 install.py install --check
```

| 参数 | 含义 |
|------|------|
| （默认） | 检测本机已装工具，智能安装/升级 |
| `--only=a,b` | 只装指定工具 |
| `--all` | 装全部已支持工具 |
| `--force` | 同版本也重装 |
| `--dry-run` / `--json` | 只看计划 |
| `uninstall` | 按清单逆序卸载 |

远程安装需要 `git`（clone 到 `~/.loopengine/src`）。

---

## 工具分层

| Tier | 工具 | 行为 |
|------|------|------|
| 1 原生插件 | Cursor · Claude · ZCode | 官方 plugin 路径 + 注册表 + MCP（Claude 除外）+ AGENTS |
| 2 半插件 | Codex · Gemini | 整包目录 + 规则注入 |
| 3 注入型 | Copilot · Pi | skills 树 + AGENTS 注入 |

---

## 装完在哪

| 项 | 路径 |
|----|------|
| 中央包 | `~/.loopengine/plugins/loopengine/<version>/`（`current` 是指针文件，不是软链） |
| 清单 | `~/.loopengine/install-manifest.json` |
| Cursor | `~/.cursor/plugins/local/loopengine` |
| Claude | cache + marketplace 各一份拷贝；键 `loopengine@loopengine-local` |
| ZCode | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/<ver>/` |
| Cursor MCP | `~/.cursor/mcp.json`（仅管理 jcodemunch / repomix / headroom） |
| Claude MCP | **不自动注入**（自行配 `~/.claude/settings.json` 或项目 `.mcp.json`） |

---

## 自检

```bash
python3 install.py install --check --json
ls ~/.cursor/plugins/local/loopengine/skills/go/SKILL.md
python3 scripts/audit_tools.py
```

---

## 常见问题

| 问题 | 处理 |
|------|------|
| 没有 Python / 版本低 | 装 Python 3.10+ |
| Windows 管道异常 | `-o install.py && python install.py` |
| Cursor 里技能不全 | `python3 install.py install --only=cursor --force` |
| 想干净卸掉 | `python3 install.py uninstall` |
| MCP 缺失 | PATH 有 `jcodemunch` / `repomix` 后重装对应 `--only` |

MCP 详规：[`mcp-setup-guide.md`](mcp-setup-guide.md)  
事故教训：[`lessons-learned.md`](lessons-learned.md)

---

## 开发自测

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_loopengine_install*.py' -v
python3 -m loopengine_install install --dry-run --json
```

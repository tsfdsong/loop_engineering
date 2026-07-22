# 🔌 MCP 三件套

LoopEngine 靠三个 MCP 少读废话、少烧 token：

| 工具 | 安装 | 干什么 |
|------|------|--------|
| **jCodeMunch** | `pip install jcodemunch-mcp` | 按符号读代码（省最多） |
| **Repomix** | `npm install -g repomix` | 打包/压缩整库结构 |
| **Headroom** | `pip install headroom-ai` | 压缩长会话上下文 |

推荐先跑 `install.py`，它会检测本机工具并写入 MCP（Cursor / ZCode 等）。Claude 不自动注入 MCP，需自己配。

### Cursor：`loopengine-ask`（C2 决策）

Cursor 安装 LoopEngine 时会额外注册 MCP **`loopengine-ask`**，提供工具 **`AskUserQuestion`**（本地网页点选，兑现 C2 决策交互）。

- **依赖**：`pip install mcp`（FastMCP 运行时）
- **注册位置**：`~/.cursor/mcp.json` 的 `mcpServers.loopengine-ask`（由 `install.py` / Cursor adapter 写入）
- **工具名**：`AskUserQuestion`（2–4 个选项，单选/多选）
- **故障处理**：若返回 `validation_error` / `browser_error` / `timeout` / `busy`，**重试工具或上报阻塞**；**禁止**改用 markdown 列表呈现决策选项继续执行（见注入规则 `LOOPENGINE-CURSOR-ASK-NOTE`）

---

## 手动安装

```bash
npm install -g repomix
pip install --upgrade jcodemunch-mcp headroom-ai   # Linux/macOS 可用 pip3

repomix --version
jcodemunch-mcp --version
headroom --version
```

**Windows**：若命令找不到，把 pip / npm 的 Scripts 目录加进 PATH。  
**macOS**：pip 用户脚本常在 `~/Library/Python/<ver>/bin/`，必要时加进 PATH。

首次索引当前项目：

```bash
jcodemunch-mcp index_folder .
```

---

## 配置写哪

`install.py` 会尽量自动写好。手动时注意两套 schema：

### Cursor / 项目根（`mcpServers`）

`~/.cursor/mcp.json` 或项目 `.mcp.json`：

```json
{
  "mcpServers": {
    "jcodemunch": { "command": "jcodemunch-mcp", "args": ["serve"] },
    "repomix": { "command": "repomix", "args": ["--mcp"] },
    "headroom": { "command": "headroom", "args": ["mcp", "serve"] }
  }
}
```

### ZCode 桌面（`mcp.servers` + `type`）

`~/.zcode/cli/config.json`：

```json
{
  "mcp": {
    "servers": {
      "jcodemunch": {
        "type": "stdio",
        "command": "jcodemunch-mcp",
        "args": ["serve"]
      },
      "repomix": {
        "type": "stdio",
        "command": "repomix",
        "args": ["--mcp"]
      }
    }
  }
}
```

Windows 上建议写绝对路径，且带正确后缀（`.exe` / `.cmd`）。改完重启对应工具。

Claude：自行写入 `~/.claude/settings.json` 或项目 `.mcp.json`。

---

## 怎么用（原则）

| 你想… | 优先 |
|------|------|
| 摸新仓库 | `get_repo_map` → `get_file_outline` |
| 读大文件 | `get_file_outline` + `search_symbols` / `get_symbol_source` |
| 改已知几行 | `Read`（带 offset/limit） |
| 找引用 | `check_references` / `find_importers` |
| 搜关键字 | `search_text` / `search_ast` |
| MCP 挂了 | `repomix` 打包，再降级 `Read` |

长会话上下文膨胀时用 Headroom 压缩（或主动写阶段小结）。

细则与红线场景矩阵见 `AGENTS.md`（C4）和 `skills/evidence-first/SKILL.md`。

---

## 排障

| 现象 | 处理 |
|------|------|
| 列表里没有 server | 查 PATH、后缀、绝对路径；重跑 `install.py install --only=cursor`（或 zcode） |
| 命令能跑但 MCP 起不来 | 看 args：`serve` / `--mcp` / `mcp serve` 是否写对 |
| 索引过期 | 再跑 `jcodemunch-mcp index_folder .` |
| Claude 没有三件套 | 正常：需手动配置 |

安装入口：[`INSTALL.md`](INSTALL.md)

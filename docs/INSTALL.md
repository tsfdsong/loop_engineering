# LoopEngine 安装指南

> v1.3.2（2026-07-03）— 新增 `install.ps1`（Windows PowerShell 兄弟脚本，纯 PS 无需 Git Bash）；修复 3 个 install.sh bug（filter 分隔符 / Cursor 路径扁平 / macOS MCP fallback）；merge_mcp_config.py headroom 改可选。
> v1.3.1 三平台 install 脚本合一（3 平台从 ~145 → ~18 行），merge_mcp_config.py 合并 ZCode + Cursor 双 schema。
> v1.3.0 OS + AI Agent 全自动感知；v1.2.0+ 智能模式（首次装 / 升级 / 同版本 5 秒等待）。

## 一行安装

### macOS / Linux / Windows Git Bash

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

### Windows PowerShell（v1.3.2 新增 · 纯 PS 无需 Git Bash）

```powershell
irm https://github.com/tsfdsong/loop_engineering/raw/main/install.ps1 | iex
```

**装完即用**。无需重启 AI 工具，无需懂任何目录约定，无需手动选平台或工具。

> **执行策略提示**：若 `irm | iex` 被执行策略阻止，先跑 `Set-ExecutionPolicy -Scope Process Bypass`（仅当前会话生效）。

## v1.3.2 核心改进

| 改动 | 说明 |
|------|------|
| 🆕 **install.ps1 新增** | Windows PowerShell 兄弟脚本（~500 行），与 install.sh 行为契约一致，共用 3 个 Python helper（render_plugins.py / inject_rules.py / merge_mcp_config.py）。两个脚本并存，按平台选用 |
| 🔧 **filter 分隔符 bug 修复** | `common_filter_tool_root_dirs` 入口标准化 want_ids（换行/逗号/制表符 → 空格），修复 detect 用换行输出但匹配用空格导致 7 个 agent 全被误拒的 bug |
| 🔧 **Cursor skills 路径扁平** | Cursor 改走扁平模式 `~/.cursor/skills/<name>/SKILL.md`（逐 skill 覆盖，不清空公共目录，保护用户其他 skill）；原逻辑多两层 `loopengine/skills/` Cursor 扫不到 |
| 🔧 **macOS MCP fallback 补全** | macOS fallback 表补 Homebrew（`/opt/homebrew/bin` / `/usr/local/bin`）+ npm global + volta；Linux 补 npm global；修复 macOS headroom 装在 Homebrew 路径找不到的问题 |
| 🔧 **headroom 解耦** | `deploy_cursor_mcp` 把 headroom 从"写 Cursor MCP 的强制门槛"降级为可选；jcodemunch + repomix 必需，headroom 找不到仅告警不阻断；`merge_mcp_config.py` cursor schema 支持空 headroom（跳过 entry） |

### v1.3.2 PowerShell 特有处理

| 问题 | 根因 | 修复 |
|------|------|------|
| 中文乱码（`ZCode 鍐呯疆鍖?`）| PowerShell 5.1 默认用 GBK 读 .ps1 | install.ps1 加 UTF-8 BOM |
| `无法覆盖变量 HOME` | `$home` 是 PS 只读自动变量 | 改用 `$homeDir = $env:USERPROFILE` |

## 更新

**v1.2.0 起，更新 = 重新跑 install.sh**（智能模式自动判断）：

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

智能模式行为：
- **未装** → 首次安装
- **已装同版** → 5 秒等待（防误触，`--force` 跳过）
- **已装旧版** → 升级（直接执行，无需等待）

### 参数

| 参数 | 作用 |
|------|------|
| `bash install.sh` | 智能模式 + 自动感知本机 AI Agent（**v1.3.0 默认**） |
| `bash install.sh --all` | 强制全量 11 目标部署（绕过 detect） |
| `bash install.sh --only=zcode,cursor` | 只给指定 agent id 部署（逗号或空格分隔） |
| `bash install.sh --force` | 跳过 5 秒等待，强制重装 |
| `bash install.sh --dry-run` | 只检查版本不实际安装 |
| `bash install.sh -h` | 显示帮助 |

## 它做了什么（v1.1.0 全面同步 · v1.2.0 一体化 · v1.2.2 Cursor 兼容 · v1.3.0 自动感知）

| 步骤 | 行为 |
|------|------|
| 0️⃣ 版本自检 | 读 `~/.loopengine/.installed_version`，已装同版本则 5 秒等待 |
| 0️⃣.5 **AI Agent 自动感知**（v1.3.0） | 扫描本机 9 个特征路径，输出已检测列表；可用 `--all` / `--only` 覆盖 |
| 1️⃣ 拉源码 | `git clone --depth 1` 到 `/tmp/loopengine-install-$$/`，自动清理 |
| 2️⃣ 部署（5 子步） | **2a** 渲染 7 plugin manifest（去 _comment，version 同步；v1.2.2 加 Cursor）<br>**2b** 复制 `skills/` 到目标（**v1.3.0 平台分支** + agent filter）<br>**2c** 复制 `hooks/` 到目标<br>**2d** 部署 7 个 `plugin.json` / `marketplace.json` / `gemini-extension.json`<br>**2e** 复制 `AGENTS.md` + `README.md` 到目标 |
| 3️⃣ MCP 三件套 | `pip install --user jcodemunch-mcp headroom` + `npm i -g repomix`（已装会跳过） |
| 4️⃣ ZCode 桌面版 MCP | 自动写入 `~/.zcode/cli/config.json` 的 `mcp.servers`（**v1.0 根因**：桌面版真正入口） |
| 5️⃣ 7 条红线 | 把 AGENTS.md 的 7 条 🔴 红线章节注入 7 个工具的**用户级**规则文件（sentinel markers，幂等；v1.2.2 扩展自 5 条） |
| 5️⃣.5 **Cursor MCP 合并**（v1.3.0） | win/macOS/Linux 自动写入 `~/.cursor/mcp.json` 的 `mcpServers`（保留 drawio 等用户自有 server） |
| 6️⃣ 自检 | 验证关键路径 + manifest 数 + 写入 `~/.loopengine/.installed_version`（**v1.3.0 阈值按平台 + agent 过滤自适应**） |

### 同步目标一览

`--all` 时取全量 11 路径（默认仅 detect 到本机已装工具，5-9 路径自适应）：
- skills/ 8-9 路径
- hooks/ 8-9 路径
- AGENTS.md / README.md 8-9 路径
- plugin manifest 5-7 路径
- ZCode 桌面版 MCP 1 路径
- Cursor MCP（v1.3.0+） 1 路径（仅 detect 到 cursor）
- 7 条红线注入 7 工具用户级文件
- 版本号文件 1 路径

**v1.3.0+ 自适应**：`skill_ok >= 总目标的 80%` 即视为通过（v1.2.x 硬阈值 8/9 改为自适应）。

## 工具部署目标（v1.3.0 按平台分支）

| AI 工具 | Windows 路径 | macOS / Linux 路径 |
|---------|-------------|---------------------|
| **ZCode** | `~/.zcode/skills/loopengine/` | `~/.zcode/skills/loopengine/` |
| Claude Code | `~/.claude/skills/loopengine/` | `~/.claude/skills/loopengine/` |
| Codex | `~/.codex/skills/loopengine/` | `~/.codex/skills/loopengine/` |
| Gemini CLI | `~/.gemini/extensions/loopengine/` | `~/.gemini/extensions/loopengine/` |
| GitHub Copilot | `~/.copilot/skills/loopengine/` | `~/.copilot/skills/loopengine/` |
| Pi | `~/.pi/skills/loopengine/` | `~/.pi/skills/loopengine/` |
| Cursor | `~/.cursor/skills/loopengine/`（hooks/manifest）+ `~/.cursor/skills/<skill>/`（v1.3.2 扁平） | `~/.cursor/skills/loopengine/`（hooks/manifest）+ `~/.cursor/skills/<skill>/`（v1.3.2 扁平） |
| **ZCode 内置包**（Windows 专属） | `~/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin/` | ❌ 不部署（v1.3.0 修复：避免创建虚假 `$HOME/AppData`） |
| **ZCode CLI 缓存** | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/` | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/` |
| **Cursor MCP**（v1.3.0 新增） | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` |

> 🟢 ZCode 用户级 fallback 是关键 — 即使其他 ZCode 内部插件路径不动，技能也能加载。
> 🟢 **Cursor 完整集成**（v1.2.2 + v1.3.0 + v1.3.2 扁平修复）：skills 扁平部署到 `~/.cursor/skills/<skill>/`（v1.3.2 改动，原 v1.3.1 多两层 `loopengine/skills/` Cursor 扫不到）；hooks/plugin.json 在 `~/.cursor/skills/loopengine/`（plugin 根）；红线注入 `~/.cursor/rules/loopengine-interaction.mdc`；**MCP 合并写入 `~/.cursor/mcp.json`**（保留 drawio 等用户自有 server，headroom 可选）。

## 全局红线注入（Step 5）

`install.sh` 自动把 AGENTS.md 中的 7 条 🔴 红线章节（v1.2.2 起含进度汇报 + Subagent 边界）注入到 7 个 AI 工具的**用户级**规则文件：

- `~/.zcode/AGENTS.md`
- `~/.claude/CLAUDE.md`
- `~/.gemini/GEMINI.md`
- `~/.codex/AGENTS.md`
- `~/.cursor/rules/loopengine-interaction.mdc`
- `~/.copilot/AGENTS.md`
- `~/.pi/AGENTS.md`

**保证**：
- **幂等性**：重复执行不重复插入（sentinel markers 检测）
- **用户保留**：你的其他自定义内容不会被覆盖
- **自动同步**：重跑 `install.sh`（智能模式）时规则自动更新

## Cursor MCP 合并（v1.3.0 新增 · Step 5.5 · v1.3.2 headroom 改可选）

`install.sh` / `install.ps1` 自动把 MCP server 路径注入到 `~/.cursor/mcp.json` 的 `mcpServers`：

- `jcodemunch`（指向 `jcodemunch-mcp.exe` / `.cmd`）— **必需**
- `repomix`（指向 `repomix.exe` / `.cmd`）— **必需**
- `headroom`（指向 `headroom.exe` / `.cmd`）— **可选**（v1.3.2 改动：找不到时跳过该 entry，不阻断写入）

**关键差异**（[F] 来自本机 `.mcp.json` 实测）：
- **Cursor IDE** schema：`mcpServers.<name>.{command, args}` （**无** `type` 字段）
- **ZCode 桌面版** schema：`mcp.servers.<name>.{type: "stdio", command, args}`

**保留策略**：用 `setdefault` 保留所有顶层字段和用户已有 server（如 `drawio`），仅强制覆写 LoopEngine 自己的 key。原子写（`.tmp` + `os.replace`）。

**v1.3.2 headroom 解耦背景**：v1.3.1 及之前要求 jcodemunch + repomix + headroom **三个全找到**才写 Cursor mcp.json，但 macOS 上 headroom 常装在 Homebrew 路径（`/opt/homebrew/bin`，不在 fallback 表），导致整个 Cursor MCP 配置被跳过 → "macOS 不能用"。v1.3.2 把 headroom 降级为可选，并补全 macOS/Linux fallback 路径表。

## 验证

开新 AI 会话后发送：

```
"告诉我 LoopEngine 的核心价值，并说明 orch v2 的场景家族（family）有哪些"
```

期望：
- 解释出 "loop + go + orch 多技能编排" 核心价值
- 列出 orch 的 5 类（调研+决策 / 分析+建议 / 诊断+修复 / 设计+实现 / 并行调研）

自动安装验证：

```bash
# 1. 自检通过
bash install.sh --dry-run

# 2. 检查 9 工具 skill 部署
ls ~/.zcode/skills/loopengine/skills/orch/   # ZCode 用户级（plugin 中间层）
ls ~/.cursor/skills/orch/                    # Cursor（v1.3.2 扁平，无 loopengine/ 中间层）

# 3. 检查 Cursor MCP 合并
cat ~/.cursor/mcp.json                       # drawio + jcodemunch + repomix（+ 可选 headroom）

# 4. 检查 7 红线注入
grep "LOOPENGINE-MANAGED" ~/.zcode/AGENTS.md # 7 sentinel markers

# 5. 检查版本号
cat ~/.loopengine/.installed_version         # 1.3.2
```

## 故障排查

| 现象 | 解决 |
|------|------|
| `git clone` 失败 | 检查网络/VPN；可手动下载 ZIP 解压后跑 `bash install.sh` |
| **PowerShell `irm\|iex` 被阻止**（v1.3.2） | 先 `Set-ExecutionPolicy -Scope Process Bypass`（仅当前会话）；或本地下载后 `.\install.ps1 -Force` |
| **PowerShell 中文乱码**（v1.3.2） | install.ps1 已加 UTF-8 BOM；若仍乱码，确认用 PowerShell 5.1+ 且文件未被二次编码 |
| `pip install` 失败 | 先 `pip install --upgrade pip`；用 `python -m pip install --user <pkg>` 替代 |
| `npm install -g` 失败 | 检查 Node.js；Linux/macOS 上需要 sudo 或 `npm config set prefix` |
| 装完 ZCode 还是看不到 loopengine 技能 | 重跑 `bash install.sh`（覆盖所有目标目录） |
| **ZCode MCP 工具不显示** | 检查 `cat ~/.zcode/cli/config.json` 是否有 `mcp.servers` 三个 server；缺失就重跑 `bash install.sh` |
| **Cursor MCP 工具不显示** | 检查 `cat ~/.cursor/mcp.json` 是否有 jcodemunch+repomix（headroom 可选）；缺失就重跑 `bash install.sh --force`（确保 detect 到 cursor） |
| **macOS Cursor MCP 不写入**（v1.3.2 已修） | v1.3.1 macOS headroom 装在 Homebrew 路径找不到 → 整个跳过；v1.3.2 已补 fallback 表 + headroom 解耦，升级后重跑 `bash install.sh --force` |
| **Cursor skills 看不到**（v1.3.2 已修） | v1.3.1 skills 部署在 `~/.cursor/skills/loopengine/skills/`（多两层，Cursor 扫不到）；v1.3.2 改扁平 `~/.cursor/skills/<skill>/`，升级后重跑 `--force` |
| MCP 工具显示了但调用失败 | 命令路径要带 Windows 扩展名（`jcodemunch-mcp.exe` / `repomix.cmd` / `headroom.exe`），install.sh/ps1 已自动处理 |
| 想强制重装最新版本 | `rm ~/.loopengine/.installed_version && bash install.sh`（或 PS: `Remove-Item ~/.loopengine/.installed_version; .\install.ps1 -Force`） |
| **v1.3.0 detect 没识别某个工具** | 用 `bash install.sh --only=zcode,cursor --force` 显式指定；或用 `--all` 强制全量（PS: `-Only zcode,cursor -Force`） |

## 设计哲学

- **不依赖** ZCode 内部 `marketplace.json` / `.zcode-plugin/plugin.json` 注册（v2.0 重构后）
- **不重启** AI 工具即可生效（直接 cp 到约定目录）
- **不重复造轮子**：每个工具的"内部机制"对我们是黑盒；只关心"约定目录"
- **覆盖 7 AI 工具**（ZCode + Claude Code + Codex + Gemini + Cursor + Copilot + Pi）+ ZCode 桌面版/内置包/CLI 缓存 3 路径；Kimi/OpenCode 走各自平台原生命令
- **单一真源**：plugin manifest 改版本号 = 改 `.plugin-template.json` 的 `version` 字段（6 个 overlay 自动同步）
- **v1.3.0+ 自动感知**：默认只给本机已装工具部署；显式 `--all` / `--only` 可覆盖
- **v1.3.1 三平台合一**：3 平台脚本从 ~145 → ~18 行（-87%），共享 `common_run_platform_steps` 主驱动
- **v1.3.2 PowerShell 兄弟**：新增 `install.ps1`（纯 PS 无需 Git Bash），与 `install.sh` 行为契约一致，共用 3 个 Python helper；两个脚本并存按平台选用

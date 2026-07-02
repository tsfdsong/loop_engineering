# LoopEngine 安装指南

> v1.3.1（2026-07-02）— 三平台 install 脚本合一（3 平台从 ~145 → ~18 行），merge_mcp_config.py 合并 ZCode + Cursor 双 schema，AGENT 标签用关联数组去重，5 红线/工具 step 拆 5 sub-function。
> v1.3.0 OS + AI Agent 全自动感知；v1.2.0+ 智能模式（首次装 / 升级 / 同版本 5 秒等待）。

## 一行安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

**装完即用**。无需重启 AI 工具，无需懂任何目录约定，无需手动选平台或工具。

## v1.3.1 核心改进

| 改动 | 说明 |
|------|------|
| 🆕 **三平台脚本合一** | `_common.sh::common_run_platform_steps` + `common_detect_mcp_exe` + `common_install_mcp_packages` + `common_write_zcode_desktop_config` 替代 windows/macos/linux 各自的 3 副本函数。3 平台从 ~145 → ~18 行（-87%）|
| 🆕 **merge_mcp_config.py 合并** | 原 merge_zcode_config.py（v1.2.3）+ merge_cursor_config.py（v1.3.0）合并为单脚本 + `--schema=zcode\|cursor` 参数。`atomic_write` 6 行在脚本内保留（不抽 `_atomic_io.py`）|
| 🆕 **AGENT 标签关联数组** | `COMMON_LABEL_TO_ID` 关联数组替代 `AGENT_LABEL_MAP + filter case` 双份真源，加新 agent 改 1 处 |
| 🆕 **deploy 拆 5 sub-function** | `common_deploy_to_9_tools` 100 行单函数拆为 `common_cleanup_target_top_level` / `common_copy_skills_for` / `common_copy_hooks_for` / `common_deploy_manifest_for` / `common_copy_root_docs_for` + `_for_each_target` 通用 iterator |
| 🆕 **BASE_TARGETS 共享数组** | windows / macos\|linux tool_root_dirs 共享 7 行基础目标，windows 追加 1 行 AppData |
| 🆕 **Kimi/OpenCode 清理** | 不在 install.sh 范围，文档/代码一致：手动 `/plugins install` / 修改 `opencode.json` |
| v1.3.0 | OS + AI Agent 自动感知（默认按本机已装工具部署）+ Cursor MCP 合并 + 修 macOS/Linux 虚假 `$HOME/AppData/` 路径 bug |

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
| Cursor | `~/.cursor/skills/loopengine/` | `~/.cursor/skills/loopengine/` |
| **ZCode 内置包**（Windows 专属） | `~/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin/` | ❌ 不部署（v1.3.0 修复：避免创建虚假 `$HOME/AppData`） |
| **ZCode CLI 缓存** | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/` | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/` |
| **Cursor MCP**（v1.3.0 新增） | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` |

> 🟢 ZCode 用户级 fallback 是关键 — 即使其他 ZCode 内部插件路径不动，技能也能加载。
> 🟢 **Cursor 完整集成**（v1.2.2 + v1.3.0）：skills/hooks/plugin.json 部署到 `~/.cursor/skills/loopengine/`，红线注入 `~/.cursor/rules/loopengine-interaction.mdc`，**MCP 合并写入 `~/.cursor/mcp.json`**（保留 drawio 等用户自有 server）。

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

## Cursor MCP 合并（v1.3.0 新增 · Step 5.5）

`install.sh` 自动把 3 个 MCP server 路径注入到 `~/.cursor/mcp.json` 的 `mcpServers`：

- `jcodemunch`（指向 `jcodemunch-mcp.exe` / `.cmd`）
- `repomix`（指向 `repomix.exe` / `.cmd`）
- `headroom`（指向 `headroom.exe` / `.cmd`）

**关键差异**（[F] 来自本机 `.mcp.json` 实测）：
- **Cursor IDE** schema：`mcpServers.<name>.{command, args}` （**无** `type` 字段）
- **ZCode 桌面版** schema：`mcp.servers.<name>.{type: "stdio", command, args}`

**保留策略**：用 `setdefault` 保留所有顶层字段和用户已有 server（如 `drawio`），仅强制覆写 3 个 LoopEngine 自己的 key。原子写（`.tmp` + `os.replace`）。

## 验证

开新 AI 会话后发送：

```
"告诉我 LoopEngine 的核心价值，并列出 orch 调度的 5 类复合任务"
```

期望：
- 解释出 "loop + go + orch 多技能编排" 核心价值
- 列出 orch 的 5 类（调研+决策 / 分析+建议 / 诊断+修复 / 设计+实现 / 并行调研）

自动安装验证：

```bash
# 1. 自检通过
bash install.sh --dry-run

# 2. 检查 9 工具 skill 部署
ls ~/.zcode/skills/loopengine/skills/orch/   # ZCode 用户级
ls ~/.cursor/skills/loopengine/skills/orch/ # Cursor

# 3. 检查 Cursor MCP 合并
cat ~/.cursor/mcp.json                       # 4 server: drawio + jcodemunch + repomix + headroom

# 4. 检查 7 红线注入
grep "LOOPENGINE-MANAGED" ~/.zcode/AGENTS.md # 7 sentinel markers

# 5. 检查版本号
cat ~/.loopengine/.installed_version         # 1.3.0
```

## 故障排查

| 现象 | 解决 |
|------|------|
| `git clone` 失败 | 检查网络/VPN；可手动下载 ZIP 解压后跑 `bash install.sh` |
| `pip install` 失败 | 先 `pip install --upgrade pip`；用 `python -m pip install --user <pkg>` 替代 |
| `npm install -g` 失败 | 检查 Node.js；Linux/macOS 上需要 sudo 或 `npm config set prefix` |
| 装完 ZCode 还是看不到 loopengine 技能 | 重跑 `bash install.sh`（覆盖所有目标目录） |
| **ZCode MCP 工具不显示** | 检查 `cat ~/.zcode/cli/config.json` 是否有 `mcp.servers` 三个 server；缺失就重跑 `bash install.sh` |
| **Cursor MCP 工具不显示**（v1.3.0 新增） | 检查 `cat ~/.cursor/mcp.json` 是否有 3 server（jcodemunch/repomix/headroom）；缺失就重跑 `bash install.sh --force`（确保 `--all` 或 detect 到 cursor） |
| MCP 工具显示了但调用失败 | 命令路径要带 Windows 扩展名（`jcodemunch-mcp.exe` / `repomix.cmd` / `headroom.exe`），install.sh 已自动处理 |
| 想强制重装最新版本 | `rm ~/.loopengine/.installed_version && bash install.sh` |
| **v1.3.0 detect 没识别某个工具** | 用 `bash install.sh --only=zcode,cursor --force` 显式指定；或用 `--all` 强制全量 |

## 设计哲学

- **不依赖** ZCode 内部 `marketplace.json` / `.zcode-plugin/plugin.json` 注册（v2.0 重构后）
- **不重启** AI 工具即可生效（直接 cp 到约定目录）
- **不重复造轮子**：每个工具的"内部机制"对我们是黑盒；只关心"约定目录"
- **覆盖 7 AI 工具**（ZCode + Claude Code + Codex + Gemini + Cursor + Copilot + Pi）+ ZCode 桌面版/内置包/CLI 缓存 3 路径；Kimi/OpenCode 走各自平台原生命令
- **单一真源**：plugin manifest 改版本号 = 改 `.plugin-template.json` 的 `version` 字段（6 个 overlay 自动同步）
- **v1.3.0+ 自动感知**：默认只给本机已装工具部署；显式 `--all` / `--only` 可覆盖
- **v1.3.1 三平台合一**：3 平台脚本从 ~145 → ~18 行（-87%），共享 `common_run_platform_steps` 主驱动

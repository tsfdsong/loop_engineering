# LoopEngine 安装指南

> **v1.2.6（2026-07-01）**— 路径平铺修复（v1.2.5 plugin 命名空间导致 ZCode 找不到技能）
> **v1.2.2** — install.sh 一体化 + Cursor 完整兼容（7 红线 + 9 工具）
> 历史指南见 [docs/legacy/](./legacy/)。

## 一行安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

**装完即用**。无需重启 AI 工具，无需懂任何目录约定。

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
| `bash install.sh` | 智能模式（默认） |
| `bash install.sh --force` | 跳过 5 秒等待，强制重装 |
| `bash install.sh --dry-run` | 只检查版本不实际安装 |
| `bash install.sh -h` | 显示帮助 |

## 它做了什么（v1.1.0 全面同步 · v1.2.0 一体化 · v1.2.2 Cursor 兼容 · v1.2.6 路径平铺）

| 步骤 | 行为 |
|------|------|
| 0️⃣ 版本自检 | 读 `~/.loopengine/.installed_version`，已装同版本则 5 秒等待 |
| 1️⃣ 拉源码 | `git clone --depth 1` 到 `/tmp/loopengine-install-$$/`，自动清理 |
| 2️⃣ 部署（6 子步） | **2a** 渲染 7 plugin manifest（去 _comment，version 同步）<br>**2b-pre** 清理 v1.2.5 遗留的 plugin 命名空间（旧 `~/.claude/skills/loopengine/` 等）<br>**2b-1** 平铺 skills 到 6 个 Skills 全局加载工具（Claude/Codex/Cursor/Pi/Copilot/ZCode 用户级）<br>**2b-2** 复制 skills 到 3 个 plugin 命名空间工具（Gemini/内置包/ZCode CLI cache）<br>**2c** 复制 `hooks/` 到 3 个 plugin 目标<br>**2d** 部署 plugin manifest 到 3 个 plugin 目标 + Claude marketplace + **ZCode enabledPlugins 注册**<br>**2e** 复制 `AGENTS.md` + `README.md` 到 3 个 plugin 目标 |
| 3️⃣ MCP 三件套 | `pip install --user jcodemunch-mcp headroom` + `npm i -g repomix`（已装会跳过） |
| 4️⃣ ZCode 桌面版 MCP | 自动写入 `~/.zcode/cli/config.json` 的 `mcp.servers`（**v1.0 根因**：桌面版真正入口） |
| 5️⃣ 7 条红线 | 把 AGENTS.md 的 7 条 🔴 红线章节注入 7 个工具的**用户级**规则文件（sentinel markers，幂等；v1.2.2 扩展自 5 条） |
| 6️⃣ 自检 | 验证关键路径 + manifest 数 + 写入 `~/.loopengine/.installed_version` |

### 同步目标一览（v1.0 → v1.2 扩展 8.5 倍）

| 类别 | v1.0.2 路径数 | v1.2.2 路径数 | 增量 |
|------|:---:|:---:|------|
| skills/ | 8 | 9 | **+1**（v1.2.2 加 Cursor） |
| hooks/ | 0 | 9 | **+9** |
| AGENTS.md | 0 | 9 | **+9** |
| README.md | 0 | 9 | **+9** |
| plugin manifest | 0 | 7 | **+7**（v1.2.2 加 Cursor plugin.json） |
| ZCode 桌面版 MCP | 1 | 1 | — |
| 7 条红线注入 | 7 | 7 | —（注入目标数不变；每文件 5 → 7 条规则块） |
| 版本号文件 | 0 | 1 | **+1** |
| **合计** | **16** | **52** | **+36** |

## 9 工具部署目标（v1.2.6 平铺模式 · v1.2.2 加 Cursor）

### 平铺目标（6 项 · 技能作为 root_dir 子目录 · v1.2.6 新设计）

适用工具的 Skills 全局加载机制 = 平铺 `<root>/<skill_name>/SKILL.md`：

| AI 工具 | 约定路径 | 加载方式 |
|---------|---------|---------|
| **ZCode（用户级）** | `~/.zcode/skills/orch/` 等 34 个平铺 | Skills 全局加载（fallback） |
| Claude Code | `~/.claude/skills/orch/` 等 34 个平铺 | Skills 全局加载 |
| Codex | `~/.codex/skills/orch/` 等 34 个平铺 | Skills 全局加载 |
| Cursor | `~/.cursor/skills/orch/` 等 34 个平铺 | Skills 全局加载 |
| GitHub Copilot | `~/.copilot/skills/orch/` 等 34 个平铺 | Skills 全局加载 |
| Pi | `~/.pi/skills/orch/` 等 34 个平铺 | Skills 全局加载 |

### Plugin 命名空间目标（3 项 · 技能在 root_dir/skills/ · 保留 plugin 模式）

| AI 工具 | 约定路径 | 加载方式 |
|---------|---------|---------|
| Gemini CLI | `~/.gemini/extensions/loopengine/skills/orch/` 等 | Plugin manifest |
| ZCode 内置包（Windows） | `~/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin/skills/orch/` 等 | Plugin manifest |
| **ZCode CLI 缓存（v1.2.6 加版本号子目录）** | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/1.2.6/skills/orch/` 等 | Plugin manifest |

> 🟢 **v1.2.6 关键修复**：ZCode CLI cache 路径加 `${COMMON_VERSION}` 子目录。
> 旧 v1.2.5 缺版本号（`.../loopengine/`），导致 ZCode 找不到 plugin。其他 plugin（如 ios-simulator）都有 `0.1.0/` 版本子目录。
>
> 🟢 **v1.2.6 新增**：ZCode enabledPlugins + known_marketplaces 自动注册（v1.2.5 漏了关键一步，即使物理部署了 plugin，ZCode 仍不会加载）。
>
> 🟢 **v1.2.6 路径平铺**：6 个 Skills 工具改为平铺到 `<root>/<skill_name>/`，符合 Skills 全局加载机制。v1.2.5 嵌套 `loopengine/skills/<name>/` 3 层是错的。
>
> 🟢 **Cursor**（v1.2.2）：skills 平铺到 `~/.cursor/skills/orch/` 等，红线注入路径仍为 `~/.cursor/rules/loopengine-interaction.mdc`（互补不冲突）。

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

## 验证

开新 AI 会话后发送：

```
"告诉我 LoopEngine 的核心价值，并列出 orch 调度的 5 类复合任务"
```

期望：
- 解释出 "loop + go + orch 多技能编排" 核心价值
- 列出 orch 的 5 类（调研+决策 / 分析+建议 / 诊断+修复 / 设计+实现 / 并行调研）

## 故障排查

| 现象 | 解决 |
|------|------|
| `git clone` 失败 | 检查网络/VPN；可手动下载 ZIP 解压后跑 `bash install.sh` |
| `pip install` 失败 | 先 `pip install --upgrade pip`；用 `python -m pip install --user <pkg>` 替代 |
| **v1.2.5 → v1.2.6 升级后技能仍找不到** | 检查 `~/.zcode/skills/`（用户级 fallback）是否有 `orch/` 等目录；缺失就 `bash install.sh --force` 重装 |
| **ZCode 桌面版仍不显示 loopengine 技能** | 检查 `cat ~/.zcode/cli/config.json` 的 `plugins.enabledPlugins` 是否有 `loopengine@zcode-plugins-official: true`；缺失就重跑 install.sh（v1.2.6 已自动注册） |
| **ZCode CLI cache 路径找不到** | v1.2.6 起路径变为 `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/1.2.6/`（带版本号子目录）；旧 v1.2.5 无版本号路径已自动清理 |
| `npm install -g` 失败 | 检查 Node.js；Linux/macOS 上需要 sudo 或 `npm config set prefix` |
| 装完 ZCode 还是看不到 loopengine 技能 | 重跑 `bash install.sh`（覆盖所有目标目录） |
| **ZCode MCP 工具不显示** | 检查 `cat ~/.zcode/cli/config.json` 是否有 `mcp.servers` 三个 server；缺失就重跑 `bash install.sh`（v1.1.0 已吸收原 `zcode-mcp-ensure.sh` 功能） |
| MCP 工具显示了但调用失败 | 命令路径要带 Windows 扩展名（`jcodemunch-mcp.exe` / `repomix.cmd` / `headroom.exe`），install.sh 已自动处理 |
| 想强制重装最新版本 | `rm ~/.loopengine/.installed_version && bash install.sh` |

## 设计哲学

- **不重启** AI 工具即可生效（直接 cp 到约定目录）
- **不重复造轮子**：每个工具的"内部机制"对我们是黑盒；只关心"约定目录"
- **覆盖 9 大 AI 工具**（ZCode + Claude Code + Codex + Gemini + Cursor + Copilot + Pi + ZCode 桌面版/内置包/CLI 缓存）
- **单一真源**：plugin manifest 改版本号 = 改 `.plugin-template.json` 的 `version` 字段（6 个 overlay 自动同步）
- **v1.2.6 修正**：依赖 ZCode `enabledPlugins` + `known_marketplaces` 注册（v1.2.5 漏了关键一步；v1.2.6 自动注册）

## v1.2.6 Release Notes（2026-07-01 · 路径平铺修复）

### 关键 bug（v1.2.5 → v1.2.6 必须升级）

v1.2.5 install.sh 把 skills 装到 `~/.claude/skills/loopengine/skills/orch/` 这种 3 层嵌套路径，
**用户视角** `~/.claude/skills/orch/` 是空的找不到技能，**ZCode 视角** enabledPlugins 没注册也找不到 plugin。

v1.2.6 修复：

1. **路径平铺（6 个 Skills 工具）**：技能直接作为 root_dir 子目录
   - `~/.claude/skills/orch/` 等（v1.2.5 是 `~/.claude/skills/loopengine/skills/orch/`）
   - 适用：Claude Code / Codex / Cursor / Pi / Copilot / ZCode 用户级
2. **ZCode CLI cache 加版本号子目录**：`.../loopengine/1.2.6/skills/orch/`（v1.2.5 无版本号）
3. **新增 ZCode enabledPlugins + known_marketplaces 注册**（v1.2.5 漏了关键一步）
4. **plugin 模式 3 工具保留**（Gemini / ZCode 内置包 / ZCode CLI 缓存）
5. **自动清理 v1.2.5 遗留的旧 plugin 命名空间**（`~/.claude/skills/loopengine/` 等）

### 升级方法

```bash
# 方式 1: 智能模式（推荐）
bash install.sh

# 方式 2: 强制重装（如果智能模式检测同版会等 5 秒）
bash install.sh --force

# 方式 3: 卸载旧版再装（彻底清理 v1.2.5 残留）
rm -rf ~/.zcode/skills/loopengine ~/.claude/skills/loopengine \
       ~/.codex/skills/loopengine ~/.copilot/skills/loopengine \
       ~/.pi/skills/loopengine ~/.cursor/skills/loopengine \
       ~/.gemini/extensions/loopengine \
       '~/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin' \
       ~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine
rm ~/.loopengine/.installed_version
bash install.sh --force
```

### 验证

升级后检查：

```bash
# 1) 平铺目标 — 技能应直接作为 root_dir 子目录
ls ~/.claude/skills/orch/      # 应有 SKILL.md
ls ~/.cursor/skills/clean-code/  # 应有 SKILL.md

# 2) ZCode CLI cache — 应有版本号子目录
ls ~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/1.2.6/

# 3) ZCode enabledPlugins — loopengine 应已注册
cat ~/.zcode/cli/config.json | python3 -c "import json,sys; print(json.load(sys.stdin)['plugins']['enabledPlugins'])"
# 应输出: {'loopengine@zcode-plugins-official': True, ...}

# 4) ZCode known_marketplaces — zcode-plugins-official 应已注册
cat ~/.zcode/cli/plugins/known_marketplaces.json | python3 -c "import json,sys; print([m['id'] for m in json.load(sys.stdin)['marketplaces']])"
# 应输出: ['claude-plugins-official', 'zcode-plugins-official']
```

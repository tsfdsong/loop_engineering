# LoopEngine 安装指南

> v1.1.0（2026-07-01）— install.sh 全量同步 7 工具（skills/hooks/AGENTS/plugin manifest/5 红线）。
> 历史指南见 [docs/legacy/](./legacy/)。

## 一行安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

**装完即用**。无需重启 AI 工具，无需懂任何目录约定。

## 更新

```bash
bash <(curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/update.sh)
```

`update.sh` v1.1.0 重构为"自愈入口"：拉最新 main → 比对版本 → 转发到 install.sh。`--dry-run` 模式只检查不安装。

## 它做了什么（v1.1.0 全面同步）

| 步骤 | 行为 |
|------|------|
| 0️⃣ 版本自检 | 读 `~/.loopengine/.installed_version`，已装同版本则 5 秒等待 |
| 1️⃣ 拉源码 | `git clone --depth 1` 到 `/tmp/loopengine-install-$$/`，自动清理 |
| 2️⃣ 部署（5 子步） | **2a** 渲染 6 plugin manifest（去 _comment，version 同步）<br>**2b** 复制 `skills/` 到 8 个目标<br>**2c** 复制 `hooks/` 到 8 个目标<br>**2d** 部署 6 个 `plugin.json` / `marketplace.json` / `gemini-extension.json`<br>**2e** 复制 `AGENTS.md` + `README.md` 到 8 个目标 |
| 3️⃣ MCP 三件套 | `pip install --user jcodemunch-mcp headroom` + `npm i -g repomix`（已装会跳过） |
| 4️⃣ ZCode 桌面版 MCP | 自动写入 `~/.zcode/cli/config.json` 的 `mcp.servers`（**v1.0 根因**：桌面版真正入口） |
| 5️⃣ 5 条红线 | 把 AGENTS.md 的 5 条 🔴 红线章节注入 7 个工具的**用户级**规则文件（sentinel markers，幂等） |
| 6️⃣ 自检 | 验证关键路径 + manifest 数 + 写入 `~/.loopengine/.installed_version` |

### 同步目标一览（v1.0 → v1.1 扩展 6.7 倍）

| 类别 | v1.0.2 路径数 | v1.1.0 路径数 | 增量 |
|------|:---:|:---:|------|
| skills/ | 8 | 8 | — |
| hooks/ | 0 | 8 | **+8** |
| AGENTS.md | 0 | 8 | **+8** |
| README.md | 0 | 8 | **+8** |
| plugin manifest | 0 | 6 | **+6** |
| ZCode 桌面版 MCP | 1 | 1 | — |
| 5 条红线注入 | 7 | 7 | — |
| 版本号文件 | 0 | 1 | **+1** |
| **合计** | **16** | **47** | **+31** |

## 7 工具部署目标

| AI 工具 | 约定路径 |
|---------|---------|
| **ZCode（用户级）** | `~/.agents/skills/`（fallback） |
| Claude Code | `~/.claude/skills/loopengine/` |
| Codex | `~/.codex/skills/loopengine/` |
| Gemini CLI | `~/.gemini/extensions/loopengine/skills/` |
| GitHub Copilot | `~/.copilot/skills/loopengine/` |
| Pi | `~/.pi/skills/loopengine/` |
| ZCode 内置包（可选） | `~/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin/` |
| ZCode CLI 缓存（可选） | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/` |

> 🟢 ZCode 用户级 fallback 是关键 — 即使其他 ZCode 内部插件路径不动，技能也能加载。

## 全局红线注入（Step 5）

`install.sh` 自动把 AGENTS.md 中的 5 条 🔴 红线章节注入到 7 个 AI 工具的**用户级**规则文件：

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
- **自动同步**：`update.sh` 重跑时规则自动更新

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
| `npm install -g` 失败 | 检查 Node.js；Linux/macOS 上需要 sudo 或 `npm config set prefix` |
| 装完 ZCode 还是看不到 loopengine 技能 | 重跑 `bash install.sh`（覆盖所有目标目录） |
| **ZCode MCP 工具不显示** | 检查 `cat ~/.zcode/cli/config.json` 是否有 `mcp.servers` 三个 server；缺失就重跑 `bash install.sh`（v1.1.0 已吸收原 `zcode-mcp-ensure.sh` 功能） |
| MCP 工具显示了但调用失败 | 命令路径要带 Windows 扩展名（`jcodemunch-mcp.exe` / `repomix.cmd` / `headroom.exe`），install.sh 已自动处理 |
| 想强制重装最新版本 | `rm ~/.loopengine/.installed_version && bash install.sh` |

## 设计哲学

- **不依赖** ZCode 内部 `marketplace.json` / `.zcode-plugin/plugin.json` 注册（v2.0 重构后）
- **不重启** AI 工具即可生效（直接 cp 到约定目录）
- **不重复造轮子**：每个工具的"内部机制"对我们是黑盒；只关心"约定目录"
- **覆盖 7 大 AI 工具**（ZCode + Claude Code + Codex + Gemini + Copilot + Pi + ZCode 桌面版/内置包/CLI 缓存）
- **单一真源**：plugin manifest 改版本号 = 改 `.plugin-template.json` 的 `version` 字段（6 个 overlay 自动同步）

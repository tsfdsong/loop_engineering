# LoopEngine 安装指南（极简版）

> **本指南替代** `docs/zcode-install-guide.md` + `docs/mcp-setup-guide.md` 两个旧文档。

## 一行安装

```bash
curl -fsSL https://raw.githubusercontent.com/tsfdsong/loop_engineering/main/install.sh | bash
```

**装完即用**。无需重启 AI 工具，无需懂任何目录约定。

---

## 它做了什么

| 步骤 | 行为 |
|------|------|
| 1️⃣ 拉源码 | `git clone --depth 1` 到 `/tmp/loopengine-install-$$/`，自动清理 |
| 2️⃣ 复制技能 | 把 `skills/*` 复制到 AI 工具的**约定技能目录**（见下表） |
| 3️⃣ MCP | 用 pip/npm 装 jcodemunch-mcp / headroom / repomix（已装会跳过） |

### 自动部署的目标目录

| AI 工具 | 约定路径 |
|---------|---------|
| **ZCode（用户级）** | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/loopengine/` |
| Codex | `~/.codex/skills/loopengine/` |
| Gemini CLI | `~/.gemini/extensions/loopengine/skills/` |
| GitHub Copilot | `~/.copilot/skills/loopengine/` |
| Pi | `~/.pi/skills/loopengine/` |
| ZCode 内置包（可选） | `~/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin/skills/` |
| ZCode CLI 缓存（可选） | `~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/skills/` |

> 🟢 **ZCode 用户级 fallback（`~/.agents/skills/`）是关键** — 即使其他 ZCode 内部插件路径不动，技能也能加载。

---

## 更新

**更新 = 重新安装**：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/tsfdsong/loop_engineering/main/update.sh)
```

或本地项目内：

```bash
bash update.sh      # = git pull + exec install.sh
```

---

## 验证

开新 AI 会话后发送：

```
"告诉我 LoopEngine 的核心价值，并列出 skill-hub 调度的 5 类复合任务"
```

期望：
- 解释出 "loop + go + skill-hub 闭环开发引擎" 核心价值
- 列出 v6.0 Orchestrator 的 5 类（调研+决策 / 分析+建议 / 诊断+修复 / 设计+实现 / 规划+并行）

如果 MCP 工具（jcodemunch / repomix / headroom）不显示，按需运行：

```bash
bash scripts/zcode-mcp-ensure.sh
```

---

## 旧系统参考（仅迁移时查阅）

| 旧命令 | 等价新做法 |
|--------|----------|
| `bash install.sh` | 直接一行 curl（每行等于一次 install） |
| `bash install.sh --update` | `bash update.sh` |
| `bash update.sh` | 同上 |
| `bash scripts/zcode-mcp-ensure.sh` | 仅当 MCP 工具不显示时跑 |

---

## 设计哲学

- **不依赖** ZCode 内部 `marketplace.json` / `.zcode-plugin/plugin.json` 注册
- **不重启** AI 工具即可生效（直接 cp 到约定目录）
- **不重复造轮子**：每个工具的"内部机制"对我们是黑盒；只关心"约定目录"
- **覆盖 6 大 AI 工具**（ZCode + Claude Code + Codex + Gemini + Copilot + Pi）

---

## 故障排查

| 现象 | 解决 |
|------|------|
| `git clone` 失败 | 检查网络/VPN；可手动下载 ZIP 解压后跑 `bash install.sh` |
| `pip install` 失败 | 先 `pip install --upgrade pip`；用 `python -m pip install --user <pkg>` 替代 |
| `npm install -g` 失败 | 检查 Node.js；Linux/macOS 上需要 sudo 或 `npm config set prefix` |
| 装完 ZCode 还是看不到 loopengine 技能 | 跑 `bash scripts/zcode-mcp-ensure.sh`（加载 marketplace + plugin.json） |
| MCP 工具不显示 | 同上 |

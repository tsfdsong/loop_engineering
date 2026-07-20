# Design: Plugin-Shaped Install（对齐 Superpowers 整包形态）

> **日期**: 2026-07-20  
> **状态**: Draft · 待用户审阅后进入 writing-plans  
> **来源**: `/brainstorming` 会话决策  

## 1. 问题陈述

当前 `install.sh` / `install.ps1` 能把 LoopEngine 装到多工具，但形态不统一：

- **Cursor** 为兼容扫描，把 32 个 skill **平铺**到 `~/.cursor/skills/<name>/`，与用户自有 skill 混名、升级易漏件、卸载困难。
- ZCode / Claude 虽有 `~/.…/skills/loopengine/` 中间层，仍主要是「文件拷贝」，**未完整走各工具官方插件注册表**（Claude 缺少 `installed_plugins.json` 条目）。
- 缺少统一的 **install / upgrade / uninstall** 清单，无法像官方插件一样干净启停。

**目标**：不依赖官方 `/plugin install` 命令，仅用自有脚本达到 **Superpowers 式插件管理效果**——整包 skills + hooks + commands，被工具识别启用，可统一升级与卸载。

**非目标**：不强求上架官方 marketplace；不改 skill 业务内容；不删除用户非 LoopEngine 资产。

## 2. 已确认决策

| # | 决策 | 选择 |
|---|------|------|
| D1 | 优先目标 | 插件形态对齐 Superpowers（整包识别启用） |
| D2 | 改造范围 | install 支持的**全部**工具一起改 |
| D3 | Cursor 策略 | 走官方 **plugins** 路径，**不再**平铺 `~/.cursor/skills/` |
| D4 | 生命周期 | 完整 **install / upgrade / uninstall** |
| D5 | 架构方案 | **A**：中央物理包 + 各工具 Adapter 注册 |
| D6 | Claude | **必须**写入官方 `installed_plugins.json`（及配套 local marketplace） |

否决备选：

- **B**（各工具独立整包无中央源）— 多份拷贝易漂移，无法解决漏升/难卸。
- **C**（纯 git marketplace 指向）— 各工具 registry 差异大，首版过重。
- Cursor symlink 回平铺 — 与 D3 冲突，命名空间问题仍在。

## 3. 架构总览

```
~/.loopengine/
├── .installed_version
├── install-manifest.json          # 卸载/升级真源
└── plugins/
    └── loopengine/
        └── <version>/             # 中央物理包（单一内容真源）
            ├── skills/
            ├── hooks/
            ├── commands/
            ├── .claude-plugin/
            ├── .zcode-plugin/
            ├── .cursor-plugin/
            ├── .codex-plugin/
            ├── AGENTS.md
            └── README.md
```

流程：

1. `ensure_central_package(version)` — 渲染 manifests，写入中央包  
2. 各 `Adapter.sync + activate` — 链接/拷贝到工具 plugin_root，写注册表  
3. `write_install_manifest()` — 记录路径与 skill 名清单  
4. upgrade / uninstall 只认 manifest  

## 4. Cursor Adapter

### 4.1 目标路径

依据本机官方插件（如 Postman）结构：包根含 `.cursor-plugin/plugin.json`、`skills/`、`commands/` 等，位于 `~/.cursor/plugins/...`。

目标态：

```
~/.cursor/plugins/local/loopengine/  →  symlink 或 rsync 自中央包
```

- **停止**向 `~/.cursor/skills/<skill>/` 写入。  
- macOS/Linux 优先 **symlink**；Windows 若无权限则 **rsync 复制**。

### 4.2 旧平铺迁移

升级/安装时：用中央包 `skills/*` 得到 **LoopEngine skill 名白名单**，删除 `~/.cursor/skills/<name>/` 中命中项；**不删**白名单外目录。并清理半成品 `~/.cursor/skills/loopengine/`（仅 hooks/无 skills 的旧形态）。

### 4.3 Spike 闸门（P0，实现前必过）

最小包放入 `~/.cursor/plugins/local/loopengine/`，新会话验证 skill/hooks 可加载。

- **通过** → 按本节落地  
- **失败** → **阻断**，不默默回退平铺；需重新决策  

## 5. Claude Adapter（含官方注册表 · D6）

### 5.1 物理包

保留/同步整包至约定 plugin 根（与中央包一致内容）。推荐与官方插件同形的 cache 路径之一：

```
~/.claude/plugins/cache/loopengine-local/loopengine/<version>/
```

或继续 `~/.claude/skills/loopengine` 作为 installPath（实现时选一种并在 manifest 固定；**优先 cache 路径以贴近官方**）。

### 5.2 Local marketplace + installed_plugins

脚本必须：

1. 在 `~/.claude/plugins/marketplaces/` 注册本地 marketplace（例：`loopengine-local`），`known_marketplaces.json` 增加条目，`source` 可为 `directory` / 本地 path（以实现时 Claude 实际 schema 为准；spike 验证）。  
2. 将 marketplace 内的 `marketplace.json` 指向 loopengine 插件元数据（复用现有 `.claude-plugin/marketplace.json` 渲染结果）。  
3. 写入 `~/.claude/plugins/installed_plugins.json`：

```json
"loopengine@loopengine-local": [
  {
    "scope": "user",
    "installPath": "<absolute plugin root>",
    "version": "<semver>",
    "installedAt": "<iso8601>",
    "lastUpdated": "<iso8601>"
  }
]
```

4. Uninstall 时移除该 key，并清理 marketplace 条目（若仅服务 LoopEngine）。

### 5.3 与现有 ZCode 注册的关系

ZCode 已有 `register_zcode_marketplace.py` / `register_zcode_plugin.py`。Claude 侧新增对等脚本（例：`register_claude_marketplace.py` / `register_claude_plugin.py`），schema 对齐 Claude `known_marketplaces.json` + `installed_plugins.json`（version: 2, plugins map）。

## 6. 其它工具 Adapter

统一契约：

```
ensure_central_package()
→ sync_plugin_root(tool)
→ write_tool_manifest()
→ activate_if_needed()
→ record_manifest_component()
```

| 工具 | plugin_root（目标） | activate |
|------|---------------------|----------|
| Cursor | `~/.cursor/plugins/local/loopengine` | local plugins 发现 + §4 |
| Claude Code | cache 或 skills/loopengine（§5 固定） | **installed_plugins.json**（必须） |
| ZCode | `~/.zcode/skills/loopengine` | 现有 marketplace + enabledPlugins |
| Codex | `~/.codex/skills/loopengine` | plugin.json overlay |
| Gemini | `~/.gemini/extensions/loopengine` | gemini-extension.json |
| Copilot / Pi | `~/.…/skills/loopengine` | 文档级 / AGENTS 注入 |

Windows `install.ps1` 与 bash `_common.sh` **共用** manifest schema 与步骤名。

## 7. install-manifest.json

路径：`~/.loopengine/install-manifest.json`

必填字段：

- `schema_version`, `product`, `version`, `installed_at`, `central_root`  
- `skill_names[]` — 卸载/清平铺白名单  
- `components.<tool>.{plugin_root, link_mode?, activated?, registry_keys?}`  
- `extras.redlines[]`, `extras.mcp.{cursor,keys}`  

Claude 组件额外记录：`marketplace_id`, `installed_plugins_key`（如 `loopengine@loopengine-local`）。

## 8. 生命周期语义

| 命令 | 行为 |
|------|------|
| `install.sh`（默认） | 未装→install；同版→提示/`--force`；旧版→upgrade |
| `--upgrade` | 新 version 中央包 → 刷新 Adapter → 更新 manifest → 删旧 version 目录 → Cursor 清平铺 |
| `--uninstall` | 按 manifest 删除中央包、各 plugin_root、Cursor 白名单平铺、Claude/ZCode 注册表条目、红线 sentinel 块；MCP 仅移除 LE 写入的 key |
| `--force` | 同版重装 |

**不删**：用户自有 skill、非 LE MCP server、未入清单路径。

## 9. 验收标准

1. 新装后 `~/.cursor/skills/` 无 LoopEngine skill 目录；`plugins/local/loopengine/skills/` 存在。  
2. Claude `installed_plugins.json` 含 `loopengine@…` 且 `installPath` 可读、含 skills。  
3. 升级后 version / 中央包 / 各 plugin_root 一致。  
4. 卸载后 manifest 路径与注册 key 消失；用户自有资产保留。  
5. ZCode / Claude / Cursor 会话可加载 `go` 或 `loop`（spike + 手工抽检）。  
6. macOS 与 Windows 脚本子命令与 manifest 字段一致。

## 10. 实现分期

| 阶段 | 内容 | 闸门 |
|------|------|------|
| **P0** | Cursor `plugins/local` spike；Claude marketplace + installed_plugins spike | 两者都通过才进 P1 |
| **P1** | 中央包 + manifest + Cursor Adapter + 旧平铺清理 | 验收 §9.1 |
| **P2** | Claude 官方注册 + 其余工具改「从中央包同步」+ uninstall | 验收 §9.2–9.4 |
| **P3** | INSTALL/README 更新；`--dry-run` 打印目标态；audit 维度增加「registry 一致」 | 文档与自检 |

## 11. 风险

| 风险 | 缓解 |
|------|------|
| Cursor local 不加载 | P0 spike 失败则停 |
| Claude local marketplace schema 与假设不符 | P0 对照官方插件条目 spike；必要时调整 installPath 到 cache |
| 误删用户同名 skill | 仅删 `skill_names` 白名单 |
| Windows symlink | 回退复制 |
| 双脚本漂移 | 共享 Python helper 写 manifest / 注册表 |

## 12. 文档与测试影响

- 更新 `docs/INSTALL.md`、`README.md`：删除「Cursor 扁平」说明；增加 `--uninstall`；验证步骤改为检查 `plugins/local` 与 Claude `installed_plugins`。  
- 新增/扩展 tests：manifest round-trip、Cursor 不再调用 flat copy、Claude registry write/remove、uninstall 幂等。

## 13. 开放实现细节（plan 阶段锁定，不阻塞本设计）

- Claude `installPath` 最终选 `plugins/cache/...` 还是 `skills/loopengine`（P0 spike 决定，写入 plan）。  
- Cursor 是否还需写额外 enable 配置文件（若 local 目录即足够则不做）。  
- 旧版无 manifest 的机器：uninstall 提供「启发式清理」模式（按已知路径 + skill 名列表），首次 upgrade 生成 manifest。

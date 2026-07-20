# Design: Plugin-Shaped Install v2.1（简化修订）

> **日期**: 2026-07-20  
> **状态**: Draft · 待用户审阅后 Approved  
> **取代**: v2 原稿同路径（本文件即为现行真源）；v1 见 `docs/2026-07-20-plugin-shaped-install-design.md`  
> **修订动机**: 对照核心目的审查后全面简化——抬一键生命周期与官方插件四件套，砍 ECC 运维表面积  
> **路径说明**: 落在 `docs/` 以便主仓版本化。

## 0. 核心目的（验收北极星）

一键脚本完成 **安装 / 更新 / 升级 / 卸载**；按各 AI Agent **官方插件模式** 管理并加载：

| 配置面 | 要求 |
|--------|------|
| skills / hooks / commands | 整包进官方 plugin 路径，可被工具发现 |
| MCP | 合并 LE 管理的 server keys，可逆 |
| AGENTS.md（及等价规则） | marker 注入，可逆 |
| 插件注册表 | 有官方 registry 则写入（Claude / ZCode 等） |

**一句话架构**：一个 `install.py` → 一个中央包 → 每工具一个 Adapter（四件套）→ 一份 manifest → 默认装/升、显式卸。

## 1. 问题陈述

当前 Bash/PS 双轨安装能部署多工具，但：

- Cursor skill **平铺**，非官方插件形态；Claude 缺 `installed_plugins.json`。
- 升级易漏件、卸载靠猜路径；macOS/Windows 逻辑双份漂移。
- MCP / AGENTS 注入与「拷贝 skills」脱节，不成统一生命周期。

**目标**：Python 单一运行时 + 官方插件路径 + 可逆生命周期，满足 §0。

**非目标**：上架官方 marketplace；引入 Node；改 skill 业务内容；删用户非 LE 资产；改造 `hooks/` 运行时 shell；首版做完整运维套件（doctor/repair 独立产品化）；首版多版本 rollback。

## 2. 已确认决策

| # | 决策 | 选择 |
|---|------|------|
| D1 | 优先目标 | 官方插件形态管理 skills/hooks/MCP/AGENTS |
| D2 | 工具范围 | **Tier 分期**（见 §6）：先 Tier-1，再 Tier-2/3 |
| D3 | Cursor | `~/.cursor/plugins/local/loopengine`；**禁止**平铺 |
| D4 | 生命周期 | 一键 **install（含智能升级）/ uninstall**；`upgrade` 仅为别名 |
| D5 | 架构 | 中央物理包 + Adapter 四件套 |
| D6 | Claude | **必须** `installed_plugins.json` + local marketplace |
| D7 | 运行时 | Python only（`install.py` → `loopengine_install`） |
| D8 | ECC 借鉴 | **精简纳入**（见 §3），非整包照搬 |
| D9 | Shell | 安装路径零业务 Shell/PS；删除 `_common.sh` 与平台 `.sh` |
| D10 | 入口 | **唯一 `install.py`**；删除 `install.sh` / `install.ps1` |
| **D11** | 用户 CLI | **三命令心智**；运维能力延后或压成 flag |
| **D12** | 真源 | **仅** `install-manifest.json`（取消 `.installed_version` 双真源） |

否决备选：Bash/PS 双轨；双入口薄壳；首版 7 子命令运维套件；全工具同迭代假拉齐；Node 运行时。

## 3. ECC 借鉴（精简）

| # | 借鉴 | 首版态度 |
|---|------|----------|
| 1 | Operation 级状态 | **要**：manifest 含 `operations[]`，由 Adapter **自动生成** |
| 2 | doctor / repair | **延后 P3**；首版用 `install --check` / `install --force` 近似 |
| 3 | 统一命名空间 `loopengine` | **要** |
| 4 | `--dry-run` + `--json` | **要**（挂在 install/uninstall 上，不单开 `plan` 命令） |
| 5 | Harness 能力矩阵 | **轻量**：写入 `docs/INSTALL.md` 一小节；不单独交付大文档 |
| 6 | 单入口可测运行时 | **要**（Python） |
| 7 | JSON Schema | **要**：单一 `schemas/install-manifest.schema.json` |

## 4. 入口与运行时

### 4.1 唯一入口

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
# Windows: curl …/install.py | python
# Fallback: curl … -o install.py && python3 install.py
# 已有源码树: python3 install.py [install|uninstall|upgrade] [flags]
```

`install.py` 职责（短小）：校验 Python `>= 3.10` → clone/更新源码到约定目录 → 调 `loopengine_install`。  
无合格 Python → 非 0 退出并打印指引；**不**回退 Shell。

### 4.2 删除资产

`install.sh`、`install.ps1`、`scripts/install/_common.sh`、`macos.sh`、`linux.sh`、`windows.sh`。

### 4.3 模块布局（合并精简）

```
install.py                         # 唯一用户入口
scripts/loopengine_install/
├── __main__.py / cli.py           # 参数解析 → lifecycle
├── lifecycle.py                   # install / uninstall 编排
├── ops.py                         # Operation apply/revert + manifest IO + schema 校验
├── package.py                     # 构建/切换中央包
├── detect.py                      # 本机 agent / MCP 可执行探测
└── adapters/
    ├── base.py                    # 四件套抽象
    ├── cursor.py / claude.py / zcode.py   # Tier-1
    ├── codex.py / gemini.py               # Tier-2
    └── copilot.py / pi.py                 # Tier-3
schemas/install-manifest.schema.json
```

现有 `render_plugins.py`、`merge_mcp_config.py`、`register_zcode_*.py`、`inject_rules.py`：由 Adapter / package **调用或迁入**，不再经 Shell 编排。

## 5. 用户 CLI（三命令心智）

```text
install.py                → install（默认：未装则装，旧版则升，同版提示/--force）
install.py uninstall      → 按 manifest 逆序卸载
install.py upgrade        → install 的显式别名

flags（挂在上述命令上）:
  --dry-run --json --force --all --only=cursor,zcode,claude
  --check                 → 只体检（P3 可升格为 doctor；首版可选实现）
```

**首版不提供**独立子命令：`plan` / `doctor` / `repair` / `list`（P3 按需加；功能用 flags 覆盖常见需求）。

## 6. 工具 Tier（分期，替代假拉齐）

| Tier | 工具 | 行为 |
|------|------|------|
| **1 原生插件** | Cursor、Claude、ZCode | 官方 plugin 路径 + registry + 四件套全做 |
| **2 半插件** | Codex、Gemini | 整包目录 + 工具自有 plugin/extension 元数据 |
| **3 注入型** | Copilot、Pi | skills 目录（若适用）+ AGENTS 注入；不假装完整 marketplace |

**实现顺序**：P0 spike（Cursor local + Claude registry）→ P1 Tier-1 闭环 → P2 Tier-2/3 + 删旧 Shell → P3 运维增强与文档打磨。

默认 `install`：detect 本机已装工具并部署；`--only` / `--all` 覆盖。

## 7. 中央包

```
~/.loopengine/
├── install-manifest.json          # 唯一真源（D12）
└── plugins/
    └── loopengine/
        ├── current -> <version>/  # 或原子目录切换；不维护复杂多版本浏览
        └── <version>/
            ├── skills/ hooks/ commands/
            ├── .claude-plugin/ .zcode-plugin/ .cursor-plugin/ .codex-plugin/
            ├── AGENTS.md
            └── README.md
```

升级：构建新 `<version>/` → 切换 `current` → 刷新各 Adapter → 写 manifest → 删除旧 version 目录。  
**非目标**：用户级 rollback CLI。

## 8. Adapter 四件套（一等公民）

每个 Adapter 必须实现（无能力则显式 no-op 并在能力表标注）：

| 方法 | 职责 | 可逆 |
|------|------|------|
| `sync_plugin()` | 中央包 → 工具 plugin_root（symlink 优先，否则 copy） | 删/解链 plugin_root |
| `activate_registry()` | 写官方插件表（Claude installed_plugins、ZCode enabledPlugins 等） | 移除 LE key |
| `merge_mcp()` | 合并 LE MCP keys（Cursor/ZCode 等） | 仅移除 LE keys |
| `inject_agents()` | AGENTS.md / 等价规则 marker 块 | 按 marker 剥离 |

统一编排：

```text
ensure_central_package()
for adapter in selected:
    sync_plugin → activate_registry → merge_mcp → inject_agents
    append operations to manifest
write_manifest()
```

### 8.1 Cursor（Tier-1）

- 目标：`~/.cursor/plugins/local/loopengine`
- 停止平铺 `~/.cursor/skills/<le-skill>/`；升级时按 `skill_names` 白名单清理旧平铺
- MCP：`~/.cursor/mcp.json`（仅 LE keys）
- P0：最小包验证 skill/hooks 可加载；**失败则阻断整计划**，不回退平铺

### 8.2 Claude（Tier-1 · D6）

- Local marketplace + `installed_plugins.json`（`loopengine@loopengine-local`）
- `installPath` 优先官方 cache 形；P0 spike 锁定
- AGENTS / MCP 按 Claude 实际支持面做；无则 no-op

### 8.3 ZCode（Tier-1）

- `~/.zcode/skills/loopengine` 整包
- 复用/迁入现有 marketplace + enabledPlugins 注册逻辑
- MCP + AGENTS 注入纳入同一 uninstall 路径

### 8.4 Tier-2 / Tier-3

按能力表降级实现四件套；文档如实写「半插件 / 注入型」，不承诺与 Cursor 同级体验。

## 9. Manifest 与 Operations

路径：`~/.loopengine/install-manifest.json`  
Schema：`schemas/install-manifest.schema.json`（单一文件）。

概念字段：`schema_version`（= 2）、`product`、`version`、`installed_at`、`central_root`、`skill_names[]`、`components`、`operations[]`。

Operation `kind`（首版仅四种，由 Adapter 生成）：

- `link-or-copy` — plugin 树  
- `registry-write` — 插件表  
- `merge-json` — MCP 等  
- `inject-markers` — AGENTS 等  

uninstall = 对 `ownership=managed` **逆序** revert。  
不删：用户自有 skill、非 LE MCP、未入清单路径。

无 manifest 旧机：首次 install 启发式清理已知 LE 平铺/旧路径后生成 manifest。

## 10. 验收标准（对齐 §0）

1. 唯一入口 `install.py`；无 `install.sh` / `install.ps1` / `scripts/install/*.sh`。  
2. `curl | python3` 完成装或升；`install.py uninstall` 干净卸载。  
3. Cursor：无 LE 平铺 skill；`plugins/local/loopengine` 含 skills/hooks；会话可加载。  
4. Claude：`installed_plugins.json` 含 LE 且 installPath 可读。  
5. ZCode：整包 + registry 一致；卸载可逆。  
6. MCP / AGENTS：安装写入、卸载剥离；用户非 LE 内容保留。  
7. Tier-1 默认 detect 安装；`--only` 可用。  
8. `--dry-run --json` 可机器解析；manifest 通过 schema。  
9. macOS / Windows 同一入口与同一模块；核心路径有 unittest。

## 11. 实现分期

| 阶段 | 内容 | 闸门 |
|------|------|------|
| **P0** | Cursor `plugins/local` spike；Claude registry spike | 双过才进 P1 |
| **P1** | `install.py` + 模块骨架；中央包；Tier-1 四件套；manifest；`--dry-run` | §10.2–10.6（Tier-1） |
| **P2** | Tier-2/3；删全部旧 install Shell/PS；INSTALL/README 改 `curl \| python3` | §10.1、10.7–10.9 |
| **P3** | 可选 `doctor`/`repair`/`list`；`--check` 增强；audit 扩展 | 非阻断 |

Tracer：先打通 **Cursor 四件套垂直切片**，再 Claude、ZCode。

## 12. 风险

| 风险 | 缓解 |
|------|------|
| Cursor local 不加载 | P0 失败则停 |
| Claude schema 不符 | P0 对照官方条目 |
| 误删用户资产 | 白名单 + managed operations |
| Windows symlink | `link-or-copy` 回退 copy |
| `curl \| python` 编码/别名 | 文档强制给出 `-o` fallback；探测 `python`/`python3` |
| 范围回膨胀 | D11/D2 Tier；P3 前不加运维子命令 |

## 13. 文档与测试

- `docs/INSTALL.md` / `README.md`：一键命令、三命令、Tier 表、卸载、Python 依赖。  
- Tests：`ops` apply/revert、manifest schema、各 Tier-1 adapter 注册写删、uninstall 幂等、`install.py` 烟雾。

## 14. 开放细节（plan 锁定）

- Claude `installPath` 最终路径（P0）。  
- Cursor 是否需额外 enable 文件。  
- 中央包用 `current` symlink 还是目录原子替换（Windows 友好优先）。  
- 现有 py helpers 迁入 vs 调用的目录整理粒度。

## 15. 文档关系

- **本文件** = 现行设计真源（v2.1）。  
- v1 design = Superseded。  
- `docs/2026-07-20-plugin-shaped-install-plan.md`（Bash 版）在批准后 **整份重写为 v2.1 plan**。

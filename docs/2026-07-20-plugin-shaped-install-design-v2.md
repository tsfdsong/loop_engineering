# Design: Plugin-Shaped Install v2.3（禁止软链 · Cursor 仅官方插件路径）

> **日期**: 2026-07-20  
> **状态**: **Approved** · 2026-07-20 · 实施计划见 `docs/2026-07-20-plugin-shaped-install-plan.md`  
> **取代**: v2.2 同路径（本文件即为现行真源）；v1 见 `docs/2026-07-20-plugin-shaped-install-design.md`  
> **修订动机**: 对照核心目的审查后全面简化——抬一键生命周期与官方插件四件套，砍 ECC 运维表面积  
> **v2.2**：禁止 symlink；各工具实体拷贝（D13）  
> **v2.3（2026-07-20）**: **撤销** Cursor「双部署平铺」；恢复 D3 = **仅** `plugins/local/loopengine` 真实拷贝，并 **清理** `~/.cursor/skills/<le-skill>/`（对齐 §0 官方插件形态；v2.2 双部署属症状绕过，已废止）  
> **路径说明**: 落在 `docs/` 以便主仓版本化。

## 0. 核心目的（验收北极星）

一键脚本完成 **安装 / 更新 / 升级 / 卸载**；按各 AI Agent **官方插件模式** 管理并加载：

| 配置面 | 要求 |
|--------|------|
| skills / hooks / commands | 整包进官方 plugin 路径，可被工具发现 |
| MCP | 合并 LE 管理的 server keys，可逆 |
| AGENTS.md（及等价规则） | marker 注入，可逆 |
| 插件注册表 | 有官方 registry 则写入（Claude / ZCode 等） |

**一句话架构**：一个 `install.py` → 一份中央真源包 → 每工具 **独立实体拷贝**（禁止软链共享）→ Adapter 四件套 → 一份 manifest → 默认装/升、显式卸。

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
| D3 | Cursor | **仅** `~/.cursor/plugins/local/loopengine` **真实目录**；**禁止** LE 平铺 `~/.cursor/skills/<le-skill>/`（安装时按 `skill_names` 清理） |
| D4 | 生命周期 | 一键 **install（含智能升级）/ uninstall**；`upgrade` 仅为别名 |
| D5 | 架构 | 中央物理包 + Adapter 四件套；**各工具分存，禁止跨目录软链** |
| D6 | Claude | **必须** `installed_plugins.json` + local marketplace |
| D7 | 运行时 | Python only（`install.py` → `loopengine_install`） |
| D8 | ECC 借鉴 | **精简纳入**（见 §3），非整包照搬 |
| D9 | Shell | 安装路径零业务 Shell/PS；删除 `_common.sh` 与平台 `.sh` |
| D10 | 入口 | **唯一 `install.py`**；删除 `install.sh` / `install.ps1` |
| **D11** | 用户 CLI | **三命令心智**；运维能力延后或压成 flag |
| **D12** | 真源 | **仅** `install-manifest.json`（取消 `.installed_version` 双真源） |
| **D13** | 存储 | **禁止 symlink**：中央包 `current` 为 pointer 文件；`sync_plugin` 一律 `copy-tree`（`symlinks=False`） |

否决备选：Bash/PS 双轨；双入口薄壳；首版 7 子命令运维套件；全工具同迭代假拉齐；Node 运行时；中央包软链到各工具目录；工具间共用同一 inode 树。

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

## 7. 中央包（构建真源 · 非运行时共享 inode）

```
~/.loopengine/
├── install-manifest.json          # 唯一真源（D12）
└── plugins/
    └── loopengine/
        ├── current                # **pointer 文本文件**（一行绝对路径）；禁止 symlink
        └── <version>/             # 中央构建产物（真实目录）
            ├── skills/ hooks/ commands/
            ├── .claude-plugin/ .zcode-plugin/ .cursor-plugin/ .codex-plugin/
            ├── AGENTS.md
            └── README.md
```

**铁律（D13）**：

- 中央包只作 **构建与版本切换真源**；**不得**被各工具 `plugin_root` 以 symlink 指向。
- 升级：构建新 `<version>/` → 写 `current` pointer → **对各 Adapter 重新 `copy-tree`** → 写 manifest → 删除旧 version 目录。
- 遗留的 `current` symlink：安装时改写为 pointer 文件。

**非目标**：用户级 rollback CLI；工具间硬链接/符号链接去重。

## 8. Adapter 四件套（一等公民）

每个 Adapter 必须实现（无能力则显式 no-op 并在能力表标注）：

| 方法 | 职责 | 可逆 |
|------|------|------|
| `sync_plugin()` | 中央包 → 本工具独立目录；**一律真实 `copy-tree`（禁止 symlink）** | 删除本工具目录树 |
| `activate_registry()` | 写官方插件表（Claude installed_plugins、ZCode enabledPlugins 等） | 移除 LE key |
| `merge_mcp()` | 合并 LE MCP keys（Cursor/ZCode 等） | 仅移除 LE keys |
| `inject_agents()` | AGENTS.md / 等价规则 marker 块 | 按 marker 剥离 |

统一编排：

```text
ensure_central_package()          # 写 <version>/ + current pointer（非软链）
for adapter in selected:
    sync_plugin → activate_registry → merge_mcp → inject_agents
    append operations to manifest
write_manifest()
```

### 8.0 分工具存储表（各自一份实体树）

| 工具 | 独立存储根（真实目录，禁止指向中央包的软链） |
|------|-----------------------------------------------|
| Cursor | **仅** `~/.cursor/plugins/local/loopengine`（真实目录；禁止软链；禁止 LE 平铺） |
| Claude | cache `…/plugins/cache/loopengine-local/loopengine/<ver>/` + marketplace `…/marketplaces/loopengine-local/plugins/loopengine/` |
| ZCode | `~/.zcode/skills/loopengine` |
| Codex / Gemini / Copilot / Pi | 各 Adapter 约定的本工具目录（同样 copy-tree） |

磁盘占用 = 中央包 ×1 + 已选工具各 ×1（可接受；正确性优先于去重）。

### 8.1 Cursor（Tier-1）

- **Plugin 包（唯一 skills 真源）**：`~/.cursor/plugins/local/loopengine` 为 **真实拷贝**（含 skills/hooks/commands、规范化 `hooks/hooks.json`、`mcp.json`、`rules/`）；安装前删除 `loopengine-spike` 与旧 symlink。
- **禁止平铺**：按 manifest `skill_names` **删除** `~/.cursor/skills/<le-skill>/`；**不得**再双部署。用户自有非 LE skill 保留。
- MCP：`~/.cursor/mcp.json`（仅 LE keys）+ plugin 内 `mcp.json` 同步。
- AGENTS：`~/.cursor/rules/loopengine-interaction.mdc`，并镜像进 plugin `rules/`。
- `--check`：plugin 非 symlink；plugin skill 数量达标；**不得**残留 LE 平铺 skill。
- **发现失败策略**：若 Cursor 仅靠 plugin 仍无法加载全部 skill → **阻断并排查 plugin 发现**（plugin.json / enable / 路径），**禁止**回退平铺（同 v2.1 §8.1）。

### 8.2 Claude（Tier-1 · D6）

- Local marketplace + `installed_plugins.json`（`loopengine@loopengine-local`）
- cache 与 marketplace 均为 **独立 copy-tree**（互不软链、也不链中央包）
- AGENTS / MCP 按 Claude 实际支持面做；无则 no-op

### 8.3 ZCode（Tier-1）

- `~/.zcode/skills/loopengine` **真实整包拷贝**（禁止软链到中央包）
- 复用/迁入现有 marketplace + enabledPlugins 注册逻辑
- MCP + AGENTS 注入纳入同一 uninstall 路径

### 8.4 Tier-2 / Tier-3

按能力表降级实现四件套；文档如实写「半插件 / 注入型」，不承诺与 Cursor 同级体验；存储仍遵守 D13。

## 9. Manifest 与 Operations

路径：`~/.loopengine/install-manifest.json`  
Schema：`schemas/install-manifest.schema.json`（单一文件）。

概念字段：`schema_version`（= 2）、`product`、`version`、`installed_at`、`central_root`、`skill_names[]`、`components`、`operations[]`。

Operation `kind`（由 Adapter 生成）：

- `copy-tree` — 插件/技能目录真实拷贝（**唯一合法树同步方式**；`shutil.copytree(..., symlinks=False)`）  
- `link-or-copy` — **遗留别名**（读旧 manifest 时与 `copy-tree` 同语义；新写入一律用 `copy-tree`）  
- `registry-write` — 插件表  
- `merge-json` — MCP 等  
- `inject-markers` — AGENTS 等  

uninstall = 对 `ownership=managed` **逆序** revert。  
不删：用户自有 skill、非 LE MCP、未入清单路径。

无 manifest 旧机：首次 install 启发式清理已知坏 symlink / 旧 spike 后生成 manifest。

## 10. 验收标准（对齐 §0）

1. 唯一入口 `install.py`；无 `install.sh` / `install.ps1` / `scripts/install/*.sh`。  
2. `curl | python3` 完成装或升；`install.py uninstall` 干净卸载。  
3. Cursor：`plugins/local/loopengine` 为真实目录（非 symlink），含全部 skills/hooks；**无** LE 平铺于 `~/.cursor/skills/`；会话可从 plugin 加载。  
4. Claude：`installed_plugins.json` 含 LE 且 installPath 为真实可读目录。  
5. ZCode：真实整包 + registry 一致；卸载可逆；plugin_root 非 symlink。  
6. MCP / AGENTS：安装写入、卸载剥离；用户非 LE 内容保留。  
7. Tier-1 默认 detect 安装；`--only` 可用。  
8. `--dry-run --json` 可机器解析；manifest 通过 schema。  
9. macOS / Windows 同一入口与同一模块；核心路径有 unittest。  
10. 安装后：`~/.loopengine/plugins/loopengine/current` 为 pointer 文件；各工具 plugin_root **均非**指向中央包的 symlink。

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
| Cursor local 不加载 / 只见单 skill | 真实拷贝 + 删 spike；**禁止**回退平铺；查 plugin 发现与 enable |
| Claude schema 不符 | P0 对照官方条目 |
| 误删用户资产 | 白名单 + managed operations |
| 多份拷贝占盘 | D13 明确可接受；正确性优先 |
| `curl \| python` 编码/别名 | 文档强制给出 `-o` fallback；探测 `python`/`python3` |
| 范围回膨胀 | D11/D2 Tier；P3 前不加运维子命令 |

## 13. 文档与测试

- `docs/INSTALL.md` / `README.md`：一键命令、三命令、Tier 表、卸载、Python 依赖。  
- Tests：`ops` apply/revert、manifest schema、各 Tier-1 adapter 注册写删、uninstall 幂等、`install.py` 烟雾。

## 14. 开放细节（plan 锁定）

- Claude `installPath` 最终路径（P0）— 已采用 cache + marketplace 双真实拷贝。  
- Cursor 是否需额外 enable 文件（plugin-only 发现不全时优先查此项，仍禁止平铺兜底）。  
- ~~中央包 `current` symlink~~ → **已决（D13）**：pointer 文件。  
- ~~Cursor 双部署平铺~~ → **已废（v2.3）**：回归 plugin-only。  
- 现有 py helpers 迁入 vs 调用的目录整理粒度。

## 15. 文档关系

- **本文件** = 现行设计真源（**v2.3**）。  
- v1 design = Superseded。  
- `docs/2026-07-20-plugin-shaped-install-plan.md` 以本文件为准（D3/D13 / §7–§8）。

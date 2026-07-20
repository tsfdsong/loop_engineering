# Design: Plugin-Shaped Install v2（Python 统一运行时）

> **日期**: 2026-07-20  
> **状态**: Draft · 待用户审阅后 Approved  
> **取代**: `docs/2026-07-20-plugin-shaped-install-design.md`（v1 · Bash/PS 双轨）  
> **来源**: `/brainstorming` 会话 · ECC 借鉴点 1–7 + Python 全面重构  
> **路径说明**: `docs/superpowers/` 已被 gitignore；本文件落在 `docs/` 以便主仓版本化。

## 1. 问题陈述

v1 已定义「中央物理包 + 各工具 Adapter + install/upgrade/uninstall」目标，但仍以 Bash `_common.sh` + PowerShell `install.ps1` 双轨承载业务，无法干净落地：

- **双轨漂移**：~3000 行 shell 与 ~700 行 PS 平行逻辑，macOS/Windows 行为易不一致。
- **生命周期偏弱**：无 operation 级状态，难做可靠 uninstall / doctor / repair。
- **插件形态未对齐**：Cursor 仍平铺 `~/.cursor/skills/`；Claude 缺 `installed_plugins.json`。
- **不可测**：安装路径几乎无单元测试；ECC 用单入口 Node + 大量测试证明了另一条路。

**目标**：用 **Python 单一运行时** 实现 Superpowers 式插件管理效果（整包 skills + hooks + commands、可升级可卸载），并纳入 ECC 借鉴点 1–7；用户入口统一为 **`install.py`**（Mac / Windows / Linux 同一条命令）。

**非目标**：不上架官方 marketplace；不引入 Node；不改 skill 业务内容；不删用户非 LoopEngine 资产；**本期不改造** `hooks/` 运行时 shell（仅清 **install 路径** 的 Shell/PS）。

## 2. 已确认决策

| # | 决策 | 选择 |
|---|------|------|
| D1 | 优先目标 | 插件形态对齐 Superpowers（整包识别启用） |
| D2 | 改造范围 | install 支持的**全部**工具一起改 |
| D3 | Cursor 策略 | 官方 **plugins** 路径；**禁止**平铺 `~/.cursor/skills/` |
| D4 | 生命周期 | 完整 **install / upgrade / uninstall** |
| D5 | 架构 | **A**：中央物理包 + 各工具 Adapter |
| D6 | Claude | **必须**写 `installed_plugins.json` + local marketplace |
| **D7** | 运行时 | **Python 单入口**（`python -m loopengine_install`） |
| **D8** | ECC 借鉴 | **1–7 全部纳入**（见 §3） |
| **D9** | Shell 边界 | 安装路径 **零业务 Shell/PS**；删除 `_common.sh` 与平台 `.sh` |
| **D10** | 入口脚本 | **单一 `install.py`**；删除 `install.ps1`；删除/不再维护 `install.sh` |

否决备选：

- Bash/PS 继续承载部署逻辑（双轨漂移）。
- Bash 与 Python 并行 feature-flag 过渡（拖长双轨）。
- 仅「插件同步」进 Python、MCP/红线留 Shell（仍双源）。
- 双入口薄壳 `install.sh` + `install.ps1`（平台习惯重复，无技术必要）。
- 只留 `install.sh`、删 `install.ps1`（仍依赖 Bash）。
- 引入 Node 对齐 ECC（仓库已有 Python helpers，无需新运行时依赖）。
- 本期一并去 `hooks/*.sh`（范围过大，另开会话）。

## 3. ECC 借鉴点（全部纳入）

| # | 借鉴 | LoopEngine 形态 |
|---|------|-----------------|
| 1 | Operation 级 install state | manifest v2 含 `operations[]` |
| 2 | doctor / repair CLI | `loopengine_install doctor` / `repair` |
| 3 | 统一命名空间 | 全局 `loopengine`；禁止 Cursor/Claude 平铺散落 |
| 4 | `--dry-run` + `--json` | `plan` / 各命令支持机器可读输出 |
| 5 | Harness 能力矩阵 | `docs/harness-capability-matrix.md` + audit 校验 |
| 6 | 单入口可测运行时 | **Python**（非 Node） |
| 7 | JSON Schema | `schemas/install-manifest.schema.json` 等 |

与 ECC **刻意差异**：不做 14 harness profile；Cursor 用用户级 `~/.cursor/plugins/local/`（非项目级 `./.cursor/`）；保留 ZCode 一等公民。

## 4. 运行时与入口

### 4.1 唯一入口：`install.py`（D10）

仓库根目录 **`install.py`** 为跨平台唯一安装入口（Mac / Windows / Linux）。

职责（bootstrap + 转发，保持短小）：

1. 校验解释器版本（`>= 3.10`）  
2. 定位或 clone/更新源码树到约定目录（如 `~/.loopengine/src` 或临时目录）  
3. 将 `scripts/` 加入 `sys.path`（或等价）后调用 `loopengine_install.cli.main()`  

公开用法（三平台同一条）：

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
# Windows 若仅有 `python`：curl …/install.py | python
# 已有 clone：python3 install.py install|upgrade|…  （flags 同 §5）
```

兼容 flags：`--force` / `--dry-run` / `--all` / `--only=…` / `--uninstall` 等，由 `install.py` 解析后交给 `loopengine_install`。

无合格 Python → **打印指引并以非 0 退出**；**不**回退 Bash/PS。

**最低 Python**：`>= 3.10`。

### 4.2 删除的入口与 Shell 资产（本期必须退役）

- `install.sh`（不再维护；文档改指 `install.py`；可选短暂保留一页 deprecation 转调说明后删除）  
- `install.ps1`（删除）  
- `scripts/install/_common.sh`  
- `scripts/install/macos.sh`  
- `scripts/install/linux.sh`  
- `scripts/install/windows.sh`  

### 4.3 Python 模块布局

```
scripts/loopengine_install/
├── __main__.py              # python -m loopengine_install
├── cli.py                   # 子命令与 flags
├── planner.py               # dry-run / --json plan
├── executor.py              # apply / revert operations
├── lifecycle.py             # install / upgrade / uninstall 编排
├── manifest.py              # load / save / validate
├── operations.py            # Operation 类型与 apply/revert
├── central_package.py       # 构建 ~/.loopengine/plugins/loopengine/<ver>/
├── detect.py                # 本机 agent / MCP 可执行探测
├── adapters/
│   ├── base.py
│   ├── cursor.py
│   ├── claude.py
│   ├── zcode.py
│   ├── codex.py
│   ├── gemini.py
│   ├── copilot.py
│   └── pi.py
└── …（MCP merge / 红线注入可内聚或调用现有 scripts/*.py）

schemas/
├── install-manifest.schema.json
└── install-operation.schema.json
```

现有 `scripts/render_plugins.py`、`merge_mcp_config.py`、`register_zcode_*.py`、`inject_rules.py`：**迁入包内或由 adapter 调用**，不再经 shell 编排。

包导入方式：由 `install.py` 将 `scripts/` 加入 `sys.path`，或 `python -m loopengine_install` 时由 `__main__` 修正路径。不强制打 PyPI 包（首版）。

## 5. CLI 面

```text
python3 -m loopengine_install <command> [options]

Commands:
  install     首次安装或智能升级（默认语义对齐今日一键安装）
  upgrade     显式升级到当前源码 version
  uninstall   按 manifest 逆序卸载
  plan        仅输出安装计划（隐含 dry-run）
  doctor      对照 manifest.operations / 磁盘 / registry
  repair      重放缺失或漂移的 managed operations
  list        列出已装组件与 registry keys

Global flags:
  --dry-run   不写盘
  --json      机器可读输出
  --force     同版重装 / 跳过确认等待
  --all       忽略 detect，全工具
  --only=…    显式工具列表
  --target=…  同 --only（别名，便于文档）
```

兼容：`install.py --uninstall` → `uninstall`；无子命令时入口默认 `install`。  
旧文档中的 `curl | bash` / `install.ps1` 一律改为 `curl | python3`（或 `python`）。

## 6. 中央包与 Adapter（沿用 v1，运行时改为 Python）

### 6.1 中央包布局

```
~/.loopengine/
├── .installed_version
├── install-manifest.json          # 生命周期真源（v2 schema）
└── plugins/
    └── loopengine/
        └── <version>/
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

流程：`ensure_central_package` → 各 Adapter `sync` + `activate` → 写 manifest（含 operations）→ upgrade/uninstall/doctor/repair 只认 manifest。

### 6.2 Cursor

- 目标：`~/.cursor/plugins/local/loopengine` ← symlink（优先）或 copy-tree（Windows 无权限时）。
- **停止**写入 `~/.cursor/skills/<skill>/`。
- 升级时按 `skill_names` 白名单清理旧平铺；清理半成品 `~/.cursor/skills/loopengine/`。
- **P0 spike**：最小包放入 `plugins/local`，新会话验证 skill/hooks；失败则**阻断**，不回退平铺。

### 6.3 Claude（D6）

1. Local marketplace（`known_marketplaces.json` + marketplace 元数据）。
2. 写入 `installed_plugins.json`：`loopengine@loopengine-local` → `installPath` / version / 时间戳。
3. Uninstall 移除 key 与仅服务 LE 的 marketplace 条目。
4. `installPath` 优先官方 cache 形路径；P0 spike 锁定后写入 plan。

### 6.4 其它工具

| 工具 | plugin_root | activate |
|------|-------------|----------|
| ZCode | `~/.zcode/skills/loopengine` | marketplace + enabledPlugins |
| Codex | `~/.codex/skills/loopengine` | plugin.json overlay |
| Gemini | `~/.gemini/extensions/loopengine` | gemini-extension.json |
| Copilot / Pi | `~/.…/skills/loopengine` | 文档级 / AGENTS 注入 |

统一契约：`ensure_central_package` → `sync_plugin_root` → `activate` → `record_operations`。

### 6.5 命名空间（借鉴点 3）

| 工具 | 允许 | 禁止 |
|------|------|------|
| Cursor | `plugins/local/loopengine/skills/…` | `~/.cursor/skills/<le-skill>/` 平铺 |
| Claude | 整包 / cache 下 `skills/…` | 顶层散落 LE skill 名 |
| ZCode | `skills/loopengine/` 整包 | 顶层散落 LE skill 目录 |

## 7. Manifest v2 与 Operations

路径：`~/.loopengine/install-manifest.json`  
校验：`schemas/install-manifest.schema.json`（借鉴点 7）。

必填概念字段：

- `schema_version`（= 2）、`product`、`version`、`installed_at`、`central_root`
- `skill_names[]`
- `components.<tool>.{plugin_root, link_mode?, registry_keys?…}`
- `operations[]`（借鉴点 1）
- `extras.redlines[]`、`extras.mcp.{…}`

### 7.1 Operation 示意

```json
{
  "id": "op-001",
  "kind": "symlink-tree",
  "ownership": "managed",
  "source": "~/.loopengine/plugins/loopengine/1.x.y",
  "destination": "~/.cursor/plugins/local/loopengine"
}
```

支持的 `kind`（首版）：`symlink-tree` | `copy-tree` | `merge-json` | `registry-write` | `write-file` | `remove-path`（迁移清理可记）。

- **install**：plan → execute → 持久化 operations  
- **uninstall**：对 `ownership=managed` **逆序** revert  
- **doctor**：operations vs 磁盘/registry（借鉴点 2）  
- **repair**：对 missing/drifted 重放 source（借鉴点 2）

**不删**：非 managed、用户自有 skill、非 LE MCP key、未入清单路径。

### 7.2 无 manifest 旧机

首次 upgrade/install：启发式探测已知路径 + `skill_names`，生成 v2 manifest；uninstall 提供启发式清理模式。

## 8. 生命周期语义

| 命令 | 行为 |
|------|------|
| `install`（默认） | 未装→install；同版→提示/`--force`；旧版→upgrade |
| `upgrade` | 新 version 中央包 → 刷新 Adapter → 更新 manifest → 删旧 version 目录 → Cursor 清平铺 |
| `uninstall` | 逆序 revert operations + 清注册表 + 红线 sentinel；MCP 仅移 LE key |
| `plan` | 输出目标态（`--json` 可选） |
| `doctor` / `repair` | 见 §7.1 |
| `list` | 已装组件摘要 |

## 9. Harness 能力矩阵（借鉴点 5）

交付物：`docs/harness-capability-matrix.md`（轻量表格）+ `audit_tools.py`（或包内 audit）增加 registry / 命名空间维度。

示例列：Harness | 形态 | skills | hooks | registry | 备注。

## 10. 验收标准

1. 唯一入口为 `install.py`；仓库内 **无** `install.sh` / `install.ps1` / `scripts/install/*.sh`。  
2. 新装后 `~/.cursor/skills/` 无 LE skill 目录；`plugins/local/loopengine/skills/` 存在。  
3. Claude `installed_plugins.json` 含 `loopengine@…` 且 `installPath` 可读。  
4. 升级后 version / 中央包 / 各 plugin_root 一致。  
5. 卸载后 manifest 路径与注册 key 消失；用户资产保留。  
6. `plan --json` / `doctor --json` 可机器解析；manifest 通过 schema。  
7. macOS 与 Windows 经同一 `install.py` + 同一 Python 模块；行为由测试锁定。  
8. 核心路径有 unittest（planner / operations apply-revert / adapter registry 写删 / uninstall 幂等）。

## 11. 实现分期

| 阶段 | 内容 | 闸门 |
|------|------|------|
| **P0** | Cursor `plugins/local` spike；Claude marketplace + `installed_plugins` spike | 两者通过才进 P1 |
| **P1** | `loopengine_install` 骨架；`plan`/`install --target cursor`；manifest v2 + schema；落地 `install.py` | Tracer：`--dry-run --json` → 实装 Cursor → `doctor` |
| **P2** | 全 Adapter + uninstall；迁入 MCP/红线/注册逻辑；**删除** `_common.sh`、平台 `.sh`、`install.sh`、`install.ps1` | 验收 §10.1–10.5 |
| **P3** | doctor/repair/list；harness 矩阵；INSTALL/README（统一 `curl \| python3`）；audit 扩展 | 验收 §10.6–10.8 |

**Tracer bullet（R5.3）**：先打通 Cursor 一条垂直切片，再扩全 harness。

## 12. 风险

| 风险 | 缓解 |
|------|------|
| Cursor local 不加载 | P0 失败则停，不回退平铺 |
| Claude schema 与假设不符 | P0 对照官方插件条目 |
| 误删用户同名 skill | 仅白名单 `skill_names` |
| Windows symlink | 回退 `copy-tree` 并记 operation |
| 无 Python | `install.py` 明确失败，文档写清依赖 |
| `curl \| python3` 在 Windows 编码/别名 | 文档同时给出 `curl … -o install.py && python install.py`；探测 `python`/`python3` |
| clone 体验 | clone/更新放在 `install.py` / 包内 bootstrap；**不得**再调用任何 install `.sh` |

## 13. 文档与测试影响

- 更新 `docs/INSTALL.md`、`README.md`：一行安装改为 `curl \| python3`；删除 `install.ps1` / `install.sh` 说明；Python 依赖；CLI；`doctor`/`repair`。  
- 废弃说明：指向 v2；v1 design 标 Superseded。  
- 新增 tests：`tests/test_loopengine_install_*.py`（含 `install.py` bootstrap 烟雾测试）。

## 14. 开放实现细节（plan 阶段锁定）

- Claude `installPath`：`plugins/cache/...` vs `skills/loopengine`（P0 决定）。  
- Cursor 是否还需额外 enable 文件（若 local 目录即足够则不做）。  
- 现有 `scripts/*.py` 是「搬进包」还是「adapter 调用」的目录整理粒度。  
- `python -m` 的 `PYTHONPATH` / 可编辑安装是否引入 `pyproject.toml` 最小包装（首版可不引入）。

## 15. 与 v1 / 旧 plan 的关系

- 本文件为**现行设计真源**。  
- v1 design 标记 Superseded，保留作历史。  
- `docs/2026-07-20-plugin-shaped-install-plan.md` 需在本 spec 用户批准后 **重写为 v2 plan**（Python 模块任务取代 Bash Task）。

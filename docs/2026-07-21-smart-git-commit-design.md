# Design: `/git-commit` — 智能 Stage + Commit（规则+启发式）

> **日期**: 2026-07-21  
> **状态**: Draft · 待用户审阅后转 Approved  
> **路径说明**: 落在 `docs/` 以便主仓版本化（与 plugin-shaped install 设计同级）。  
> **动机**: IDE 手工提交常漏 **untracked 新文件**，导致部署缺文件；需要一条明确、快速、确定性的提交命令。

## 0. 核心目的（验收北极星）

用户在开发完成后执行 **一条** LoopEngine 插件命令 `/git-commit`，系统在 **不调用 LLM 决定文件列表** 的前提下：

1. 快速识别当前工作区相对 HEAD 的变更（含 untracked）  
2. 自动 `git add` **应该进库**的文件  
3. 自动跳过 **不该进库**的文件（规则 + 轻量启发式）  
4. 使用用户提供的 message 完成 `git commit`  
5. 打印可审计的 WILL ADD / SKIPPED 清单  

**成功标准**：中小脏工作区亚秒～数秒完成；新源码类 untracked 不再因「没勾选」而漏提交；密钥与噪声默认不进库。

## 1. 问题陈述

- 痛点类型（已确认）：**A — 新文件未 `git add`（untracked）** 为主。  
- 现有 LoopEngine：`/loop` / `go` 内部有「自动 git add + commit」**文本约定**（模型执行），**无** 面向人手的确定性 slash 命令；仓库也未启用实战 pre-commit/pre-push。  
- IDE Source Control 依赖人工勾选，易漏 untracked。

**非目标（首版）**

- 多条命令拆分（`/git-stage` 等）— 用户选择只要 **一条** `/git-commit`；预览用 `--dry-run`  
- LLM 辅助判断「该不该 add」  
- 自动生成 commit message  
- 默认 `git push`（仅显式 `--push`）  
- 改造 Cursor/ZCode 原生 Source Control UI  
- 首版强制让 `/loop` GitCheck 改调本脚本（列为可选后续）

## 2. 已确认决策

| # | 决策 | 选择 |
|---|------|------|
| D1 | 漏文件类型 | 以 untracked 新文件为主 |
| D2 | 交互形态 | **一条** LoopEngine slash 命令 `/git-commit` |
| D3 | 执行引擎 | 命令薄入口 + **本地脚本**（对齐 `/audit` → `audit_tools.py`） |
| D4 | 过滤策略 | **B**：`.gitignore` 隐含 + 硬黑名单 + 轻量启发式；**无 LLM** |
| D5 | Commit message | **`-m` 必填** |
| D6 | Push | 默认关闭；可选 `--push` |
| D7 | 与 `/loop` | 并存；首版不替换 loop 内部 GitCheck |

## 3. 架构

```text
/git-commit -m "..." [--dry-run] [--push]
        │
        ▼
commands/git-commit.md     # 薄入口：参数、必须跑脚本、禁止模型凭感觉 add
        │
        ▼
scripts/smart_commit.py    # 唯一执行引擎（确定性）
        │
        ├─ git status --porcelain
        ├─ filter (blacklist + heuristics)
        ├─ git add <passed>
        ├─ git commit -m ...
        └─ optional git push
```

**速度**：一次 porcelain + 规则匹配 + git 调用；不扫全仓、不调模型。

## 4. 过滤规则

### 4.1 硬黑名单（命中则 SKIP；路径或文件名）

- 密钥/凭证：`.env`、`.env.*`、`*.pem`、`*.key`、含 `credentials` / `secret` 的路径片段（大小写不敏感）  
- 依赖/构建：`node_modules/`、`vendor/`、`dist/`、`build/`、`.next/`、`__pycache__/`、`*.pyc`  
- 日志与噪声：`*.log`、`*.tmp`、`.DS_Store`、`coverage/`、`htmlcov/`、`.pytest_cache/`  
- IDE/工具缓存：`.idea/`、未刻意跟踪的 `.vscode/`、`*.swp`

### 4.2 会加入

- 已跟踪的 modified / deleted  
- untracked 中未命中 4.1、且未被 `.gitignore` 忽略者（`git status` 已不列出被 ignore 的 untracked）

### 4.3 项目扩展（可选）

- 若存在 `.loopengine-commit-ignore`（gitignore 语法），其匹配项追加为 SKIP。  
- 内置表仍生效；项目文件只做加严，不放宽硬黑名单中的密钥类。

### 4.4 输出格式（每次必打）

```text
WILL ADD:
  path/...
SKIPPED:
  path/...  (reason)
COMMIT: <hash | dry-run | failed>
```

## 5. 命令与 CLI

### 5.1 Slash

```text
/git-commit -m "<message>"
/git-commit -m "<message>" --dry-run
/git-commit -m "<message>" --push
```

`commands/git-commit.md` 要求代理：**仅**通过调用脚本完成 stage/commit，禁止自行拼 `git add` 列表。

### 5.2 脚本（被 slash 与终端共用）

```bash
python3 scripts/smart_commit.py -m "<message>" [--dry-run] [--push]
```

| 情况 | 退出码与行为 |
|------|----------------|
| 非 git 仓库 | ≠0，立即失败 |
| 缺 `-m` | ≠0，打印用法 |
| 过滤后无可提交 | ≠0，列出 SKIPPED |
| `commit` 失败（含钩子） | ≠0；不 push；保留 stage；回显错误 |
| `--push` 失败 | commit 已成功则保留；≠0 标明 push 失败 |
| `--dry-run` | 0（若有可提交候选）或 ≠0（无候选）；不改仓库 |

**Staged 策略**：以「本轮规则通过的文件全集」为准执行 `git add`；`--dry-run` 可预览。不在首版做复杂的「保留用户手工 stage、仅补 untracked」混合模式（YAGNI）。

## 6. 组件清单

| 路径 | 职责 |
|------|------|
| `commands/git-commit.md` | 插件命令入口、参数说明、强制调用脚本 |
| `scripts/smart_commit.py` | porcelain → filter → add → commit → optional push |
| `tests/test_smart_commit.py` | 过滤与 CLI 行为单测（临时 git 仓） |
| `.plugin-template.json` / 各 overlay | 若 commands 为目录枚举则随 `./commands/` 自动包含；否则登记命令 |

可选后续（非首版）：`/loop` GitCheck 复用 `smart_commit.py`；轻量 pre-push 仅作二次闸门。

## 7. 测试计划

1. 仅 modified → 全部 WILL ADD，commit 成功  
2. untracked 源码 + `.env` + `*.log` → 源码 add，其余 SKIPPED  
3. `--dry-run` 后 status 与对象库不变  
4. 过滤后为空 → ≠0  
5. 非 git 目录 → ≠0  
6. 缺 `-m` → ≠0  

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 启发式误跳过合法文件 | 输出 SKIPPED+reason；可用 `--dry-run`；项目 ignore 只加严 |
| 启发式误加入噪声 | 硬黑名单优先；密钥类宁可不提交 |
| 代理忽略文档自己 `git add` | command 文案硬约束 + 验收测「应调用脚本」 |
| ZCode/Cursor 对 command 参数传递不一致 | 脚本为真源；文档写明等价 CLI |

## 9. 反选项（否决）

| 方案 | 否决理由 |
|------|----------|
| 仅 pre-push 拦截、不自动 add | 不符「一键识别并提交」 |
| 纯 slash 靠模型决定文件列表 | 慢、不稳，不符「快速高效」与 D4 |
| 无条件 `git add -A` | 过滤能力过弱，易提交密钥/噪声 |
| 首版多命令拆分 | 用户明确只要一条命令 |

## 10. 实施顺序（概要）

1. 实现 `smart_commit.py` + 单测（红绿）  
2. 增加 `commands/git-commit.md`  
3. 确认 plugin 打包含该 command；必要时更新 README/`using-loopengine` 一行说明  
4. 本地手测 dry-run / 真实 commit  

详细任务拆解待本 spec **Approved** 后由 writing-plans 产出。

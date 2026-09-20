---
name: using-git-worktrees
description: |
  TRIGGER: 开始需与当前工作区隔离的功能开发 / 执行实施计划前 / 确保 isolated workspace 存在（原生工具优先，git worktree 兜底）（不用于：单会话小改动无需隔离的场景）
  RULE: V4 主承载 — subagent / 多任务开发必须 worktree 隔离
  DETAIL: 本 SKILL.md（worktree 建立流程）+ AGENTS.md §V4
---

# Using Git Worktrees（使用 git worktree）

## 概述

确保工作发生在隔离工作区。优先用平台原生 worktree 工具。只有没有原生工具时才回退手动 git worktree。

**核心原则：** 先检测既有隔离，再用原生工具，最后回退 git。绝不与 harness 对抗。

**开始时声明：** "我正在使用 using-git-worktrees 技能建立隔离工作区。"

## Step 0: 检测既有隔离

**创建任何东西之前，先检查你是否已处于隔离工作区。**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule 防护：** git submodule 内 `GIT_DIR != GIT_COMMON` 同样成立。下"已在 worktree"的结论前，先确认不在 submodule 里：

```bash
# 若返回路径，你在 submodule 中而非 worktree —— 按普通 repo 处理
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**若 `GIT_DIR != GIT_COMMON`（且非 submodule）：** 你已在 linked worktree 中。跳到 Step 3（项目设置）。**不要**再建 worktree。

按分支状态回报：
- 在分支上："已在隔离工作区 `<path>`，分支 `<name>`。"
- Detached HEAD："已在隔离工作区 `<path>`（detached HEAD，外部管理）。收尾时需要建分支。"

**若 `GIT_DIR == GIT_COMMON`（或在 submodule 中）：** 你在普通 repo checkout。

你的指令中用户是否已声明 worktree 偏好？没有则在创建前征求同意：

> "要我建立一个隔离 worktree 吗？它可以保护你当前分支不被改动。"

已有声明偏好则不再询问直接遵循。用户拒绝则在原地工作，跳到 Step 3。

## Step 1: 创建隔离工作区

**两种机制，按此顺序尝试。**

### 1a. 原生 worktree 工具（优先）

用户已要隔离工作区（Step 0 同意）。你已有创建 worktree 的手段吗？可能叫 `EnterWorktree`、`WorktreeCreate`、`/worktree` 命令或 `--worktree` flag。有就用它，然后跳到 Step 3。

原生工具自动处理目录落位、分支创建与清理。有原生工具时用 `git worktree add` 会制造 harness 看不见也管不了的幻影状态。

没有原生 worktree 工具才继续 Step 1b。

### 1b. Git Worktree 兜底

**仅在 Step 1a 不适用时使用** —— 没有原生 worktree 工具。手动用 git 建 worktree。

#### 目录选择

按此优先级。用户显式偏好永远优先于文件系统现状。

1. **查指令中的既定 worktree 目录偏好。** 用户已指定则直接用，不再询问。

2. **查项目本地既有 worktree 目录：**
   ```bash
   ls -d .worktrees 2>/dev/null     # 优先（隐藏）
   ls -d worktrees 2>/dev/null      # 备选
   ```
   找到就用。两个都有则 `.worktrees` 胜出。

3. **查既有全局目录：**
   ```bash
   project=$(basename "$(git rev-parse --show-toplevel)")
   ls -d ~/.config/superpowers/worktrees/$project 2>/dev/null
   ```
   找到就用（旧全局路径向后兼容）。

4. **无任何其他指引时**，默认用项目根的 `.worktrees/`。

#### 安全验证（仅项目本地目录）

**创建 worktree 前必须验证目录已被 ignore：**

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**未被 ignore：** 加入 .gitignore，commit 该改动，再继续。

**为什么关键：** 防止 worktree 内容被意外提交进仓库。

全局目录（`~/.config/superpowers/worktrees/`）无需验证。

#### 创建 Worktree

```bash
project=$(basename "$(git rev-parse --show-toplevel)")

# Determine path based on chosen location
# For project-local: path="$LOCATION/$BRANCH_NAME"
# For global: path="~/.config/superpowers/worktrees/$project/$BRANCH_NAME"

git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**Sandbox 兜底：** `git worktree add` 因权限错误失败（sandbox 拒绝）时，告知用户 sandbox 阻止了 worktree 创建、改为在当前目录工作。然后原地跑设置与基线测试。

## Step 3: 项目设置

自动探测并运行相应设置：

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

## Step 4: 验证干净基线

跑测试确保工作区起点干净：

```bash
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**测试失败：** 报告失败，询问继续还是排查。

**测试通过：** 报告就绪。

### 回报

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| 状况 | 动作 |
|------|------|
| 已在 linked worktree | 跳过创建（Step 0） |
| 在 submodule 中 | 按普通 repo 处理（Step 0 防护） |
| 有原生 worktree 工具 | 用它（Step 1a） |
| 无原生工具 | git worktree 兜底（Step 1b） |
| `.worktrees/` 存在 | 用它（验证 ignored） |
| `worktrees/` 存在 | 用它（验证 ignored） |
| 两者都存在 | 用 `.worktrees/` |
| 都不存在 | 查指令文件，再默认 `.worktrees/` |
| 全局路径存在 | 用它（向后兼容） |
| 目录未被 ignore | 加 .gitignore + commit |
| 创建遇权限错误 | Sandbox 兜底，原地工作 |
| 基线测试失败 | 报告失败 + 询问 |
| 无 package.json/Cargo.toml | 跳过依赖安装 |

## 常见错误

### 与 harness 对抗

- **问题：** 平台已提供隔离时仍用 `git worktree add`
- **修复：** Step 0 检测既有隔离。Step 1a 让位原生工具。

### 跳过检测

- **问题：** 在既有 worktree 里再嵌套建 worktree
- **修复：** 创建任何东西前永远先跑 Step 0

### 跳过 ignore 验证

- **问题：** worktree 内容被 git 跟踪，污染 git status
- **修复：** 创建项目本地 worktree 前永远先 `git check-ignore`

### 臆断目录位置

- **问题：** 制造不一致，违反项目约定
- **修复：** 遵循优先级：既有 > 旧全局 > 指令文件 > 默认

### 带着失败测试继续

- **问题：** 分不清新 bug 与既有问题
- **修复：** 报告失败，取得明确许可再继续

## Red Flags

**Never：**
- Step 0 检测到既有隔离还创建 worktree
- 有原生 worktree 工具（如 `EnterWorktree`）时用 `git worktree add`。这是头号错误——有就用。
- 跳过 Step 1a 直接跳进 Step 1b 的 git 命令
- 创建项目本地 worktree 前不验证 ignored
- 跳过基线测试验证
- 不询问就带着失败测试继续

**Always：**
- 先跑 Step 0 检测
- 原生工具优先于 git 兜底
- 遵循目录优先级：既有 > 旧全局 > 指令文件 > 默认
- 项目本地目录验证 ignored
- 自动探测并运行项目设置
- 验证干净测试基线

---

## §K. 完成开发分支（吸收原 finishing-a-development-branch · v2.0 合并 · D2.0）

> **来源**：community skill · D2.0 合并于 using-git-worktrees（worktree 创建与收尾本是一对）。
> **使用场景**：实现完成、所有测试通过、需要决定如何收尾（merge / PR / keep / discard）时使用。
> **核心原则**：Verify tests → Detect environment → Present options → Execute choice → Clean up。

### The Process（收尾流程）

#### Step 1: 验证测试

**在给出选项前，先验证测试通过：**

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**若测试失败**：

```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

停止，不进入 Step 2。

**若测试通过**：进入 Step 2。

#### Step 2: 探测环境

**给出选项前先确定工作区状态：**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

| 状态 | 菜单 | 清理 |
|-------|------|---------|
| `GIT_DIR == GIT_COMMON`（普通 repo） | 标准 4 选项 | 无 worktree 要清 |
| `GIT_DIR != GIT_COMMON`，命名分支 | 标准 4 选项 | 基于来源（见 Step 6） |
| `GIT_DIR != GIT_COMMON`，detached HEAD | 简化 3 选项（无 merge） | 不清理（外部管理） |

#### Step 3: 确定基分支

```bash
# Try common base branches
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

或询问："这个分支是从 main 切出来的——对吗？"

#### Step 4: 呈现选项

**普通 repo 与命名分支 worktree —— 恰好这 4 个选项：**

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Detached HEAD —— 恰好这 3 个选项：**

```
Implementation complete. You're on a detached HEAD (externally managed workspace).

1. Push as new branch and create a Pull Request
2. Keep as-is (I'll handle it later)
3. Discard this work

Which option?
```

**不要加解释** —— 保持选项简洁。

#### Step 5: 执行所选

##### Option 1: 本地 Merge

```bash
# Get main repo root for CWD safety
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"

# Merge first — verify success before removing anything
git checkout <base-branch>
git pull
git merge <feature-branch>

# Verify tests on merged result
<test command>

# Only after merge succeeds: cleanup worktree (Step 6), then delete branch
git branch -d <feature-branch>
```

##### Option 2: Push 并创建 PR

```bash
# Push branch
git push -u origin <feature-branch>

# Create PR
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

**不要清理 worktree** —— 用户需要它来迭代 PR 反馈。

##### Option 3: 保持现状

报告："保留分支 `<name>`。Worktree 保留在 `<path>`。"

**不清理 worktree。**

##### Option 4: Discard

**先确认：**

```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

等待精确确认。确认后：

```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
# Cleanup worktree (Step 6), then force-delete branch:
git branch -D <feature-branch>
```

#### Step 6: 清理工作区

**只对 Option 1 和 4 运行。** Option 2 和 3 总是保留 worktree。

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
WORKTREE_PATH=$(git rev-parse --show-toplevel)
```

- **若 `GIT_DIR == GIT_COMMON`**：普通 repo，无 worktree 要清。完成。
- **若 worktree 路径在 `.worktrees/`、`worktrees/` 或 `~/.config/superpowers/worktrees/` 下**：我们创建了这个 worktree —— 我们负责清理：

  ```bash
  MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
  cd "$MAIN_ROOT"
  # Pre-removal guard: surface untracked/uncommitted files (borrowed from superpowers v6.3.0)
  git -C "$WORKTREE_PATH" status --porcelain
  git worktree remove "$WORKTREE_PATH"
  git worktree prune  # Self-healing: clean up any stale registrations
  ```

  **未跟踪文件防护**：若 `status --porcelain` 输出非空（存在未跟踪/未提交文件），**禁止继续移除**——停下来逐个点名文件，用 AskUserQuestion 让用户决定：先转移/提交文件再重跑清理，或明确确认丢弃。**Never** 在 `worktree remove` 报错后顺手加 `--force`——`--force` 会静默销毁未跟踪文件，这正是本防护要拦的路径。

- **其他情况**：宿主环境（harness）拥有此工作区。**不要移除**。若平台提供 workspace-exit 工具，用它；否则保持原状。

### Quick Reference（收尾）

| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | yes | - | - | yes |
| 2. Create PR | - | yes | yes | - |
| 3. Keep as-is | - | - | yes | - |
| 4. Discard | - | - | - | yes (force) |

### Common Mistakes（收尾）

- **跳过测试验证** → Merge 坏代码 / 创建失败 PR。Fix：始终先验证测试。
- **开放式提问**（"What should I do next?"）→ 模糊。Fix：恰好 4 个结构化选项（detached HEAD 3 个）。
- **Option 2 清理 worktree** → 移除了用户迭代 PR 需要的 worktree。Fix：只对 Option 1 和 4 清理。
- **删除分支前不移除 worktree** → `git branch -d` 失败（worktree 仍引用分支）。Fix：先 merge，移除 worktree，再删分支。
- **在 worktree 内部运行 `git worktree remove`** → 静默失败。Fix：`cd` 到主 repo 根再移除。
- **清理 harness 拥有的 worktree** → 幻影状态。Fix：只清 `.worktrees/` / `worktrees/` / `~/.config/superpowers/worktrees/`。
- **Option 4 不确认** → 误删工作。Fix：要求键入 "discard" 确认。
- **`worktree remove` 失败后加 `--force`** → 静默销毁未跟踪文件。Fix：先跑 `status --porcelain` 列出未跟踪文件，非空则停下问用户（2026-09-20 引入，源自 superpowers v6.3.0）。

### Red Flags（收尾）

**Never:**
- 在测试失败时继续
- 不验证结果就 merge
- 不确认就删除工作
- 不明确请求就 force-push
- 不确认 merge 成功就移除 worktree
- 清理不是你创建的 worktree（来源检查）
- 在 worktree 内部运行 `git worktree remove`
- 未跟踪文件非空时 `--force` 移除（先点名文件问用户）

**Always:**
- 给选项前验证测试
- 给菜单前检测环境
- 恰好 4 个选项（detached HEAD 3 个）
- Option 4 要求键入确认
- 只对 Option 1 和 4 清理 worktree
- worktree 移除前 `cd` 到主 repo 根
- 移除后 `git worktree prune`

---

## §N. 多会话并发隔离工作流（v2.0 强化 · V4 主承载）

### worktree 创建 SOP
1. 主会话确定任务边界（scope）后创建 worktree
2. 每个 subagent / 并发会话在独立 worktree 中工作
3. 完成后由主会话统一 merge / PR

### 多会话场景
- **A 场景**：用户同时开 2+ 个 AI 会话改同一仓库 → 每会话一个 worktree
- **B 场景**：主会话派 subagent 并行改代码 → 每 subagent 一个 worktree（或串行共用主 worktree）
- **C 场景**：长任务 + 紧急修复并行 → 紧急修复独立 worktree，不阻塞长任务

### 禁止行为（V4 红线）
- ❌ 多个 agent 同时改同一工作目录（无隔离）
- ❌ worktree 未验证 ignore 就创建
- ❌ 跳过 Step 0 检测直接创建（可能嵌套）

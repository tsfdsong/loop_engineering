# LoopEngine — 循环工程全家桶

## 🔴 MCP 红线规则（本项目最高优先级 · 不可违反 · v6.4 重构）

> **任何需要理解代码结构的操作，必须先用 MCP 工具，禁止直接 Read 全文件。**
> 此规则适用于本项目（loop_engineering）的所有开发、调研、分析工作。

### 1. 适用范围

- 修改代码、调研代码、解释代码、分析架构
- 查找函数/类/变量定义、查找引用位置
- 了解项目结构、浏览目录、理解文件内容
- **只要目的是"理解代码"，就必须 MCP 优先**

### 2. 四层探查策略（L0 → L3）

**核心原则**：从粗到精，层层下钻，Read 降级为最后手段。

```
┌─────────────────────────────────────────────────────────────────┐
│ L0 项目全景                                                      │
│   jcodemunch.get_repo_map(scope="...")   ← 代码符号级结构        │
│   repomix.pack_codebase(directory)      ← 兜底（不依赖索引）     │
│   输出: 1-2K token 的项目骨架                                      │
├─────────────────────────────────────────────────────────────────┤
│ L1 文件结构                                                      │
│   jcodemunch.get_file_outline(file_path)  ← 符号列表/签名       │
│   headroom.headroom_compress(content)     ← 大段 Markdown        │
│   输出: 每文件 200-500 token 大纲/摘要                              │
├─────────────────────────────────────────────────────────────────┤
│ L2 精准内容                                                      │
│   jcodemunch.search_symbols(query)         ← 符号语义搜索         │
│   jcodemunch.get_symbol_source(symbol_id)  ← 拿到源码            │
│   headroom.headroom_retrieve(hash, query)  ← 按需展开压缩内容    │
│   输出: 单符号/段 ~100-300 token                                   │
├─────────────────────────────────────────────────────────────────┤
│ L3 精确行（最后手段）                                              │
│   Read(file_path, offset=N, limit=M)       ← offset+limit 限定   │
│   输出: 1-3 行精确内容                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 3. MCP 三件套职责分工

| 工具 | 最佳场景 | 兜底场景 | 限制 |
|------|---------|---------|------|
| **jCodeMunch-MCP** | Python 代码（AST 解析） | 任意结构化文件 | 需先 index_folder；worktree 默认未索引 |
| **Repomix** | 任意代码库（含 Markdown） | jcodemunch 索引失败时 | 一次性输出，无增量 |
| **Headroom-ai** | 大段 Markdown / 大文件压缩 | 长会话持续压缩 | hash 检索，不变更内容 |

### 4. 唯一例外（5 条）

| # | 例外场景 | 处理 |
|---|---------|------|
| 1 | MCP 工具全部不可用（报错/超时/未索引） | 记录原因后用 Read，但**仍要尝试 repomix 兜底** |
| 2 | 文件 < 50 行（小配置文件等） | 可直接 Read |
| 3 | 已通过 MCP 定位，需要精确读取 1-3 行 | Read with offset/limit |
| 4 | **执行类操作**（git/cp/rsync/worktree） | 用 Bash，**不算违规** |
| 5 | **JSON/YAML/TOML 小配置**（< 30 行） | Read 全文，**不算违规** |

### 5. 违规判定（3 级 6 条）

| 等级 | 违规行为 | 自愈方法 |
|------|---------|---------|
| 🔴 **红线** | 连续 3 次 Read 而未用 MCP | 立即重写会话，先用 MCP 探查 |
| 🟠 **严重** | 单次 Read > 100 行 | 改用 `get_file_outline` 或 `headroom_compress` |
| 🟠 **严重** | Bash `cat/grep/head file` 探查代码 | 改用 `search_symbols` 或 Read with offset/limit |
| 🟠 **严重** | worktree 中未先 `index_folder` | 改用 `index_folder(identity_mode="git", follow_symlinks=true)` |
| 🟡 **中等** | MCP 不可用时未尝试 `pack_codebase` 兜底 | 自动调用 repomix 兜底 |
| 🟡 **中等** | 长会话（> 30 轮）未用 `headroom_compress` | 定期压缩大段内容 |

### 6. 自查清单（5 项 · 会话结束前必查）

- [ ] **MCP 调用次数 ≥ Read 调用次数？**
- [ ] **单次 Read > 100 行？**（应改 MCP）
- [ ] **Bash 探查代码次数 < 5？**（含 cat/grep/head）
- [ ] **worktree 中是否先 index_folder？**
- [ ] **长会话是否用 headroom 压缩？**

### 7. worktree 特殊流程（v6.4 新增 · 修复本次任务根因）

> **根因**：v6.4 任务中 worktree 路径未被 jcodemunch 索引，导致 `get_repo_map` 报 "Repository not found"，最终被迫大量用 Read，违反红线。

**强制流程**：

```bash
# 1. 创建 worktree 后立即索引
mcp__jcodemunch__index_folder(
  path=".worktrees/<name>",
  identity_mode="git",        # 关键：让 jcodemunch 识别为同一 git repo
  follow_symlinks=true        # 跟随 git worktree 符号链接
)

# 2. 验证可解析
mcp__jcodemunch__resolve_repo(path=".worktrees/<name>")

# 3. 失败兜底（jcodemunch 索引失败时）
mcp__repomix__pack_codebase(directory=".worktrees/<name>")

# 4. 仍失败 → 才 fallback 到 Read（最后手段）
```

### 8. Bash 探查职责清单

| ✅ 允许（执行类） | ❌ 禁止（探查类，应改 MCP/Read） |
|------------------|---------------------------------|
| `git log/show/diff` | `cat < file >` |
| `ls/find`（仅看文件名） | `head -N < file >`（探查内容） |
| `cp/rsync/rm/worktree add` | `grep -rn "pattern" *.py`（探查代码） |
| `git rm/mv/add/commit` | `wc -l < file >`（探查行数） |
| `mkdir/touch/chmod` | `awk/sed`（修改文件） |

### 9. MCP 工具速查（按层级）

| 层级 | 工具 | 用途 | Token 节省 |
|:---:|------|------|:---:|
| **L0** | `mcp__jcodemunch__get_repo_map` | 项目结构全景图（符号级） | ~80% |
| **L0** | `mcp__repomix__pack_codebase` | 打包代码库（兜底） | ~70% |
| **L1** | `mcp__jcodemunch__get_file_outline` | 文件符号大纲 | ~85% |
| **L1** | `mcp__jcodemunch__get_file_tree` | 目录树浏览 | ~95% |
| **L1** | `mcp__headroom__headroom_compress` | 压缩大段内容 | ~95% |
| **L2** | `mcp__jcodemunch__search_symbols` | 语义搜索符号 | ~90% |
| **L2** | `mcp__jcodemunch__get_symbol_source` | 拿单符号源码 | ~90% |
| **L2** | `mcp__jcodemunch__find_references` | 查找引用位置 | ~85% |
| **L2** | `mcp__jcodemunch__get_blast_radius` | 修改影响面分析 | ~90% |
| **L2** | `mcp__headroom__headroom_retrieve` | 按需展开压缩 | ~95% |
| **L3** | Read with offset/limit | 精确行（最后手段） | 视场景 |

### 10. 性能基准（6 场景实测）

| 场景 | 直接读（Read+grep+cat） | MCP 优化 | 节省 |
|------|----------------------|--------|:---:|
| 阅读单个函数（300 行） | ~800 token | ~40 token | **95%** |
| 理解项目架构 | ~1,200,000 token | ~370,000 token | **69%** |
| 长会话（50 轮） | ~40,000 token | ~12,000 token | **70%** |
| pytest 输出（200 行） | ~1,200 token | ~200 token | **83%** |
| **worktree 启动（v6.4 新增）** | ~5,000 token（Read 全部） | ~200 token（index+map） | **96%** |
| **跨 9 技能审查（v6.4 新增）** | ~34,000 token（9×Read） | ~5,000 token（outline+symbol） | **85%** |
| **典型场景平均** | — | — | **~80%** |

### 11. PATH 修复指引（如 MCP 命令找不到）

如果 `jcodemunch-mcp` 或 `headroom` 命令找不到，是因为 pip 安装到了 Scripts 目录但未加入 PATH：

- **Windows**: 把 `C:\Users\<user>\AppData\Roaming\Python\Python<ver>\Scripts\` 加入系统 PATH
- **Linux/macOS**: `export PATH="$HOME/.local/bin:$PATH"`（写入 ~/.bashrc / ~/.zshrc）

或修改项目根 `.mcp.json` 用绝对路径（详见 `docs/mcp-setup-guide.md` 第四章）。

### 12. 与其他规则的关系

- **本规则** vs `evidence-first` 技能：evidence-first 关注"事实标注 [F]/[H]/[P]"，本规则关注"如何用工具高效探查"——两者互补不冲突
- **本规则** vs `systematic-debugging`：debug 时同样适用本规则（探查代码走 MCP）
- **本规则** vs `verification-before-completion`：完成前自检时，本规则的 5 项自查清单**也必须**勾选

---

> **v6.4 升级要点**：
> - 从 2 级违规 → 3 级 6 条
> - 从 4 场景基准 → 6 场景（新增 worktree + 跨技能审查）
> - 新增 worktree 特殊流程（**修复 v6.4 任务根因**）
> - 新增 Bash 探查职责清单
> - 新增 4 层探查策略（L0-L3）

---

## 🔴 事实优先硬规则（本项目最高优先级 · 不可违反 · 2026-06-29 加入）

> **针对 2026-06-29 v5.4 兼容性胡乱分析事故**（AI 基于错误假设套用通用话术被用户当场识破），
> 本项目强制执行以下 5 条事实优先规范：

1. **项目分析前必查 5 项事实**（参见 `skills/evidence-first/SKILL.md`）：
   - `git log --oneline -10`（最近 10 次提交）
   - `README.md` / `AGENTS.md`（项目自述）
   - `pyproject.toml` / `package.json`（版本声明）
   - `docs/` 下最近的设计文档 / CHANGELOG
   - `git log --since="3 months ago" --oneline | wc -l`（3 个月活跃度）

2. **每句话必须标注 [F]/[H]/[P]**：
   - `[F]` 事实（已通过 git/file/docs 验证，可追溯）
   - `[H]` 假设（基于经验但未验证，需明确标注）
   - `[P]` 原则（通用工程参考，优先级最低）

3. **不确定 = 说"我不清楚"**：禁止凑答案 / 编造 / 套模板

4. **长篇论述前自检 4 问**：
   - 我有 [F] 事实依据吗？
   - [H] 假设明确标注了吗？
   - 错了损失大吗？（高损失必须 [F] 主导）
   - 能说"我不清楚"吗？

5. **判断必须可追溯到事实**：每条结论附"事实依据 + 来源 + 验证方式"

**未完成事实清单 = 禁止进入分析论述**。

**违规判定**：长篇论述（> 5 段）无 [F] 标注 = 视为红线违规，自动加载 `evidence-first` 技能重写。

**事故教训库**：`docs/lessons-learned.md`（含本事故的完整记录 + 修复措施）

---

## 如果你是 AI 代理

你拥有 LoopEngine —— 一个包含 33 个技能（v6.4 真正融合超级技能 + 清理 v6.2 漏网后）的开发引擎全家桶（v6.1 新增 `evidence-first`）。

**Below is the full content of your 'loopengine:skill-hub' skill —— 你的技能调度中心。收到任何任务后，先通过 skill-hub 自动匹配最合适的技能。**

skill-hub 会在收到任务时自动分析意图，从 33 个技能（v6.4 真正融合后）中调度最精准的一个。涵盖：编码、架构、重构、测试、调试、API、安全、数据库、CI/CD、规划执行、产品管理、循环工程等全领域。

## 安装方式

一行安装（极简 curl 一条龙）：

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

**装完即用**。覆盖 ZCode / Claude Code / Codex / Gemini / Copilot / Pi 等 AI 编程工具的约定技能目录。详见 `docs/INSTALL.md`。

### 更新

```bash
bash <(curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/update.sh)
```

更新 = git pull 最新 + exec install.sh 重装。

---

## 历史（v1.0.x 旧文档，已废弃 · 仅做迁移参考用）

> ⚠️ **v2.0 重构后不再依赖** ZCode 内部 `marketplace.json` / `.zcode-plugin/plugin.json` 注册链。下面记录的是历史踩过的坑，仅作迁移参考。

### 旧版 ZCode 桌面版手动安装（PowerShell）

<details>
<summary>展开</summary>

```powershell
# 1. 克隆项目到内置包目录
git clone https://github.com/tsfdsong/loop_engineering.git "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"

# 2. 复制到 CLI 缓存
mkdir -p "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.1"
xcopy "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin\*" "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.1\" /E /I /Y

# 3. 在 marketplace.json 中注册
# 4. 在 config.json 中启用
# 5. 创建 data 目录
# 6. 重启 ZCode 桌面版
```

详见旧文档 `docs/zcode-install-guide.md`。

</details>

### 旧版 ZCode 桌面版 MCP 重启丢失红线（2026-06-28 实测发现）

<details>
<summary>展开</summary>

**症状**：安装/更新后 MCP 三件套正常加载，但**重启 ZCode 后消失**。

**根因**：
1. ZCode 启动时自动重写 marketplace.json，只保留"内置包目录能找到的插件"
2. ZCode 优先从 CLI 缓存 `plugin.json` 加载 MCP（不是项目源）
3. CLI 缓存的 `plugin.json` 默认没有 `mcpServers` 字段

**v2.0 治本**：让 install.sh 直接 cp skills/ 到 `~/.agents/skills/`（用户级 fallback），绕开 marketplace 注册链。

**调试**：

```bash
# 看 CLI 缓存 plugin.json 是否有 mcpServers
grep -A2 "mcpServers" ~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/*/.zcode-plugin/plugin.json

# 看 marketplace.json 是否含 loopengine
grep "loopengine" ~/.zcode/cli/plugins/marketplaces/*/marketplace.json

# 必要时跑自愈
bash scripts/zcode-mcp-ensure.sh
```

</details>

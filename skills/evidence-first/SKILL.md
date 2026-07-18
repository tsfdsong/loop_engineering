---
name: evidence-first
description: |
  TRIGGER: 比较选项 / 评估设计 / 架构决策 / 'X vs Y' / 'should I' / '为什么' / '分析' / '比较' / '评估' / '选型' / '该不该' / '应不应该'（不用于：纯实现用 refactoring/testing，头脑风暴用 brainstorming）
  RULE: C3 + C4 主承载 — 任何长篇论述（>5 段）前必须先给证据/数据/引用；MCP 工具优先
  DETAIL: 本 SKILL.md（证据优先方法论）+ AGENTS.md §C3 §C4
metadata:
  version: "1.0"
  type: skill
  origin: "2026-06-29 v5.4 兼容性事故"
  trigger_keywords: "分析/比较/评估/为什么/设计/重构/选型/该不该/应不应该"
  mandatory_before: "任何长篇论述（> 5 段）"
---

# Evidence-First Protocol（事实优先协议）

> **铁律**：**没有事实清单 = 禁止论述**。
> 任何"为什么 X""X 和 Y 哪个好""该不该 X""X 的价值"类问题，必须先查事实，再回答。

## 1. 起源

2026-06-29 v5.4 兼容性事故：AI 在回答"为什么需要 v5.4 兼容"时，基于"v5.4 是老版本"的**错误假设**，套用通用软件工程话术，给出 5 条**不实理由**（用户生态 / 企业 SLA / SemVer / 法律责任等），被用户当场识破。

**事故根因**：
1. 没看 git log，不知道 v5.4 是当天定稿的基线
2. 套用"通用兼容性原则"代替"项目事实"
3. 长篇大论掩盖事实不清
4. 没有"我错了/我不清楚"的意识

**事故教训**：**没有事实依据的专业论述 = 高级胡说**。

## 2. 5 项事实清单（必查）

任何项目分析、比较、评估前，**必须**先输出 5 项事实：

| # | 必查项 | 命令/位置 | 用途 |
|---|--------|----------|------|
| 1 | **最近 10 次提交** | `git log --oneline -10` | 了解项目活跃度和最近方向 |
| 2 | **项目自我描述** | `README.md` / `AGENTS.md` | 项目的"自述"，避免外部推断 |
| 3 | **版本声明** | `package.json` / `pyproject.toml` / `VERSION` | 了解当前版本基线 |
| 4 | **最近 changelog / 设计文档** | `docs/` / `CHANGELOG.md` | 了解最近的设计决策 |
| 5 | **main 分支活跃度** | `git log --since="3 months ago" --oneline \| wc -l` | 判断项目是否活跃 |

**未完成 5 项事实清单 = 禁止进入分析论述**。

## 3. 三类标注（每句话必标）

每一条论述中的**每一句话**必须标注类型：

| 标注 | 含义 | 优先级 | 示例 |
|------|------|:------:|------|
| **[F]** | **事实** — 已通过 git/file/docs 验证 | 🟢 最高 | [F] v5.4 SKILL.md 备份存在（ls 验证） |
| **[H]** | **假设** — 基于通用经验的合理推测 | 🟡 中 | [H] 用户可能依赖 v5.4 行为（未验证） |
| **[P]** | **原则** — 通用工程原则/最佳实践 | 🔴 最低 | [P] SemVer 规定次版本兼容（通用原则） |

**冲突优先级：F > H > P**（事实推翻假设，假设推翻原则）。

## 4. 自检 4 问（长篇论述前必答）

回答前自问：

1. **我有 [F] 事实依据吗？**（至少 1 个 [F] 标注才能长篇论述）
2. **[H] 假设明确标注了吗？**（不能用"应该""可能"伪装成事实）
3. **错了损失大吗？**（高损失场景必须 [F] 主导）
4. **能说"我不清楚"吗？**（不确定时优先说不知道）

**4 问中任一失败** = 缩小论述范围 / 标注不确定 / 主动询问用户。

## 5. 不确定时的处理（铁律）

| 场景 | 正确做法 | 错误做法 |
|------|---------|---------|
| 不了解项目状态 | "让我先查 git log / 文件" | 凭印象推断 |
| 假设与事实冲突 | "事实推翻假设" | 坚持假设 |
| 通用原则套用 | "通用原则是 X，但本项目是 Y" | 套模板不验证 |
| 用户纠正后 | "你说得对，我之前错在 X" | 辩解/转移话题 |
| 真的不知道 | **"我不清楚"** | 编造"通常""一般""应该" |

## 6. 触发场景（必须加载本技能）

- 用户问"为什么是 X" / "X 有什么用" / "X 有什么价值"
- 用户问"X 和 Y 哪个好" / "X vs Y" / "选 X 还是 Y"
- 用户问"该不该 X" / "应不应该 X"
- 用户问"评估/分析/设计/重构"类
- AI 自己准备给出**长篇论述（> 5 段）**时

## 7. 输出格式模板

```markdown
## 事实清单

1. [F] ...（已验证）
2. [F] ...（已验证）
3. [F] ...（已验证）
4. [H] ...（未验证的假设）
5. [P] ...（通用原则参考）

## 自检 4 问

1. 我有 [F] 依据吗？✅
2. [H] 明确标注了吗？✅
3. 错了损失大吗？中（关键决策需 [F] 主导）
4. 能说"我不清楚"吗？✅

## 分析

[基于事实的回答，每句话标注类型]

## 结论

[可追溯到事实的结论]
```

## 8. 详细规范

- 5 项事实清单详解 → `references/fact-checklist.md`
- [F]/[H]/[P] 标注规范 → `references/claim-types.md`
- 自检 4 问详解 → `references/self-check.md`
- 不确定时处理 → `references/no-hallucination.md`
- 追溯链规范 → `references/traceability.md`

## 9. 好坏对比案例

- 坏案例（事故现场）→ `examples/bad-v54-compat-answer.md`
- 好案例（重写版）→ `examples/good-v54-compat-answer.md`

## 10. 兼容性

- ✅ 与现有 45 个技能（v6.1.1 合并后）完全兼容
- ✅ 可与 `verification-before-completion`（完成时验证）配合使用
- ✅ 可与 `systematic-debugging`（调试）配合使用
- ✅ 形成完整链路：evidence-first（开始）→ systematic-debugging（过程）→ verification-before-completion（完成）

---

## 论源（v1.0.4 工程实践红线对接）

本技能作为以下工程实践红线的**方法论支撑**（单点真源引用，AGENTS.md §9）：

- **R5.6 Working > Comprehensive** — 提供"先让代码 work，再补文档"的事实优先方法论；禁止"完整文档先行"导致的过度设计（与本技能"事实优先"铁律一致）

> **红线触发场景**：任何 AI 处理"该不该写文档 / 什么时候补文档 / 是否需要完整设计"类问题时，必须遵循 R5.6；本技能提供 5 项事实清单 + 长篇论述前的 4 问自查。
> **同步版本**：AGENTS.md v1.0.4（2026-07-03）

---

## §N. 防幻觉专章（v2.0 强化 · 适配各种能力模型）

### 默认怀疑自己的判断
- 不确定就说"我不清楚"
- 关键判断多用 [F] 标注（事实 · 可追溯）
- 避免凑答案 / 编造 / 套模板

### 长输出前自检 4 问
- 我有 [F] 事实依据吗？
- [H] 假设标注了吗？
- 错了损失大吗？（高损失必须 [F] 主导）
- 能说"我不清楚"吗？

### 能力较弱模型尤其受益
- 默认走"证据先行"路径（每结论附来源+验证方式）
- 长篇论述（>5 段）无 [F] = 红线违规
- 与 C3 事实优先红线协同：本 skill 提供"如何做到事实优先"的方法论

---

## §N. MCP 场景矩阵详规（吸收原 AGENTS.md §1.2-1.10 · v2.0 迁移）

> **来源**：原 AGENTS.md §1.2-1.10（v1.0.6+ · 909 行结构）。
> v2.0 AGENTS.md 精简为"C4 MCP-S1 只保留 1 句话（接入新代码库必须先 `get_repo_map` → `get_file_outline`）"，其余 S2-S6 场景矩阵 / 三件套职责 / 例外 / 违规档 / worktree 流程 / Bash 表 / 测试纪律迁入本节，作为 evidence-first 的"代码探查"配套方法论。
> 归档溯源：`docs/legacy/red-lines-history.md` §6.1。

### N.1 场景矩阵（S1-S6 · 原 §1.2）

**核心原则**：按工作场景分层定义 MCP 使用规则，消除"绝对 MCP 优先"的过度泛化。

| 场景 | 工作场景 | 推荐工具 | 必须性 |
|---|---|---|---|
| **S1** | 接入新代码库（首次理解项目结构） | `get_repo_map` → `get_file_outline` | **必须** |
| **S2** | 探索大文件结构（>500 行，功能未知） | `get_file_outline` + `search_symbols` | 建议 |
| **S3** | 修改已知位置（行号已知或符号已知） | `Read` (offset/limit) **或** `get_symbol_source` | 直接合规 |
| **S4** | 跨文件搜索引用（找调用方/被调用方） | `check_references` / `find_importers` | 建议 |
| **S5** | 跨文件关键字搜索（grep 类） | `search_text` / `search_ast` | 替代 Bash grep |
| **S6** | 失败/不可用时 fallback | `repomix.pack_codebase` | 必须 fallback |

**必须性定义**：
- **必须**：违反触发自检警告，AI 应主动解释为何未用
- **建议**：默认使用，AI 可基于效率判断 fallback
- **直接合规**：任何方式都 OK，不需解释

**工作流（修订版）**：

```
任务开始 → 判断场景
├─ S1 接入新代码库 → 必须 L0 (get_repo_map) → L1 (get_file_outline)
├─ S2 大文件结构   → 建议 L1 (get_file_outline) + L2 (search_symbols)
├─ S3 修改已知位置 → 直接 Read (offset/limit) 或 L2 (get_symbol_source)
├─ S4 跨文件搜索   → 建议 L2 (check_references / find_importers)
├─ S5 跨文件关键字 → 建议 L2 (search_text / search_ast)
└─ S6 MCP 失败     → 必须 fallback (repomix → Read)
```

### N.2 MCP 三件套职责分工（原 §1.3）

| 工具 | 最佳场景 | 兜底场景 | 限制 |
|------|---------|---------|------|
| **jCodeMunch-MCP** | Python 代码（AST 解析） | 任意结构化文件 | 需先 index_folder；worktree 默认未索引 |
| **Repomix** | 任意代码库（含 Markdown） | jcodemunch 索引失败时 | 一次性输出，无增量 |
| **Headroom-ai** | 大段 Markdown / 大文件压缩 | 长会话持续压缩 | hash 检索，不变更内容 |

### N.3 唯一例外（5 条 · 原 §1.4）

| # | 例外场景 | 处理 |
|---|---------|------|
| 1 | MCP 工具全部不可用（报错/超时/未索引） | 记录原因后用 Read，但**仍要尝试 repomix 兜底** |
| 2 | 文件 < 50 行（小配置文件等） | 可直接 Read |
| 3 | 已通过 MCP 定位，需要精确读取 1-3 行 | Read with offset/limit |
| 4 | **执行类操作**（git/cp/rsync/worktree） | 用 Bash，**不算违规** |
| 5 | **JSON/YAML/TOML 小配置**（< 30 行） | Read 全文，**不算违规** |

### N.4 违规判定（4 档 · v6.11 场景感知 · 原 §1.5）

**核心变更**：从"通用阈值"（连续 3 Read、单次 > 100 行）改为"按场景判定"。

| 等级 | 违规行为（按场景） | 自愈方法 |
|------|-------------------|---------|
| 🔴 **红线** | **S1 接入新代码库**未用 `get_repo_map` 直接 Read | 立即重写会话，先用 MCP 探查 |
| 🟠 **严重** | **S5 跨文件关键字搜索**未用 `search_text` 直接 Bash grep | 改用 `search_text` / `search_ast`（或 Read with offset/limit） |
| 🟠 **严重** | worktree 中未先尝试 `index_folder` 直接 Read | 优先 `index_folder(identity_mode="git")`；失败 → repomix 兜底 |
| 🟡 **中等** | MCP 不可用时未尝试 `repomix.pack_codebase` 兜底 | 自动调 repomix 兜底 |
| 🟡 **中等** | 长会话（> 30 轮）未用 `headroom_compress` | 定期压缩大段内容 |
| ✅ **合规** | **S3 修改已知位置**直接 Read（offset/limit） | 不算违规 |
| ✅ **合规** | **S5 单文件 grep** 直接用 Bash | 不算违规（仅限单文件） |
| ✅ **合规** | 文件 < 50 行（沿用 §N.3 例外 2） | 不算违规 |

### N.5 worktree 特殊流程（v6.11 自动化 fallback · 原 §1.7）

**优先级自动反转**：worktree 中默认仍应尝试 MCP（因失败成本低），但失败时**自动**降级 repomix，**不再**算违规。

```bash
# 1. 进入 worktree → 优先尝试 MCP 索引
mcp__jcodemunch__index_folder(
  path=".worktrees/<name>",
  identity_mode="git",        # 关键：让 jcodemunch 识别为同一 git repo
  follow_symlinks=true        # 跟随 git worktree 符号链接
)

# 2. 失败 → 自动 fallback 到 repomix（不报错、不算违规）
mcp__repomix__pack_codebase(directory=".worktrees/<name>")

# 3. 仍失败 → 才 fallback 到 Read with offset/limit（最后手段）

# 4. 验证可解析（仅 S1 接入新代码库场景必须）
mcp__jcodemunch__resolve_repo(path=".worktrees/<name>")
```

**关键差异（vs v6.4）**：
- ✅ "立即索引" → "优先尝试"（失败不阻断）
- ✅ `resolve_repo` 步骤 2 → 步骤 4（仅 S1 场景必须）
- ✅ "失败兜底" → "自动 fallback"（语义降级）
- 🆕 失败时由 repomix 接续，不需 AI 手动判断

### N.6 Bash 探查职责清单（原 §1.8）

| ✅ 允许（执行类） | ❌ 禁止（探查类，应改 MCP/Read） |
|------------------|---------------------------------|
| `git log/show/diff` | `cat < file >` |
| `ls/find`（仅看文件名） | `head -N < file >`（探查内容） |
| `cp/rsync/rm/worktree add` | `grep -rn "pattern" *.py`（探查代码） |
| `git rm/mv/add/commit` | `wc -l < file >`（探查行数） |
| `mkdir/touch/chmod` | `awk/sed`（修改文件） |

### N.7 自查清单（5 项 · 场景感知 · 原 §1.6）

- [ ] **S1 接入新代码库**是否先 `get_repo_map` → `get_file_outline`？（漏斗价值最高）
- [ ] **S3 修改已知位置**是否用 `Read` (offset/limit) 而非 Read 全文？（直接合规）
- [ ] **S4 跨文件搜索**是否优先 `check_references` / `find_importers`？（MCP 强项）
- [ ] **worktree 中**是否先尝试 `index_folder(identity_mode="git")`，失败再 fallback `repomix.pack_codebase`？（自动降级）
- [ ] **长会话**（> 30 轮）是否定期 `headroom_compress` 大段内容？（防止上下文爆炸）

### N.8 测试纪律（L#002 specs 卡死事故 · 原 §1.10）

> **背景**：2026-07-03 specs 安装卡死事故。AI 助手在 5 轮本地测试中**每次都加 `--skip-specs` 跳过**真正的问题，导致"端到端验证通过"但用户实际命令卡死 1 powershell + 7 个 git 子进程，**永不退出**。详细事故链见 `docs/lessons-learned.md` L#002。
>
> **核心混淆**：`git pull` 在远端不存在时**不是 fail** 而是 **hang**（反复重试 TCP/认证）。`if ! cmd` 抓不到，`2>/dev/null` 吞不掉。必须 `timeout N` 主动设上限。

**5 条硬规则**（任何 release/fix PR 涉及 install 或 deploy 改动前必查）：

1. **黄金路径测试纪律**：每个 release/PR 必跑**用户最小命令**（零 flag）端到端至少 1 次。开发期 `--force` / `--skip-specs` / `--only` 等是便利**不是替代**。
2. **区分 fail vs hang**：
   - **失败（sync fail）**：返回非 0 → `if ! cmd` 能捕获
   - **挂起（hang）**：永不返回 → 必须 `timeout N cmd` 主动设上限
   - `2>/dev/null` / `2>&1 | Out-Null` **只吞错误信息，不终止挂起**
3. **测试时禁用开发期 flag**：若加 flag 才"测试通过"，立刻怀疑"用户裸跑会怎样"。"测试通过 ≠ 真实可用"。
4. **脏状态 = 测试失败**：本地有遗留 `~/.xxx/` 脏目录（指向不存在 URL）时跑 deploy 100% 触发 hang。**测试前清环境**应成为肌肉记忆。
5. **加新功能时 red team 自己的设计**：
   - 依赖仓库不存在？远端返回 5xx？网络慢到 timeout？用户在防火墙后？
   - **任何一个没设计降级路径的依赖都是定时炸弹**

**自查清单**（每次写 install/deploy 脚本前）：

- [ ] 是否引入了新的外部依赖（git clone、API、远程服务）？
- [ ] 外部依赖不可达时，脚本是 fail（可控）还是 hang（用户卡死）？
- [ ] 是否给了"如果依赖不存在怎么办"的降级路径（timeout / 默认跳过 / 完全删除）？
- [ ] 本地测试是否至少跑过 1 次"用户裸命令"（无任何 flag）？
- [ ] 本地测试前是否清掉脏目录（`rm -rf` 模拟首次安装）？

> **与 evidence-first 的协同**：本节把"探查阶段用什么工具"（§N.1-N.7）和"测试阶段守什么纪律"（§N.8）完整收录于 evidence-first 方法论之下——两者都属于"证据先行"的前置条件：无证据则无结论，无合规探查/测试则无证据。

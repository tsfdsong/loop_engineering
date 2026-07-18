---
name: loop
description: |
  TRIGGER: 单任务闭环编码 / 自动 gates + 自愈 / '/loop' / '闭环编码' / '单任务'（不用于：多任务并行用 go/subagent-driven-development，纯研究用 deep-research）
  RULE: V2 + V5 主承载 — 闭环内必经验证 Gate（G1-G9）+ 按阶段汇报进度
  DETAIL: 本 SKILL.md（闭环 + gates 流程）+ references/
metadata:
  version: "4.1"
  type: slash-command
  mode: closed-loop-with-git-isolation
---

# /loop — 循环工程全流程命令

你是 `/loop` 命令的执行引擎。用户输入 `/loop [--auto] 功能描述 [验收条件]` 后，自动走完闭环编码流程，不需要用户逐步推动。

## 命令格式

```
/loop [--auto|--lite|--standard|--full] 功能描述，验收条件1，验收条件2，...
/loop --auto 功能描述                  # 纯自动模式（go 调用目标）
/loop --lite 修复分页Bug               # 强制轻量
/loop --full 重构用户模块               # 强制完整
```

## 模式分发（纯规则，零 token）

```
--auto → 🤖 纯自动模式（references/mode-auto.md）
  全程审计闸门 · 不等用户确认 · 门禁全绿自动合并
  go 调用 loop 时固定走此模式

默认  → 🟢🟡🔴 自适应（references/mode-default.md）
  复杂度评估 → 按级别裁剪全流程
  内部使用 A+D 引擎做验收条件推理和自信度闸门
```

## 用户交互硬规则 🔴

loop 在任何需要用户确认的地方，**必须且只能**使用以下交互方式：

1. **选择框交互**：使用 `AskUserQuestion` 工具，以选项列表呈现
2. **推荐项必标注**：第一个选项为推荐项，标注 `(推荐)`，描述中说明推荐理由
3. **其他选项必说明**：每个非推荐选项的描述中说明不推荐或需谨慎的理由
4. **禁止自由文本输入**：不允许要求用户"直接回车"、"输入数字"、"输入你的想法"等开放式交互
5. **禁止开放式追问**：不允许"你觉得呢？"、"还需要什么？"等需要用户组织语言回答的提问

违反以上任何一条 → 视为阻塞 Bug，必须自愈修复。

## 核心原则（两种模式通用）

1. **断点续跑**：状态文件持久化，中断后可恢复
2. **门禁矩阵不可跳过**：G0-G9, F1-F5, G10，每个 ❌ 必须进自愈闭环
3. **不降级红线**：禁止静默删减功能、降低验收标准
4. **Git 隔离不妥协**：遵循 using-git-worktrees，保护主分支
5. **验证证据标准化**：可复现、有数据、有对比、可追溯
6. **每轮输出结构化门禁报告**：含每维度通过/失败状态和自愈处置
7. **新增文件自动 git add + commit，不 push**；commit 前必须通过 **G9 代码审查**（调用 `code-reviewer` 技能）

   🆕 v6.1 桥接模式（opt-in）:
   ```
   export LOOPENGINE_BRIDGES=alpha
   /loop --reviewer=subagent-dd ...
   └─ G9 = subagent-dd 三阶段循环
        (implementer → spec reviewer → code quality reviewer)
   └─ 桥接失败自动降级到 code-reviewer
   └─ 详见 shared/references/g9-g10-coordination.md
   ```
8. **G10 系统审查在 go 中执行，不在 loop 重复触发**：loop 只读 `handoff.gate_result` 字段展示 G10 结果，不重复调用 `system-review` 技能
9. **合并需用户确认**（--auto 模式除外）
10. **🔴 MCP 红线（最高优先级）**：遵循 AGENTS.md §1（v6.11 S1-S6 场景矩阵）的单点真源。本技能**不重复承载**红线全文，仅作行为约束：探查代码结构按 S1-S6 选层，S3 修改已知位置可直接 Read(offset/limit) 属合规。违规判定以 AGENTS.md §1.5 为准。

---

## 门禁按 L 级别裁剪（v2.0 编排层重构 · D4.2）

> v2.0 起 loop 门禁不再"一刀切全跑"。按 go Step ① L0 评估的级别裁剪 · 降低单任务通过门槛 · 提升完成度（痛点 4 解法）。

### 三级门禁表

| L 级别 | 跑哪些门禁 | 适用场景 | 通过门槛 |
|---|---|---|---|
| **L1**（轻量）| G0（环境预检）+ G1（语法）+ G9（代码审查）| 单文件小修 / 行号已知 / 简单 bug fix / 文档改动 | 3 核心门禁全过 |
| **L2**（标准 · 默认）| G0-G9（10 个门禁）| 默认复杂度 / 多文件改动 / 中等重构 | 10 门禁全过 |
| **L3**（完整）| G0-G9 + F1-F5（前端验证）+ G10（系统审查）| 跨模块 / 架构级 / 新功能 / 含前端改动 | 15+ 门禁全过 |

### go 调用 loop 时的级别传递

go Step ① L0 评估结果决定 loop 的门禁级别：

```
/go --level=L1 单文件修复         # 强制 L1（3 门禁）
/go --level=L2 中等重构           # 强制 L2（10 门禁）
/go --level=L3 跨模块新功能       # 强制 L3（15+ 门禁）
/go 功能描述                       # 自动评估（L1/L2/L3）
```

### loop 内部如何按级别裁剪

- **L1**：跳过 G2-G8（不跑测试 / 不跑架构审查 / 不跑跨模块）· 只保 G0/G1/G9
- **L2**：跑 G0-G9（默认）· 跳过 F1-F5 / G10（前端验证与系统审查交 go Step ⑦.5）
- **L3**：跑全部 G0-G9 + F1-F5（前端验证）· G10 由 go 触发（不在 loop 内）

### 与 supervisor 的协同

- supervisor 监控 loop 的门禁通过情况
- 门禁失败 → supervisor 触发 R1 重启（最多 2 次）
- loop exhausted → supervisor 触发 R2 降级（最多 1 次）

详见 `skills/supervisor/SKILL.md`。

### 反模式（禁止）

- ❌ 跳过 G0（环境预检 · 即使 L1 也必须跑）
- ❌ 跳过 G9（代码审查 · 即使 L1 也必须跑）
- ❌ 自降级别（L3 任务标记为 L1 以求快速通过）

## 流程详情

- **纯自动模式**: `references/mode-auto.md`
- **默认模式**: `references/mode-default.md`
- **A+D 引擎**: `references/acceptance-inference.md`

## 共享组件

| 组件 | 文件 | 内容 |
|------|------|------|
| 门禁矩阵 | `references/gate-matrix.md` | G0-G9, F1-F5, G10 维度定义、启用规则、报告格式 |
| 自愈闭环 | `references/self-healing.md` | A/B/C/🎨 分级触发、阻塞保护、exhausted 终态 |
| 前端验证协议 | `references/frontend-verification.md` | 四阶段验证、@ref 规则、agent-browser MCP 工具表 |
| **环境配置** | `references/agent-browser-setup.md` | agent-browser 安装、MCP 配置、G0 预检、故障排查 |
| 经验库协议 | `references/experience-library.md` | 注入时机、匹配规则、沉淀时机、维护规则 |
| 状态管理 | `references/state-protocol.md` | .loop-state-*.json 格式、断点恢复、并发检测 |

## 环境前置（G0 门禁）

涉及前端验证（F1-F5）的任务，**必须**先确保 agent-browser 环境就绪：

```bash
bash skills/loop/scripts/check-agent-browser.sh
```

预检通过（exit 0）→ 继续；失败（exit 1）→ 阻塞，按提示修复后重跑。
详见 `references/agent-browser-setup.md`。

## 与其他命令的区别

| 命令 | 适用场景 |
|------|----------|
| `/loop 功能 条件` | 端到端新功能开发，有明确验收标准 |
| `/loop --auto 功能` | go 编排子任务，或确定需求的快速执行 |
| brainstorming | 纯需求探索，不写代码 |

---

## §N. 进度汇报模板（v2.0 强化 · V5 主承载 · 默认输出格式）

### 触发条件（满足任一）
- 长任务（≥10 步工具调用）
- 多文件改动（≥5 个文件）
- 跨 skill 编排（go 调度 ≥2 个 skill）
- 调用 subagent

### 模板（固定格式）

```markdown
## 📊 进度汇报 (N/M)
- **已完成**：[步骤列表 · 简短]
- **当前阶段**：[具体阶段名]
- **下一步**：[即将做什么]
- **阻塞**：[如有 · 未阻塞则填"无"]
- **预计剩余**：[X 步 / Y 分钟]
```

### 节奏
- 每 5-10 步或每主要阶段完成时输出
- 禁止 >30 分钟静默

### 豁免
- 单步任务（1-2 工具调用）
- 短任务（<5 步 / <1 分钟）
- 用户明确"不需要进度"

与 V5 进度汇报红线协同：本 skill 提供"何时汇报+模板"的方法论。

### 与"摘要输出红线"的协调（吸收原 AGENTS.md §6.5 · v2.0 迁移）

> **来源**：原 AGENTS.md §6.5（v1.0.6+ · 909 行结构）。v2.0 AGENTS.md 精简为 V5 一句话铁律，"进度 vs 摘要"协调段迁入本节末尾，澄清两者不冲突。
> 归档溯源：`docs/legacy/red-lines-history.md` §5.6 + §5.4。

- **进度汇报（进度 = 中途）**：**中途**节奏控制（每 5-10 步）— 短促、状态型，让用户知道 AI 还活着、走到哪、何时完
- **摘要输出（摘要 = 结束）**：**任务结束**结构化摘要（## 📌 核心摘要）— 完整、决策型，让用户能基于结果做下一步决策
- **两者不冲突**：进度汇报简短、按节奏插入；任务结束时归入完整摘要，不在末尾再重复进度细节

> 一句话区分（与摘要红线协调）：**进度汇报回答"现在到哪了"，摘要回答"做完了意味着什么"**。

### 违规判定（吸收原 AGENTS.md §6.6 · v2.0 迁移）

- **满足触发条件但 > 30 分钟无任何状态输出** → 🔴 红线违规（"假死感"痛点回归）
- **仅转述"还在做"、"差不多了"等模糊措辞** → 🔴 红线违规 → 必须用上方固定模板结构（含 N/M 计数 + 当前阶段 + 下一步 + 阻塞 + 预计剩余 5 字段）
- **与完成前验证红线冲突时优先级**：**完成前验证（诚信端 · C1） > 进度汇报（运行端 · V5）** — 若验证证据与进度节奏冲突，先保诚信（宁可慢一步报进度，也不可未经验证宣称完成）

---

## §N. 端到端示例（v2.0 强化）

### 示例 1：L2 单任务闭环（修分页 bug）

**用户输入:** `/loop --level=L2 修复用户列表分页 bug · 验收：第 2 页能正确显示`

**loop 流程（L2 标准 · G0-G9）：**

1. **G0 环境预检**: ✅ agent-browser 已装（前端验证可能用到）
2. **G1 语法/lint**: 定位 `src/users/list.tsx:45` · 发现 `pageSize=NaN`（API 返回 null 未兜底）→ 改为 `pageSize=10`
3. **G2-G3 单元测试**: 写 `list.test.tsx`（覆盖 pageSize=null/undefined/正常值 3 case）→ `npm test` → ✅ 全绿
4. **G4-G6 集成**: `npm run test:integration`（含路由 + API mock）→ ✅
5. **G7 性能**: 无回归（render 时间 12ms → 11ms · 在噪声范围）
6. **G8 文档**: 更新 CHANGELOG（fix: 用户列表分页 pageSize 兜底）
7. **G9 代码审查**: 调用 `code-reviewer` skill → ✅（无 nits）
8. commit + 报告

**自愈场景（G3 失败 → 自愈 A 级）：**
- G3 首次跑：test 红（mock 未模拟 null 返回）
- 自愈分级 → **A 级**（单点修复 · test mock 补 null case）
- 重跑 G3 → ✅ 绿 → 继续 G4

**交付**: gate_result 全绿 · commit `fix(users): pagination pageSize fallback` · 等待合并确认（非 --auto 模式）

### 示例 2：L3 跨模块新功能（go 调用 · F1-F5 触发）

**go 派发:** `/loop --auto --level=L3 实现 orders 创建接口 · 含前端表单`

**loop 流程（L3 完整 · 15+ 门禁）：**

1. G0 环境预检 ✅ → G1 语法 ✅ → G2-G3 后端单测 ✅
2. G4-G6 集成（API + DB）✅
3. **F1-F5 前端验证**（L3 触发）:
   - F1: agent-browser 打开 `/orders/new` → 表单渲染 ✅
   - F2: 填表提交 → API 201 ✅
   - F3-F5: 视觉回归 + a11y + 响应式 ✅
4. G7 性能（首屏 LCP < 2.5s）✅
5. G8 文档（API spec 更新）✅
6. G9 代码审查 ✅
7. **G10 不在 loop 跑**（交 go Step ⑦.5）
8. commit + handoff（gate_result 传 go）

**关键差异（vs 示例 1）:** L3 多跑 F1-F5 前端验证 · G10 交 go · handoff 传 gate_result · --auto 模式自动合并不等确认

# loop 默认模式（薄执行环）

用户输入 `/loop 功能，验收条件` 时触发。目标：验收齐全时尽快进入 **编码 ↔ 门禁 ↔ 自愈 ↔ 交付**。

**不做**：需求理解确认 Ask、复杂度/轮次 Ask、writing-plans 级计划拆分。

---

## 轻量补验收（仅缺可测验收时）

当用户**未提供**可测验收条件或条件过于模糊时，可选调用 A+D 仅补短清单（详见 `references/acceptance-inference.md`）：

1. 按功能类型补默认验收条件模板（短清单）
2. **默认审计闸门**：不 Ask「需求理解是否正确」
3. 补完即进入 Git 隔离 + 编码

模糊到无法执行（纯选型 / 「要不要做 X」）→ 一句提示走 brainstorming 或 `/go`，不进入长确认流。

### 默认验收条件模板（补齐用）

| 功能类型 | 关键词 | 自动补全的默认验收条件 |
|----------|--------|----------------------|
| **通用** | 所有功能 | ① 单元测试通过（覆盖率 ≥ 80%）② 无回归 Bug |
| **API/接口** | API、接口、端点、REST | + 响应时间 < 200ms、+ 错误码规范、+ 输入参数校验 |
| **数据库** | 数据库、表、迁移、存储 | + 数据完整性校验、+ 迁移可回滚、+ 无 N+1 查询 |
| **前端/UI** | 页面、组件、UI、前端 | + 组件可访问性、+ 响应式适配、+ 加载/空/错误三态 |
| **性能优化** | 性能、加速、优化、慢 | + Benchmark对比、+ 无内存泄漏、+ P99 < 目标值 |
| **安全相关** | 安全、权限、加密、认证 | + OWASP检查、+ 敏感数据不落盘、+ 权限边界测试 |
| **重构** | 重构、重写、改进、清理 | + 行为不变(回归通过)、+ 圈复杂度下降 |

---

## 执行流程（对齐设计 §4.1）

```
/loop 触发
    │
    ▼
Step ⓪ 断点续跑检测
  • 检查 .loop-state-<分支slug>.json
  • 存在 → AskUserQuestion:
    问题: "检测到未完成的loop任务：[功能名]，如何处理？"
    ┌─────────────────────────────────────────────────┐
    │ 【推荐】从断点恢复                               │
    │   已完成部分门禁轮次，恢复后继续编码与验证        │
    │ 【备选】放弃并重新开始                           │
    │   丢弃状态文件，按当前输入重新执行                │
    └─────────────────────────────────────────────────┘
  • 不存在 → 新建状态文件，进入 Step ①
  │
  ▼
Step ① 解析目标 + 可选补验收
  • 提取功能描述、验收条件、技术栈
  • 验收齐全 → 直接下一步
  • 验收缺失 → 轻量 A+D 补短清单（默认不 Ask）
  • 明显未定型 → 提示 brainstorming /go，停止
  • L 级别：--level / --lite|--standard|--full / 默认 L2
  • 最多内部 1–3 条改动要点（不落计划文件、不问用户）
  │
  ▼
Step ② Git 隔离（遵循 using-git-worktrees）
  • 检测当前是否已在隔离环境
  • 已在 worktree → 复用
  • 在普通 checkout → git worktree add loop/<slug>-<MMDD>
  │
  ▼
Step ③ 闭环编码（详见 references/gate-matrix.md + references/self-healing.md）
  每 Round = Implement → GitCheck → 门禁矩阵 → 自愈闭环 → Decide

  • 门禁矩阵: 按 L 级别裁剪（见 SKILL.md）
  • 自愈闭环: 门禁失败 → A/B/C/🎨 分级触发
  • Decide:
    ✅ 门禁全绿 → success，进入 Step ③.5 验证官
    🟡 连续2轮无进展 → stagnated → AskUserQuestion
    🔴 exhausted → AskUserQuestion
  │
  ▼
Step ③.5 验证官独立验证（🆕 v6.12 · 三层防御 B 层）
  门禁全绿后，派 verification-officer subagent 做独立验证：
  • 不复用 implementer 上下文，从零验证（解决"既写又验"利益冲突）
  • 按 task_type 路由验证策略（frontend/api/backend/script/config）
  • 验证官写 .verify-state/<SID>/verdict.json（Stop hook 的判据）

  判定:
    ✅ VERIFIED → 进入 Step ④ 交付
    ❌ FAILED → 回到 Step ③ 自愈（修代码后重派验证官）
    ⛔ BLOCKED → AskUserQuestion（环境问题）
    ❓ NEEDS_CONTEXT → AskUserQuestion（问用户验证方式）
  │
  ▼
Step ④ 交付
  • 按 L 裁剪：L1 快速 verification；L2+ code-reviewer + verification；L3 可加文档产出
  • 经验复盘沉淀 → loop-library/lessons/

  AskUserQuestion:
    问题: "所有验收条件已通过，如何处理代码？"
    ┌─────────────────────────────────────────────────┐
    │ 【推荐】合并到主分支                             │
    │   门禁全绿，回归通过                             │
    │ 【备选】保留分支                                 │
    │   代码保留在 [分支名]，供手动审查后合并            │
    │ 【备选】丢弃改动                                 │
    │   放弃所有修改，回到原始分支状态                  │
    └─────────────────────────────────────────────────┘
  │
  ▼
✅ 完成
```

## L 级别对照（替代旧「复杂度 Ask」）

| 来源 | 行为 |
|------|------|
| `--lite` / `--level=L1` | 强制 L1 门禁 |
| `--standard` / `--level=L2` / 默认 | L2 |
| `--full` / `--level=L3` | L3 |
| go 传入 | **消费**传入 L，不重新评估 |

| 维度 | L1 | L2（默认）| L3 |
|------|:--:|:--:|:--:|
| 断点续跑 | ✅ | ✅ | ✅ |
| 补验收（仅缺时） | ✅ | ✅ | ✅ |
| 需求确认 Ask | ❌ | ❌ | ❌ |
| 计划拆分 / writing-plans | ❌ | ❌ | ❌ |
| Git 隔离 | ✅ | ✅ | ✅ |
| 门禁矩阵 | G0/G1/G9 | G0-G9 | G0-G9+F1-F5 |
| 自愈闭环 | ✅ | ✅ | ✅ |
| 合并决策 | AskUserQuestion | AskUserQuestion | AskUserQuestion |

## 手动覆盖

```
/loop --lite 修复分页Bug     → 强制 L1
/loop --full 重构用户模块      → 强制 L3
/loop --standard 添加导出功能  → 强制 L2
```

## 典型示例

| 用户输入 | 路径 |
|---------|------|
| `修复用户列表分页错位，验收：第2页正确` | 验收齐 → 直入编码+门禁 |
| `给订单加导出 CSV`（无验收） | 轻量补验收 → 编码 |
| `要不要做积分系统？` | 提示 brainstorming /go，不执行 |

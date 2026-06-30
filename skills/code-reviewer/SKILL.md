---
name: code-reviewer
description: "Use when reviewing code, requesting review, or processing review feedback. Triggers on 'CR', 'review', '审查', '代码审查', 'code review'. Do NOT use for: system-wide architecture review (use system-review), or improving code quality (use refactoring)."
metadata:
  version: "2.0"
  type: skill
  sources:
    - community (anthropics code-reviewer)
    - superpowers (requesting-code-review + receiving-code-review)
  merged_from:
    - code-reviewer
    - requesting-code-review
    - receiving-code-review
  merge_date_v2: "2026-06-29"
  merge_date_v2_1: "2026-06-30"  # v6.4 重组为 4 阶段工作流
  merge_reason: |
    v6.1.1 三合一合并 → 仍是堆叠；v6.4 重组为 4 阶段工作流（提交前自查 → 请求审查 → 接收反馈 → 闭环修复），
    真正从"CR 全流程"角度融合而非简单拼接。
  review_level: code
  scope: per-subtask
  invoked_by:
    - loop (gate G9)
    - manual user request
  not_invoked_by: go (go 调 system-review，不调本技能)
---

# Code Reviewer 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

代码审查（CR）是 4 个阶段的**循环工作流**，不是一次性动作：

```
┌─────────────────────────────────────────────────────────┐
│ Stage 1: 提交前自查 (Self-Review)                       │
│   ↓ 通过                                                 │
│ Stage 2: 请求审查 (Request Review)                      │
│   ↓ 收到反馈                                             │
│ Stage 3: 接收审查 (Receive Review)                      │
│   ↓ 决策: 接受 / 反驳 / 询问                            │
│ Stage 4: 闭环修复 (Fix & Verify)                        │
│   ↓ 通知审查者确认                                       │
│ （回到 Stage 1，准备下一轮）                             │
└─────────────────────────────────────────────────────────┘
```

**调用入口**：
- **Stage 1 自动触发**：`loop` 命令 G9 门禁 / 用户主叫
- **Stage 2-4 手动触发**：用户完成实现后进入 CR 循环

---

## Stage 1 · 提交前自查（Self-Review）

> 核心原则：**提交前自己先审查一遍**，减少来回次数。

### 1.1 静态分析

- [ ] **类型检查**：`mypy --strict` / `tsc --noEmit` 通过
- [ ] **Lint**：`eslint` / `ruff` / `pylint` 无 error
- [ ] **格式化**：`prettier` / `black` 已应用
- [ ] **死代码**：`vulture` / `knip` 检测无未使用导出
- [ ] **依赖漏洞**：`npm audit` / `pip-audit` 无 high/critical

### 1.2 测试覆盖

- [ ] **单测**：覆盖率 ≥ 80%（关键路径 100%）
- [ ] **集成测试**：跨模块路径有覆盖
- [ ] **边界**：空、零、null、超大值有测试
- [ ] **失败路径**：异常/超时/取消有测试

### 1.3 安全自查

- [ ] **OWASP Top 10**：注入/XSS/CSRF/SSRF 已防
- [ ] **敏感数据**：密钥/token 不在代码中、不在日志中
- [ ] **输入验证**：所有外部输入有白名单校验
- [ ] **依赖安全**：第三方库无已知漏洞

### 1.4 文档同步

- [ ] **API 文档**：Swagger/OpenAPI 自动生成
- [ ] **README**：使用方式/部署/配置已更新
- [ ] **CHANGELOG**：破坏性变更/新功能有记录
- [ ] **ADR**：重要架构决策有记录

### 1.5 自我质疑清单

| 维度 | 自我提问 |
|------|---------|
| **可读性** | 半年后回来看能立即理解吗？ |
| **可测试性** | 关键逻辑能 mock 出来单测吗？ |
| **可维护性** | 改一处会不会引发连锁改动？ |
| **可观测性** | 出问题时能从日志/指标定位吗？ |
| **性能** | 有 N+1 / 不必要的 IO / 重复计算吗？ |
| **安全** | 攻击面是否最小？ |

> **全部通过 → 进入 Stage 2。任一项不通过 → 先修复再提交。**

---

## Stage 2 · 请求审查（Request Review）

> 核心原则：**Review early, review often**。一次提交越早审查，问题越早发现。

### 2.1 何时必须请求审查

**强制**：
- 完成 subagent-driven-development 的每个 task 后
- 完成主要功能后
- 合并到 main 前
- 重大架构变更后

**可选但有价值**：
- 卡住时（获取新视角）
- 重构前（基线检查）
- 修复复杂 bug 后

### 2.2 如何请求

**Step 1：获取 git SHA**

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # 或 origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**Step 2：派发审查 subagent**

```
用 Task 工具 + general-purpose 类型，填充模板：

DESCRIPTION: {一句话总结你构建了什么}
PLAN_OR_REQUIREMENTS: {它应该做什么 + 验收标准}
BASE_SHA: {起始 commit}
HEAD_SHA: {结束 commit}
```

**Step 3：基于反馈行动**

| 反馈级别 | 行动 |
|---------|------|
| **Critical** | 立即修复（阻塞合并） |
| **Important** | 处理后继续 |
| **Minor** | 记录，后续处理 |
| **反驳** | 用技术理由推回（见 Stage 3） |

### 2.3 集成到工作流

| 工作流 | 审查时机 |
|-------|---------|
| **Subagent-Driven Development** | 每个 task 后 |
| **Executing Plans** | 每个 task 或自然检查点 |
| **Ad-Hoc Development** | 合并前 + 卡住时 |

### 2.4 Red Flags

- ❌ "太简单"跳过审查
- ❌ 忽略 Critical 反馈
- ❌ 未修 Important 就继续
- ❌ 与有效技术反馈争辩

---

## Stage 3 · 接收审查（Receive Review）

> 核心原则：**技术正确性 > 社交舒适度。** 不表演同意。

### 3.1 响应模式（强制）

```
WHEN 收到审查反馈:
  1. READ   — 完整读完，不立即反应
  2. RESTATE — 用自己话复述需求（不清就问）
  3. VERIFY  — 与代码库现实核对
  4. EVALUATE — 对本项目技术正确？
  5. RESPOND — 技术确认 / 推回 / 询问
  6. IMPLEMENT — 一次一项，每项测一次
```

### 3.2 禁止的回复（红线）

| ❌ 禁止 | ✅ 替代 |
|--------|--------|
| "You're absolutely right!" | 直接复述需求 / 直接开干 |
| "Great point!" / "Excellent!" | 沉默 / 技术确认 |
| "Thanks for catching that!" | "Fixed. [简述改了什么]" |
| "Let me implement that now" | 先 VERIFY 再行动 |
| "好建议" | 沉默 / 直接改 |

### 3.3 来源差异化处理

#### 来自人类合作伙伴
- **可信** — 理解后实现
- **仍要问** — 范围不清时
- **不表演同意**
- **直接行动** 或技术确认

#### 来自外部审查者

实现前必查 5 问：
1. 对本项目技术正确吗？
2. 会破坏现有功能吗？
3. 当前实现有理由吗？
4. 在所有平台/版本都工作吗？
5. 审查者了解完整上下文吗？

#### 何时推回（Push Back）

| 推回时机 | 推回方式 |
|---------|---------|
| 破坏现有功能 | 用技术理由 + 测试证明 |
| 审查者缺上下文 | 补充信息后让 ta 重审 |
| 违反 YAGNI | 引用功能使用数据 |
| 技术上对当前栈错 | 引用文档/标准 |
| 与人类合作伙伴决策冲突 | **停下，先讨论** |

### 3.4 不清晰反馈的处理

```
IF 任一项不清晰:
  STOP — 不实现任何东西
  ASK — 询问不清晰项

WHY: 项可能互相关联。部分理解 = 错误实现。
```

### 3.5 常见错误

| 错误 | 修正 |
|------|------|
| 表演同意 | 复述需求或直接开干 |
| 盲目实现 | 先 VERIFY 代码库现实 |
| 批量无测试 | 一次一项，每项测一次 |
| 假设审查者对 | 检查是否破坏 |
| 避免推回 | 技术正确 > 舒适 |
| 部分实现 | 先全部问清楚 |

---

## Stage 4 · 闭环修复（Fix & Verify）

> 核心原则：**审查的价值在修复中兑现**，改完不算完，要验证 + 通知。

### 4.1 修复纪律

- **一次修一项** — 不批量（避免引入新问题）
- **每项测一次** — 不堆到最后测
- **测试先行** — 改前先写失败测试（防回归）
- **不改无关代码** — 范围控制

### 4.2 验证清单

每修一项后必过：

- [ ] **单测通过**：相关测试已更新 + 通过
- [ ] **Lint 通过**：无新增 warning
- [ ] **类型通过**：mypy/tsc 仍 strict
- [ ] **集成测试**：跨模块路径仍正常
- [ ] **自审查**：Stage 1 的 5 类检查仍全过

### 4.3 通知审查者

修复后回到 Stage 2 末：

```
回复模板：

@审查者

✅ Critical 已修：[简述]
✅ Important 已修：[简述]
📝 Minor 已记录：[issue 链接 / 后续 TODO]
🔄 反驳结果：[对推回项的决定 + 理由]

请求重新审查（重点：是否仍有阻塞？）。
```

### 4.4 决策树：何时合并

```
所有反馈都已处理（接受/反驳/记录）
├─ 是 → CI 全绿
│   └─ 是 → ✅ 合并
└─ 否 → 还有阻塞项 → 回到 Stage 4 继续修
```

---

## 4 阶段工作流总览

```
┌──────────────────────────────────────────────────────────┐
│ Stage 1 自查:                                             │
│   静态分析 + 测试覆盖 + 安全自查 + 文档同步 + 5 维自问    │
│   ↓ 自查通过                                              │
│ Stage 2 请求:                                              │
│   获取 SHA + 派发 subagent + 基于反馈分级行动              │
│   ↓ 收到反馈                                              │
│ Stage 3 接收:                                              │
│   READ → RESTATE → VERIFY → EVALUATE → RESPOND           │
│   ↓ 决策                                                  │
│ Stage 4 修复:                                              │
│   一次一项 + 每项测 + 验证清单 + 通知审查者               │
│   ↓ 反馈已闭环                                            │
│ （下一轮 Stage 1 / 合并）                                  │
└──────────────────────────────────────────────────────────┘
```

---

## 与其他技能配合

| 场景 | 配合技能 |
|------|---------|
| 自动化单测覆盖 | `testing`（TDD 红绿重构） |
| 系统级审查 | `system-review`（项目/架构级） |
| 上线前全量审计 | `production-readiness`（生产就绪检查） |
| 调试测试失败 | `systematic-debugging` |
| 事实校验 | `evidence-first`（不基于假设下结论） |

---

## 局限

- **不替代环境特定验证** — 不同项目有不同规范
- **不替代实际测试** — 自动化检查无法替代人工判断
- **不替代人工审查** — 复杂业务逻辑需架构师/产品经理

---

## 迁移说明

- v6.1.1 合并前：code-reviewer + requesting-code-review + receiving-code-review 三个独立技能
- v6.1.1 合并后：code-reviewer 一个超级技能（三部分英文原文堆叠）
- **v6.4 重组**：从堆叠 → 4 阶段 CR 工作流（提交前自查 → 请求审查 → 接收反馈 → 闭环修复）
- 保留 code-reviewer 名字以兼容 loop G9 引用（避免修改 loop 代码）
- skill-hub 调度表已同步

---
name: verification-before-completion
description: |
  TRIGGER: 即将声称工作完成/已修复/测试通过 / 提交前 / 创建 PR 前（必须先跑验证命令并确认输出，evidence before assertions）（不用于：设计/探索/纯调研类无完成声明的任务）
  RULE: C1 + C5 + V1 主承载 — 完成前必跑验证命令 + Token 感知 + 摘要式输出
  DETAIL: 本 SKILL.md（验证清单）+ AGENTS.md §C1 §C5 §V1
---

# Verification Before Completion（完成前验证）

## Overview（概述）

未经验证就宣称工作完成是不诚实，不是效率。

**核心原则：** 永远先证据后宣称。

**违反此规则的字面即违反此规则的精神。**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

没在**本条消息**里跑过验证命令，就不能宣称它通过。

## Gate Function（闸门函数）

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

（识别：什么命令能证明这个宣称？→ 运行：完整执行（新鲜的、完整的）→ 阅读：全量输出、查退出码、数失败数 → 验证：输出是否支持宣称？否 → 带证据陈述实际状态；是 → 带证据做宣称 → 然后才做宣称。跳过任一步 = 撒谎，不是验证。）

## 常见失败

| 宣称 | 需要 | 不够 |
|-------|----------|----------------|
| 测试通过 | 测试命令输出：0 失败 | 上一次的运行、"应该会过" |
| Linter 干净 | Linter 输出：0 错误 | 部分检查、外推 |
| 构建成功 | 构建命令：exit 0 | Linter 过了、日志看着行 |
| bug 已修 | 复现原症状的测试：通过 | 代码改了、假设修好了 |
| 回归测试有效 | 红绿循环已验证 | 测试跑过一次 |
| agent 已完成 | VCS diff 显示改动 | agent 报告"成功" |
| 需求已满足 | 逐条清单核对 | 测试通过 |

## Red Flags —— 停下

- 用 "should"、"probably"、"seems to"
- 验证前表达满意（"Great!"、"Perfect!"、"Done!" 等）
- 未验证就要 commit/push/PR
- 信任 agent 的成功报告
- 依赖部分验证
- 想着"就这一次"
- 累了想赶紧收工
- **任何未跑验证就暗示成功的措辞**

## 合理化防范

| 借口 | 现实 |
|--------|---------|
| "现在应该可以了" | **去跑**验证 |
| "我有信心" | 信心 ≠ 证据 |
| "就这一次" | 无例外 |
| "Linter 过了" | Linter ≠ 编译器 |
| "agent 说成功了" | 独立验证 |
| "我累了" | 疲劳 ≠ 借口 |
| "部分检查够了" | 部分证明不了任何事 |
| "换个说法规则就不适用" | 精神高于字面 |

## 关键模式

**测试：**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**回归测试（TDD 红绿）：**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**构建：**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**需求：**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**agent 委派：**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## 为什么重要

来自 24 条失败记忆：
- human partner 说 "I don't believe you" —— 信任崩塌
- 未定义函数被发布 —— 必然崩溃
- 缺失需求被发布 —— 功能不完整
- 虚假完成 → 返工重定向 → 浪费时间
- 违反："诚实是核心价值。你撒谎，就会被替换。"

## 何时应用

**永远在以下之前：**
- 任何形式的成功/完成宣称
- 任何满意表达
- 任何关于工作状态的正面陈述
- commit、建 PR、宣布任务完成
- 进入下一任务
- 委派给 agent

**规则适用于：**
- 精确措辞
- 转述与同义词
- 成功的暗示
- **任何**暗示完成/正确的沟通

## The Bottom Line（底线）

**验证没有捷径。**

跑命令。读输出。**然后**才宣称结果。

这不可协商。

---

## 前后端联调验证（v6.12 补充 · 补 Gap 4）

> 本节补全原 SKILL.md 缺失的前后端联调场景。协议详情见 `loop/references/frontend-verification.md`。

涉及前端/UI/页面/交互类功能时，**必须**执行四阶段协议——不能只跑后端测试就宣称完成：

```
阶段0: 环境就绪（G0 + G1）
  agent-browser ≥ 0.29.0 + Chrome 可用 + 前后端服务已启动

阶段1: 页面加载断言
  agent_browser_open(targetUrl) → agent_browser_snapshot
  断言: 页面标题/路由正确，无全局错误边界

阶段2: 三件套采集 + 自动断言（这是判据，不是截图）
  errors   = agent_browser_errors           → error 数量 = 0  （F1 红线）
  network  = agent_browser_network_requests  → 全部 2xx/3xx   （F2 红线）
  snapshot = agent_browser_snapshot          → 验收元素全命中  （F3）

阶段3: 交互流执行（F4）
  对每个用户操作流: snapshot → @ref → click/fill → snapshot → 断言
  每步采集 console + network → 断言

阶段4: 汇总 → 全绿才可宣称完成
```

**关键红线**：
- **截图仅留证，程序化断言才是判据**（errors=0 + 网络状态码 + snapshot 元素命中）
- **禁止肉眼截图判断**（"看起来没问题"不等于 errors=0）
- **禁止"点了没崩就算过"**（每步必须有 snapshot 断言）
- **登录态必须实际完成**（方案A脚本内置 / 方案B auth vault / 方案C Chrome profile），不能假设已登录

---

## 验证 Gate 机制（v6.12 · 三层防御）

> 本项目已部署**机器级**验证 Gate（不再是纯 prompt 级软约束）。

### 三层防御架构

| 层 | 机制 | 强制力 |
|---|---|---|
| **D 证据文件** | `.verify-state/<SID>/verdict.json` | 真相源，可审计 |
| **B 验证官** | `verification-officer` subagent 独立验证 | 解决利益冲突 |
| **A Stop hook** | `hooks/verify-gate.sh` 机器阻断 | AI 无法绕过 |

### 工作流

```
AI 改代码（Edit/Write）
  → PostToolUse hook 标记 has_code_changes=true
  → 派验证官 subagent → 写 verdict.json
  → AI 尝试停止
  → Stop hook 读 verdict.json:
      VERIFIED → 放行
      FAILED → 阻断（exit 2，强制修复后重验）
      缺失   → 阻断（exit 2，"必须先派验证官"）
      阻断 ≥3 次 → 软警告放行（防无限循环）
```

### 与本技能的关系

- **本技能** = 文化层（"NO COMPLETION CLAIMS WITHOUT EVIDENCE"的 prompt 级铁律）
- **Gate 机制** = 机器层（Stop hook 硬拦截 + 验证官独立验证）
- **两者互补**：文化层管 AI 的意图，机器层管 AI 的行为。即使 AI 想跳过验证，Stop hook 也会阻断

> 详见 `hooks/verify-gate.sh` + `skills/verification-officer/SKILL.md`

---

## §N. 长会话 Token 管理（v2.0 强化 · C5 主承载）

### 触发条件
- 长会话（>20 轮）
- 单次任务 >10 文件改动
- 单次工具输出累积 >500 行

### 必须动作（任一）
- 用 `headroom_compress` 压缩大段内容
- 主动总结前文（输出 `## 📌 阶段小结` 结构化摘要）
- 用 TodoWrite 清理已完成项（保持上下文聚焦）

### 避免上下文爆炸
- 长会话不压缩 → 输出质量下降（各种能力模型均如此）
- 能力较弱模型尤其敏感（决策分母过大）
- 与 C5 Token 感知红线协同：本 skill 提供"何时压缩+如何压缩"的方法论

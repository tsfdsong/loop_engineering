---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

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

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Why This Matters

From 24 failure memories:
- your human partner said "I don't believe you" - trust broken
- Undefined functions shipped - would crash
- Missing requirements shipped - incomplete features
- Time wasted on false completion → redirect → rework
- Violates: "Honesty is a core value. If you lie, you'll be replaced."

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.

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

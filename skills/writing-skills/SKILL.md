---
name: writing-skills
description: |
  TRIGGER: 创建新 skill / 编辑现有 skill / 部署前验证 skill 可用性
  RULE: no specific rule（方法论 skill · skill 编写方法论）
  DETAIL: 本 SKILL.md（skill 结构 + 元数据 + 验证流程）+ references/skill-spec.md（详细规范）
---

# Writing Skills

## Overview

**Writing skills IS Test-Driven Development applied to process documentation.**

**Personal skills live in agent-specific directories (`~/.claude/skills` for Claude Code, `~/.agents/skills/` for Codex)**

You write test cases (pressure scenarios with subagents), watch them fail (baseline behavior), write the skill (documentation), watch tests pass (agents comply), and refactor (close loopholes).

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

**REQUIRED BACKGROUND:** You MUST understand superpowers:test-driven-development before using this skill. That skill defines the fundamental RED-GREEN-REFACTOR cycle. This skill adapts TDD to documentation.

**Official guidance:** For Anthropic's official skill authoring best practices, see anthropic-best-practices.md. This document provides additional patterns and guidelines that complement the TDD-focused approach in this skill.

## What is a Skill?

A **skill** is a reference guide for proven techniques, patterns, or tools. Skills help future Claude instances find and apply effective approaches.

**Skills are:** Reusable techniques, patterns, tools, reference guides

**Skills are NOT:** Narratives about how you solved a problem once

## TDD Mapping for Skills

| TDD Concept | Skill Creation |
|-------------|----------------|
| **Test case** | Pressure scenario with subagent |
| **Production code** | Skill document (SKILL.md) |
| **Test fails (RED)** | Agent violates rule without skill (baseline) |
| **Test passes (GREEN)** | Agent complies with skill present |
| **Refactor** | Close loopholes while maintaining compliance |
| **Write test first** | Run baseline scenario BEFORE writing skill |
| **Watch it fail** | Document exact rationalizations agent uses |
| **Minimal code** | Write skill addressing those specific violations |
| **Watch it pass** | Verify agent now complies |
| **Refactor cycle** | Find new rationalizations → plug → re-verify |

The entire skill creation process follows RED-GREEN-REFACTOR.

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious to you
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)
- Others would benefit

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (put in CLAUDE.md)
- Mechanical constraints (if it's enforceable with regex/validation, automate it—save documentation for judgment calls)

## Skill Types

### Technique
Concrete method with steps to follow (condition-based-waiting, root-cause-tracing)

### Pattern
Way of thinking about problems (flatten-with-flags, test-invariants)

### Reference
API docs, syntax guides, tool documentation (office docs)

## Directory Structure


```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Only if needed
```

**Flat namespace** - all skills in one searchable namespace

**Separate files for:**
1. **Heavy reference** (100+ lines) - API docs, comprehensive syntax
2. **Reusable tools** - Scripts, utilities, templates

**Keep inline:**
- Principles and concepts
- Code patterns (< 50 lines)
- Everything else

## SKILL.md Structure (核心要点)

**Frontmatter 必填两字段：** `name`（只用字母/数字/连字符）+ `description`（第三人称、以 "Use when..." 开头、只述何时用不述做什么、尽量 <500 字符、总 frontmatter ≤1024 字符）。

**主干段落骨架：** Overview（核心原则 1-2 句）→ When to Use（症状/用例 + 何时不用）→ Core Pattern（before/after）→ Quick Reference（表）→ Implementation（inline 或链接）→ Common Mistakes。

> 完整结构模板、字段细节、good/bad YAML 示例、token 效率技巧、交叉引用规范 → **见 `references/skill-spec.md` § SKILL.md 结构模板 + § Claude Search Optimization**。

## Claude Search Optimization（CSO）— 要点

**发现性关键：** 未来的 Claude 需要能**找到**你的 skill。

**铁律：Description = When to Use，NOT What the Skill Does。** description 概述工作流会形成 Claude 走的捷径，导致它跳过 skill 主体。测试已证实此退化模式。

**核心技巧：**
- 以 "Use when..." 开头，只给触发条件，绝不概述工作流
- 用具体触发器/症状/场景（技术无关，除非 skill 技术特定）
- Keyword coverage：覆盖错误消息、症状、同义词、工具名
- Descriptive naming：动词在前、主动语态（`creating-skills` > `skill-creation`）
- Token efficiency：getting-started <150 词、高频 <200 词、其他 <500 词
- **不用 `@` 链接**引用其他 skill（会强制加载烧 context）；用 `**REQUIRED BACKGROUND:** Use <skill-name>` 形式

> 完整 good/bad YAML 对比、token 压缩示例、命名规则、cross-reference 规范 → **见 `references/skill-spec.md` § Claude Search Optimization**。

## Flowchart Usage — 要点

**只在以下场景用 flowchart：** 不明显的决策点、可能提前停下的循环、"A vs B" 决策。

**绝不用于：** reference 材料（用表/列表）、代码示例（用 markdown 块）、线性指令（用编号列表）、无语义标签。

graphviz 样式见 @graphviz-conventions.dot；渲染 SVG 见本目录 `render-graphs.js`。

> 完整决策 flowchart + 何时用 markdown vs inline flowchart → **见 `references/skill-spec.md` § Flowchart Usage**。

## Code Examples — 要点

**一个优秀示例胜过一堆平庸示例。** 选最相关语言（测试→TS/JS、系统调试→Shell/Python、数据→Python）。好示例：完整可运行、注释解释 WHY、来自真实场景、可改造（非填空模板）。不要多语言实现、不要捏造示例。

> 完整 do/don't 列表 → **见 `references/skill-spec.md` § Code Examples**。

## File Organization — 要点

三种形态：**Self-Contained**（全 inline）、**Skill with Reusable Tool**（SKILL.md + example 代码）、**Skill with Heavy Reference**（SKILL.md + 600 行 API ref + scripts/）。

> 完整目录结构示例 → **见 `references/skill-spec.md` § File Organization**。

## The Iron Law (Same as TDD)

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

This applies to NEW skills AND EDITS to existing skills.

Write skill before testing? Delete it. Start over.
Edit skill without testing? Same violation.

**No exceptions:**
- Not for "simple additions"
- Not for "just adding a section"
- Not for "documentation updates"
- Don't keep untested changes as "reference"
- Don't "adapt" while running tests
- Delete means delete

**REQUIRED BACKGROUND:** The superpowers:test-driven-development skill explains why this matters. Same principles apply to documentation.

## Testing All Skill Types — 要点

不同 skill 类型测不同维度：

| 类型 | 测什么 | 成功标准 |
|---|---|---|
| **Discipline-Enforcing**（规则） | 学术问题 + 压力场景 + 多重压力叠加 | 最大压力下仍守规则 |
| **Technique**（how-to） | 应用 + 变体 + 信息缺失 | 成功应用到新场景 |
| **Pattern**（心智模型） | 识别 + 应用 + 反例 | 正确识别何时/如何用 |
| **Reference**（文档/API） | 检索 + 应用 + 空白 | 找到并正确应用信息 |

> 每类的完整测试方法、场景示例 → **见 `references/skill-spec.md` § Testing All Skill Types**。

## Common Rationalizations for Skipping Testing

| Excuse | Reality |
|--------|---------|
| "Skill is obviously clear" | Clear to you ≠ clear to other agents. Test it. |
| "It's just a reference" | References can have gaps, unclear sections. Test retrieval. |
| "Testing is overkill" | Untested skills have issues. Always. 15 min testing saves hours. |
| "I'll test if problems emerge" | Problems = agents can't use skill. Test BEFORE deploying. |
| "Too tedious to test" | Testing is less tedious than debugging bad skill in production. |
| "I'm confident it's good" | Overconfidence guarantees issues. Test anyway. |
| "Academic review is enough" | Reading ≠ using. Test application scenarios. |
| "No time to test" | Deploying untested skill wastes more time fixing it later. |

**All of these mean: Test before deploying. No exceptions.**

## Bulletproofing Skills Against Rationalization — 要点

执行纪律的 skill（如 TDD）必须抗合理化。核心 5 招：

1. **显式封堵每个漏洞** — 不只陈述规则，显式禁止具体规避（"delete means delete / 不留 reference / 不边测边改"）
2. **切断"精神 vs 字面"争论** — 早期立基础原则："违反字面即违反精神"
3. **建合理化表** — 从基线测试捕获每个借口入表（Excuse | Reality）
4. **建 Red Flags 列表** — 让 agent 自检（"this is different because..." = STOP）
5. **CSO 加违规症状** — description 里标"即将违规"的症状

**心理学基础：** 权威/承诺/稀缺/社会认同/归属感原则（研究基础见 persuasion-principles.md）。

> 完整 good/bad 对比、Red Flags 模板、CSO 违规症状示例 → **见 `references/skill-spec.md` § Bulletproofing Skills Against Rationalization**。

## RED-GREEN-REFACTOR for Skills

Follow the TDD cycle:

### RED: Write Failing Test (Baseline)

Run pressure scenario with subagent WITHOUT the skill. Document exact behavior:
- What choices did they make?
- What rationalizations did they use (verbatim)?
- Which pressures triggered violations?

This is "watch the test fail" - you must see what agents naturally do before writing the skill.

### GREEN: Write Minimal Skill

Write skill that addresses those specific rationalizations. Don't add extra content for hypothetical cases.

Run same scenarios WITH skill. Agent should now comply.

### REFACTOR: Close Loopholes

Agent found new rationalization? Add explicit counter. Re-test until bulletproof.

**Testing methodology:** 完整方法（压力场景写法、压力类型、系统性堵漏洞、元测试）见 @testing-skills-with-subagents.md。

## Anti-Patterns — 要点

四类禁止：**Narrative Example**（太具体不可复用）、**Multi-Language Dilution**（多语言平庸实现）、**Code in Flowcharts**（不能复制粘贴）、**Generic Labels**（无语义）。

> 完整反例 + why bad → **见 `references/skill-spec.md` § Anti-Patterns**。

## STOP: Before Moving to Next Skill

**After writing ANY skill, you MUST STOP and complete the deployment process.**

**Do NOT:**
- Create multiple skills in batch without testing each
- Move to next skill before current one is verified
- Skip testing because "batching is more efficient"

**The deployment checklist below is MANDATORY for EACH skill.**

Deploying untested skills = deploying untested code. It's a violation of quality standards.

## Skill Creation Checklist (TDD Adapted)

**IMPORTANT: Use TodoWrite to create todos for EACH checklist item below.**

**RED Phase - Write Failing Test:**
- [ ] Create pressure scenarios (3+ combined pressures for discipline skills)
- [ ] Run scenarios WITHOUT skill - document baseline behavior verbatim
- [ ] Identify patterns in rationalizations/failures

**GREEN Phase - Write Minimal Skill:**
- [ ] Name uses only letters, numbers, hyphens (no parentheses/special chars)
- [ ] YAML frontmatter with required `name` and `description` fields (max 1024 chars; see [spec](https://agentskills.io/specification))
- [ ] Description starts with "Use when..." and includes specific triggers/symptoms
- [ ] Description written in third person
- [ ] Keywords throughout for search (errors, symptoms, tools)
- [ ] Clear overview with core principle
- [ ] Address specific baseline failures identified in RED
- [ ] Code inline OR link to separate file
- [ ] One excellent example (not multi-language)
- [ ] Run scenarios WITH skill - verify agents now comply

**REFACTOR Phase - Close Loopholes:**
- [ ] Identify NEW rationalizations from testing
- [ ] Add explicit counters (if discipline skill)
- [ ] Build rationalization table from all test iterations
- [ ] Create red flags list
- [ ] Re-test until bulletproof

**Quality Checks:**
- [ ] Small flowchart only if decision non-obvious
- [ ] Quick reference table
- [ ] Common mistakes section
- [ ] No narrative storytelling
- [ ] Supporting files only for tools or heavy reference
- [ ] **主干 SKILL.md ≤ 500 行**（详细规范挪到 `references/` · v2.0 硬规则）

**Deployment:**
- [ ] Commit skill to git and push to your fork (if configured)
- [ ] Consider contributing back via PR (if broadly useful)

## Discovery Workflow

How future Claude finds your skill:

1. **Encounters problem** ("tests are flaky")
3. **Finds SKILL** (description matches)
4. **Scans overview** (is this relevant?)
5. **Reads patterns** (quick reference table)
6. **Loads example** (only when implementing)

**Optimize for this flow** - put searchable terms early and often.

## references/

| 文档 | 内容 |
|------|------|
| **`references/skill-spec.md`** | 🆕 v2.0 拆分 · 详细规范（结构模板 / CSO / flowchart / code examples / file org / testing / rationalization / RED-GREEN-REFACTOR / anti-patterns） |
| `anthropic-best-practices.md` | Anthropic 官方 skill 编写最佳实践 |
| `testing-skills-with-subagents.md` | 完整 subagent 测试方法（压力场景 / 堵漏洞 / 元测试） |
| `persuasion-principles.md` | 说服原则研究基础（Cialdini 等） |
| `graphviz-conventions.dot` | graphviz 样式规则 |
| `render-graphs.js` | flowchart → SVG 渲染脚本 |

## The Bottom Line

**Creating skills IS TDD for process documentation.**

Same Iron Law: No skill without failing test first.
Same cycle: RED (baseline) → GREEN (write skill) → REFACTOR (close loopholes).
Same benefits: Better quality, fewer surprises, bulletproof results.

If you follow TDD for code, follow it for skills. It's the same discipline applied to documentation.

> **详细规范（格式/长度/字数/具体写法/测试方法/反模式）一律 lazy load 自 `references/skill-spec.md`。本主干只保留入口 + 流程 + 关键检查清单。**

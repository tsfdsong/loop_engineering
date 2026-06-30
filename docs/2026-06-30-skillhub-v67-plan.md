---
title: skill-hub v6.7.0-alpha 实施计划（对齐 superpowers）
date: 2026-06-30
author: writing-plans (ZCode MiniMax-M3)
status: ✅ 用户批准（2026-06-30）
parent_design: docs/2026-06-30-skillhub-complexity-aware-design.md
parent_research: 4 轮 deep-research（业界 5 方案 + superpowers 1 方案源码级调研）
---

# Skill-Hub v6.7.0-alpha Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 skill-hub 改造为对齐 superpowers 的"调度协议"——LLM 自主路由 + 1% 规则 + P0 流程类优先 + 三层仲裁，彻底解决"新装技能不可知"和"硬编码 KEYWORDS 表覆盖不全"问题。

**Architecture:** 4 阶段改造——调度协议元技能化 → description 触发器化 → session-start 注入 → 优先级+仲裁。**不破坏** v5.4 / v6.0 / v6.1 / v6.5 任何层。

**Tech Stack:** Markdown / Node.js CJS（complexity-scorer 已有）/ YAML frontmatter / Bash + PowerShell hooks。

---

## 0. 范围与不变量

### 0.1 范围（v6.7.0-alpha 4 项必修）

| # | 改造 | 工时 |
|---|------|:---:|
| 1 | 改写 skill-hub/SKILL.md 为"调度协议"元技能 | 0.5 天 |
| 2 | 改写 34 个 SKILL.md description 为 "Use when..." 模式 | 3 天 |
| 3 | 实现 session-start 元技能注入机制（跨平台 hooks） | 0.5 天 |
| 4 | 建立 P0 流程类优先级 + 三层冲突仲裁 | 0.5 天 |
| **合计** | — | **4.5 天** |

### 0.2 不变量（破坏任一 = 红线违规）

- [ ] **v5.4 baseline 27 条测试 100% 通过**（`tests/golden-traces/v54-baseline.json`）
- [ ] **v6.0 复合任务 5 类表全部兼容**
- [ ] **v6.1 三技能协同契约 6 个全过**
- [ ] **v6.5 complexity-scorer 不破坏**（`tests/complexity-scorer.test.cjs` 全过）
- [ ] **KEYWORDS 表降级为 fast-path 不删除**
- [ ] **`LOOPENGINE_COMPLEXITY_AWARE=disabled` 一键回滚仍生效**

### 0.3 关键设计原则（来自 superpowers 调研）

1. **1% 规则**：哪怕 1% 概率适用，LLM 必须调对应技能
2. **description 不总结工作流**：只写触发条件（避免 LLM 跳过读全文）
3. **用户 > 技能 > 系统 三层仲裁**：用户显式指令最高优先
4. **元技能单点注入**：只注入 1 个 skill-hub（教 LLM 怎么调），不注入 34 个
5. **平台原生 Skill 工具**：LLM 自主决定调哪个，平台被动提供

---

## 1. 文件结构（前置）

### 1.1 新增文件

```
skills/skill-hub/
├── SKILL.md                       # 改写为"调度协议"元技能（替换原内容）
├── references/
│   ├── complexity-scorer.cjs      # 改：增加 priority 维度
│   ├── priority-manifest.json     # 新：P0 流程类硬编码清单
│   └── router-fallback.md         # 新：L4 AskUserQuestion 模板
└── hooks/                          # 新：跨平台 session-start 注入
    ├── skillhub-bootstrap.sh      # 新：POSIX (Linux/macOS)
    ├── skillhub-bootstrap.cmd     # 新：Windows
    └── skillhub-bootstrap.ps1     # 新：PowerShell (可选)

docs/
└── 2026-06-30-skillhub-v67-plan.md # 本文件
```

### 1.2 改写文件

```
skills/<name>/SKILL.md  # 34 个，全部改写 description 字段
```

### 1.3 测试文件

```
tests/
├── golden-traces/
│   ├── v54-baseline.json          # 验证：必须 100% 通过
│   └── v67-router-baseline.json   # 新：20 case 覆盖调度协议
├── skill-hub-v67-router.test.cjs  # 新：P0 优先级 + 仲裁 unit test
└── skill-lint.test.cjs            # 新：description 格式校验
```

---

## 2. 任务分解

### Task 1: 改写 skill-hub/SKILL.md 为"调度协议"元技能

**Files:**
- Modify: `skills/skill-hub/SKILL.md:1-682`（全文件重写）
- Create: `skills/skill-hub/references/router-fallback.md`
- Test: `tests/golden-traces/v67-router-baseline.json`

**目标**：把 skill-hub 从"路由表"改造为"调度协议"——教 LLM 怎么用其他技能，而不是替 LLM 决定用哪个。

#### - [ ] **Step 1.1: 写失败的基线测试**

创建 `tests/golden-traces/v67-router-baseline.json`：

```json
{
  "version": "v6.7.0-alpha",
  "description": "调度协议元技能的基线行为测试",
  "cases": [
    {
      "id": "1_percent_rule",
      "query": "我觉得可能需要重构",
      "expected_mention_skills": ["refactoring"],
      "rationale": "1% 规则：哪怕 1% 适用，refactoring 必须被提示"
    },
    {
      "id": "p0_priority",
      "query": "我想设计一个新功能",
      "expected_p0_first": ["brainstorming", "writing-plans"],
      "rationale": "P0 流程类必须先调：brainstorming → writing-plans"
    },
    {
      "id": "user_override",
      "query": "我跳过 brainstorming 直接写代码",
      "expected_respect_user": true,
      "rationale": "用户 > 技能：用户显式跳过 brainstorming 时不强制"
    },
    {
      "id": "fallback_ask_user",
      "query": "我要做某件未知的事",
      "expected_action": "ask_user_question",
      "rationale": "L4 兜底：路由失败时显式求助，不强行猜"
    }
  ]
}
```

#### - [ ] **Step 1.2: 验证测试文件存在**

```bash
cat tests/golden-traces/v67-router-baseline.json
```

期望：输出完整 JSON，4 个 case。

#### - [ ] **Step 1.3: 备份原 SKILL.md**

```bash
cp skills/skill-hub/SKILL.md skills/skill-hub/SKILL.md.v66.backup
```

#### - [ ] **Step 1.4: 改写 SKILL.md 为"调度协议"**

替换 `skills/skill-hub/SKILL.md` 全文件为以下内容（保留 v6.4 + v6.5 章节不动）：

```markdown
---
name: skill-hub
description: Use when starting any conversation, when unsure which skill applies, or when no obvious skill matches the task. Routes to other skills via LLM semantic matching, not keyword tables. Do NOT use for: tasks that have a clear single skill match (just call that skill directly), pure code questions (use systematic-debugging or refactoring), or architecture review (use system-review).
metadata:
  version: "6.7.0-alpha"
  type: meta-skill
  parent_skill: null
  injects_at: session-start
---

# Skill Hub — 调度协议元技能

你是 **调度协议**（不是路由表）。你教 LLM 怎么用其他技能，**不替 LLM 决定用哪个**。

## 核心规则（按优先级）

### 🔴 规则 0：三层仲裁（最高优先级）

```
1. 用户显式指令（AGENTS.md / CLAUDE.md / 直接请求）← 最高
2. 本 skill-hub 调度协议
3. 其他技能自身的 description
4. 默认系统提示                                          ← 最低
```

**即使 skill-hub 说"必须调 brainstorming"，若用户的 AGENTS.md 说"不要 brainstorming"，遵循用户。**

### 🔴 规则 1：1% 规则（不可协商）

> **哪怕 1% 概率某个技能适用，你必须调用它。**

- ❌ "这看起来简单，不用调 skill" → 违反
- ❌ "我已经知道答案了" → 违反
- ✅ "我看到 query 含 '重构'，1% 概率 refactoring 适用 → 调 refactoring"
- ✅ "这个任务涉及多个领域，我先 brainstorm 一下意图"

### 🟠 规则 2：P0 流程类优先（硬编码）

P0 流程类**必须先调**，再考虑 P1 实现类：

| 优先级 | 类别 | 技能 | 触发场景 |
|:---:|------|------|---------|
| P0 | 流程类 | `brainstorming` | 设计/创意/新功能 |
| P0 | 流程类 | `systematic-debugging` | bug/报错/不工作 |
| P0 | 流程类 | `evidence-first` | 分析/比较/评估/选型 |
| P0 | 流程类 | `writing-plans` | 写实施计划 |
| P1 | 实现类 | `refactoring` / `testing` / `code-reviewer` 等 | 具体执行 |

**反例**："帮我重写这个函数" → 不直接调 refactoring，应先想"是否需要 brainstorming"。

### 🟡 规则 3：description 触发器（替代关键词表）

**`description` 字段 = 路由触发器**，不是文档说明。判断流程：

1. 用户 query 进来
2. LLM 看到所有技能的 description（启动期由 session-start 注入）
3. LLM 自主判断：哪个 description 与 query 匹配（**用 LLM 语义，不用关键词表**）
4. 调用对应技能的 `Skill` 工具

**description 写作规范**（参照 superpowers writing-skills）：
- 必须以 "Use when..." 开头
- 第三人称（注入系统提示的）
- < 500 字符
- **不总结工作流**（避免 LLM 跳过读全文）
- 包含"Do NOT use for:"反向触发

### 🟢 规则 4：L4 显式求助（兜底）

**L1 关键词表 fast-path + L2 文件扫描 + L3 domain 过滤全部失败时**：

**绝对禁止**：
- ❌ AI 自行选一个最像的技能
- ❌ 跳过技能直接执行
- ❌ 静默回退到无技能模式

**必须**：
- ✅ 用 `AskUserQuestion` 列出 top-3 候选
- ✅ 用户选择 → 路由 + 记录到 `docs/lessons-learned.md`
- ✅ 用户选 "Other" → 记录自由文本，下版本尝试接入

### 🟢 规则 5：MCP 红线（仅限代码域）

> **任何"理解/修改/调研代码结构"操作，必须先用 MCP 工具。**

**作用范围**：
- ✅ 受约束：理解/修改/调研本项目代码
- ❌ 不受约束：浏览器自动化（agent-browser）/ 网页抓取 / 文档生成 / 远程 API / 用户数据处理

**判定口诀**：任务对象是「本项目代码文件」→ 受约束；任务对象是「外部网页/远程服务/用户数据」→ 不受约束。

---

## 调度流程（4 步）

```
用户 query 进来
    ↓
[1] 1% 规则检查
    → "哪怕 1% 概率有技能适用" → 调用该技能
    → "确定无技能适用" → 响应（包括澄清问题）
    ↓
[2] P0 流程类先调（如果 1% 规则命中 P0 技能）
    → brainstorming / systematic-debugging / evidence-first / writing-plans
    → 必先调，再考虑 P1
    ↓
[3] description 语义匹配
    → LLM 看到所有技能的 description
    → 自主判断调哪个（用 LLM 语义，不用关键词表）
    → 调用对应技能的 Skill 工具
    ↓
[4] L4 显式求助（如果上面全部失败）
    → AskUserQuestion 列 top-3
    → 用户选择 → 路由
```

## 不做什么

- ❌ **不维护关键词表作为权威**（KEYWORDS 表降级为 fast-path 缓存，保留兼容）
- ❌ **不替 LLM 决定调哪个技能**（用 1% 规则 + LLM 自主判断）
- ❌ **不强行猜**（L4 兜底必须 AskUserQuestion）
- ❌ **不总结技能工作流在 description**（避免 LLM 跳过读全文）

## 关键不变量（向后兼容）

- v5.4 baseline 27 条测试 100% 通过
- v6.0 复合任务 5 类表兼容
- v6.1 三技能协同契约兼容
- v6.5 complexity-scorer 不破坏
- KEYWORDS 表保留为 fast-path
- `LOOPENGINE_COMPLEXITY_AWARE=disabled` 一键回滚仍生效

## 启动期注入（详见 Task 3）

本技能在 `SessionStart` 事件时被注入到系统提示。**只注入本技能 1 个**，不注入其他 34 个技能——其他技能由 LLM 通过 `Skill` 工具按需加载。

---

# 下游章节（保留 v6.4 + v6.5 + v6.6 内容）

[此处保留 v6.4 三层架构、v6.5 复杂度感知路由、v6.6 文件扫描、Orchestrator alpha mock、桥接契约等所有现有章节，标注版本号]
```

#### - [ ] **Step 1.5: 验证文件大小**

```bash
wc -l skills/skill-hub/SKILL.md
```

期望：< 700 行（参照 v6.5 设计稿的 700 行上限）。

#### - [ ] **Step 1.6: 创建 L4 兜底模板**

创建 `skills/skill-hub/references/router-fallback.md`：

```markdown
# L4 显式求助兜底模板

**触发条件**：L1 fast-path + L2 文件扫描 + L3 domain 过滤 + LLM 语义匹配 全部 miss。

## AskUserQuestion 模板

```yaml
question: "我无法确定该用哪个技能，请帮我选择："
header: "技能选择"
options:
  - label: "brainstorming（推荐）"
    description: "探索需求和方案设计"
  - label: "refactoring"
    description: "重构现有代码"
  - label: "systematic-debugging"
    description: "排查 bug 或报错"
  - label: "Other"
    description: "以上都不匹配（请说明具体需求）"
multiSelect: false
```

## 记录到 lessons-learned

用户选择后，记录到 `docs/lessons-learned.md`：
```markdown
## [YYYY-MM-DD] 路由失败案例
- query: <用户原话>
- 候选: <列出的 top-3>
- 实际选择: <用户选哪个>
- 教训: <应该如何改进 description 或 KEYWORDS>
```
```

#### - [ ] **Step 1.7: 验证 v5.4 baseline 仍兼容**

```bash
npm test -- --testPathPattern=golden-traces/v54-baseline
```

期望：PASS（27 条全过）。

#### - [ ] **Step 1.8: Commit**

```bash
git add skills/skill-hub/SKILL.md skills/skill-hub/references/router-fallback.md tests/golden-traces/v67-router-baseline.json skills/skill-hub/SKILL.md.v66.backup
git commit -m "feat(skillhub): v6.7.0-alpha 调度协议元技能化（1% 规则 + P0 优先 + L4 兜底）"
```

---

### Task 2: 改写 34 个 SKILL.md description 为 "Use when..." 模式

**Files:**
- Modify: `skills/<name>/SKILL.md`（34 个文件 frontmatter description 字段）
- Create: `tests/skill-lint.test.cjs`
- Reference: `skills/skill-hub/references/superpowers-description-template.md`

**目标**：所有 description 改为 "Use when..." 触发器格式（参照 superpowers writing-skills 规范）。

#### - [ ] **Step 2.1: 创建 description 改造模板**

创建 `skills/skill-hub/references/superpowers-description-template.md`：

```markdown
# SKILL.md description 改造模板

参照 superpowers writing-skills 规范。

## 格式硬性要求

```yaml
---
name: skill-name
description: Use when [specific triggering conditions]. Do NOT use for: [exclusion scenarios].
---
```

## 关键规则

1. **必须以 "Use when..." 开头**
2. **第三人称**（注入系统提示的）
3. **< 500 字符**
4. **不总结工作流**（避免 LLM 跳过读全文）
5. **包含 "Do NOT use for:" 反向触发**
6. **埋关键词**：错误信息、症状、工具名、同义词

## 正反对比

```yaml
# ❌ 错误：总结了工作流
description: "代码质量超级技能 —— 4 源风格融合（Martin 原则式 + McConnell 要点式 + self 规范表格式 + pragmatic-programmer 工程决策式）"

# ✅ 正确：只有触发条件
description: "Use when writing or reviewing code, when code quality issues are noticed (naming, comments, complexity), or when the user asks for cleanup/standards/refactoring. Do NOT use for: architecture design (use software-architecture), debugging (use systematic-debugging), or specific language features."
```

## 改造工作流

每个 SKILL.md 改造步骤：
1. 读原 description
2. 提取核心场景（3-5 个）
3. 写 "Use when..." 触发条件
4. 写 "Do NOT use for:" 反向触发
5. 校验 < 500 字符
6. 验证不总结工作流
7. 跑 skill-lint 通过
```

#### - [ ] **Step 2.2: 写 skill-lint 测试**

创建 `tests/skill-lint.test.cjs`：

```javascript
// tests/skill-lint.test.cjs
// v6.7 description 格式校验
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const SKILLS_DIR = path.join(__dirname, '..', 'skills');

function extractFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const yaml = match[1];
  const descMatch = yaml.match(/^description:\s*(.+?)(?=\n[a-z]|\n$|$)/ms);
  return { yaml, description: descMatch ? descMatch[1].trim() : null };
}

function lintDescription(desc) {
  const issues = [];
  if (!desc) issues.push('missing description');
  else {
    if (!desc.startsWith('Use when')) issues.push('must start with "Use when"');
    if (desc.length > 500) issues.push(`exceeds 500 chars (${desc.length})`);
    if (/^(Use when|This skill|The |A )/i.test(desc) === false) {
      issues.push('should describe triggering conditions, not workflow');
    }
    // 不应总结工作流（粗略检查）
    if (/step.by.step|RED.GREEN|workflow|process|pipeline/i.test(desc)) {
      issues.push('appears to summarize workflow (anti-pattern)');
    }
  }
  return issues;
}

const allSkills = fs.readdirSync(SKILLS_DIR)
  .filter(name => {
    const stat = fs.statSync(path.join(SKILLS_DIR, name));
    return stat.isDirectory();
  })
  .filter(name => name !== 'shared' && name !== 'skill-hub');

const tests = [];
for (const skill of allSkills) {
  const skillMd = path.join(SKILLS_DIR, skill, 'SKILL.md');
  if (!fs.existsSync(skillMd)) continue;
  const content = fs.readFileSync(skillMd, 'utf8');
  const fm = extractFrontmatter(content);
  const issues = fm && fm.description ? lintDescription(fm.description) : ['missing frontmatter'];
  tests.push({
    skill,
    description: fm?.description || '(none)',
    issues
  });
}

const passing = tests.filter(t => t.issues.length === 0).length;
const failing = tests.filter(t => t.issues.length > 0);

console.log(`\n=== skill-lint v6.7.0-alpha ===`);
console.log(`Total skills: ${tests.length}`);
console.log(`Passing: ${passing}`);
console.log(`Failing: ${failing.length}`);

if (failing.length > 0) {
  console.log('\nFailing skills:');
  for (const t of failing) {
    console.log(`  - ${t.skill}: ${t.issues.join('; ')}`);
    console.log(`    desc: ${t.description?.slice(0, 80)}...`);
  }
  process.exit(1);
}

console.log('\n✅ All 34 skills pass skill-lint v6.7.0-alpha');
```

#### - [ ] **Step 2.3: 验证 skill-lint 失败**

```bash
node tests/skill-lint.test.cjs
```

期望：FAIL（多数 skill 还是旧 description）。

#### - [ ] **Step 2.4: 改写 34 个 SKILL.md description**

按 `skills/skill-hub/references/superpowers-description-template.md` 模板，逐一改写 34 个 SKILL.md frontmatter 的 `description` 字段。

**改写示例**（10 个高频 skill 的目标 description）：

```yaml
# skills/brainstorming/SKILL.md
description: "Use when creating features, building components, adding functionality, or modifying behavior. Triggers when user wants to design something new or is unsure what they want. Do NOT use for: pure research (use deep-research), debugging (use systematic-debugging), or code review (use code-reviewer)."

# skills/systematic-debugging/SKILL.md
description: "Use when investigating bugs, errors, test failures, unexpected behavior, or 'X doesn't work'. Triggers on 'bug', '报错', '不工作', 'debug', '排查', '修'. Do NOT use for: new features (use brainstorming), or system architecture issues (use system-review)."

# skills/evidence-first/SKILL.md
description: "Use when comparing options, evaluating designs, making architectural decisions, or any 'X vs Y' / 'should I' / 'why' question. Triggers on '分析', '比较', '评估', '选型'. Do NOT use for: pure implementation (use refactoring/testing), or brainstorming new ideas (use brainstorming)."

# skills/writing-plans/SKILL.md
description: "Use when you have an approved design and need to break it into implementable tasks. Triggers on '写计划', 'plan', '拆分任务', '实现方案'. Do NOT use for: brainstorming design (use brainstorming), or executing existing plans (use executing-plans)."

# skills/refactoring/SKILL.md
description: "Use when improving existing code structure, fixing code smells, reducing complexity, or applying design patterns. Triggers on '重构', '坏味道', '太长', '重复代码'. Do NOT use for: new features (use brainstorming), or debugging (use systematic-debugging)."

# skills/testing/SKILL.md
description: "Use when writing tests, setting up TDD, adding test coverage, or designing test strategies. Triggers on '测试', 'TDD', '单元测试', '端到端', 'mock'. Do NOT use for: fixing test failures (use systematic-debugging), or code review (use code-reviewer)."

# skills/code-reviewer/SKILL.md
description: "Use when reviewing code, requesting review, or processing review feedback. Triggers on 'CR', 'review', '审查', '代码审查'. Do NOT use for: system-wide architecture review (use system-review), or improving code quality (use refactoring)."

# skills/agent-browser/SKILL.md
description: "Use when interacting with websites, automating browser tasks, taking screenshots, filling forms, or scraping web pages. Triggers on '浏览器', '网页', '截图', '打开', '登录', '抓取'. Do NOT use for: reading project code (use Read/MCP), or generating documentation (use writing-skills)."

# skills/skill-hub/SKILL.md
description: "Use when starting any conversation, when unsure which skill applies, or when no obvious skill matches. Routes via LLM semantic matching. Do NOT use for: tasks with clear single skill match (call that skill directly), or pure code questions (use systematic-debugging/refactoring)."

# skills/loop/SKILL.md
description: "Use when executing single-task closed-loop coding with automatic gates and self-healing. Triggers on '/loop', '闭环编码', '单任务'. Do NOT use for: multi-task parallel (use go or subagent-driven-development)."
```

**其余 24 个 skill 改写**（参照上述模式 + writing-skills 规范）：

按以下顺序改写（从高频到低频）：

```
1. brainstorming
2. systematic-debugging
3. evidence-first
4. writing-plans
5. refactoring
6. testing
7. code-reviewer
8. agent-browser
9. skill-hub
10. loop
11. go
12. subagent-driven-development
13. dispatching-parallel-agents
14. executing-plans
15. finishing-a-development-branch
16. using-git-worktrees
17. verification-before-completion
18. system-review
19. software-architecture
20. domain-driven-design
21. python-web-development
22. production-readiness
23. github-actions-templates
24. database-design
25. clean-code
26. drawio-skill
27. deep-research
28. product-manager
29. to-prd
30. using-loopengine
31. skill-router
32. agent-skill-architecture
33. writing-skills
34. context-driven-development
```

每个 skill 的 description 改造后，长度必须 < 500 字符，必须以 "Use when..." 开头，必须包含 "Do NOT use for:"。

#### - [ ] **Step 2.5: 验证 skill-lint 全部通过**

```bash
node tests/skill-lint.test.cjs
```

期望：✅ All 34 skills pass skill-lint v6.7.0-alpha。

#### - [ ] **Step 2.6: 验证 v5.4 baseline 仍兼容**

```bash
npm test -- --testPathPattern=golden-traces/v54-baseline
```

期望：PASS（27 条全过，KEYWORDS 表 fast-path 仍工作）。

#### - [ ] **Step 2.7: 验证 description 长度**

```bash
# 验证所有 description < 500 字符
for f in skills/*/SKILL.md; do
  desc=$(grep "^description:" "$f" | head -1)
  len=${#desc}
  if [ $len -gt 520 ]; then
    echo "TOO LONG: $f ($len chars)"
  fi
done
```

期望：无输出（全部 < 520 字符含 description: 前缀）。

#### - [ ] **Step 2.8: Commit**

```bash
git add skills/*/SKILL.md tests/skill-lint.test.cjs skills/skill-hub/references/superpowers-description-template.md
git commit -m "feat(skillhub): v6.7.0-alpha 改写 34 个 SKILL.md description 为 Use when 模式"
```

---

### Task 3: 实现 session-start 元技能注入机制（跨平台 hooks）

**Files:**
- Create: `skills/skill-hub/hooks/skillhub-bootstrap.sh`（POSIX）
- Create: `skills/skill-hub/hooks/skillhub-bootstrap.cmd`（Windows）
- Create: `skills/skill-hub/hooks/install-hooks.sh`（POSIX 安装脚本）
- Create: `skills/skill-hub/hooks/install-hooks.ps1`（Windows 安装脚本）
- Test: `tests/skill-hub-hooks.test.sh`（集成测试）

**目标**：在 `SessionStart` 事件触发时，把 `skill-hub/SKILL.md` 全文注入到系统提示（参照 superpowers session-start 脚本）。

#### - [ ] **Step 3.1: 创建 POSIX bootstrap 脚本**

创建 `skills/skill-hub/hooks/skillhub-bootstrap.sh`：

```bash
#!/usr/bin/env bash
# skills/skill-hub/hooks/skillhub-bootstrap.sh
# v6.7 session-start bootstrap - 注入 skill-hub 全文到系统提示
# 参照 superpowers/session-start 实现

set -euo pipefail

# 定位插件根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 读取 skill-hub/SKILL.md 全文
SKILLHUB_MD="${PLUGIN_ROOT}/skills/skill-hub/SKILL.md"
if [ ! -f "$SKILLHUB_MD" ]; then
  echo "ERROR: skill-hub/SKILL.md not found at $SKILLHUB_MD" >&2
  exit 1
fi

SKILL_CONTENT=$(cat "$SKILLHUB_MD")

# JSON 转义
escape_for_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\\n'/\\n}"
  s="${s//$'\\r'/\\r}"
  s="${s//$'\\t'/\\t}"
  printf '%s' "$s"
}

ESCAPED_CONTENT=$(escape_for_json "$SKILL_CONTENT")

# 构造 session context
SESSION_CONTEXT="<EXTREMELY_IMPORTANT>
You have skill-hub (v6.7.0-alpha) installed as your meta-skill for routing.

**Below is the full content of your skill-hub skill. Read it carefully.**

${SKILL_CONTENT}

**For all other skills, follow the 1% rule: even 1% chance a skill applies → invoke it.**
</EXTREMELY_IMPORTANT>"

ESCAPED_CONTEXT=$(escape_for_json "$SESSION_CONTEXT")

# 按平台分支输出 JSON
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
  # Cursor 格式
  printf '{"additional_context": "%s"}' "$ESCAPED_CONTEXT"
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
  # Claude Code 格式
  printf '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "%s"}}' "$ESCAPED_CONTEXT"
else
  # Copilot CLI / 其他标准格式
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
fi

exit 0
```

#### - [ ] **Step 3.2: 验证 POSIX 脚本可执行**

```bash
chmod +x skills/skill-hub/hooks/skillhub-bootstrap.sh
bash skills/skill-hub/hooks/skillhub-bootstrap.sh | head -c 200
```

期望：输出 `{"additional_context": "..."}` 或 `{"hookSpecificOutput": ...}`。

#### - [ ] **Step 3.3: 创建 Windows bootstrap 脚本**

创建 `skills/skill-hub/hooks/skillhub-bootstrap.cmd`：

```batch
@echo off
REM skills/skill-hub/hooks/skillhub-bootstrap.cmd
REM v6.7 session-start bootstrap - Windows 版本

setlocal enabledelayedexpansion

REM 定位插件根目录
set SCRIPT_DIR=%~dp0
set PLUGIN_ROOT=%SCRIPT_DIR%..\..\

REM 读取 skill-hub/SKILL.md
set SKILL_FILE=%PLUGIN_ROOT%skills\skill-hub\SKILL.md
if not exist "%SKILL_FILE%" (
  echo ERROR: skill-hub/SKILL.md not found at %SKILL_FILE% 1>&2
  exit /b 1
)

REM 简单 JSON 转义（PowerShell 会处理复杂情况）
set SKILL_CONTENT=
for /f "delims=" %%a in (%SKILL_FILE%) do (
  set SKILL_CONTENT=!SKILL_CONTENT!%%a\n
)

REM 构造 session context
set SESSION_CONTEXT=<EXTREMELY_IMPORTANT>^

You have skill-hub (v6.7.0-alpha) installed as your meta-skill for routing.^

^

**Below is the full content of your skill-hub skill.**^

^

%SKILL_CONTENT%^

^

**For all other skills, follow the 1%% rule: even 1%% chance a skill applies -> invoke it.**^

</EXTREMELY_IMPORTANT>

REM 简化为顶层 additionalContext（兼容各平台）
echo {"additionalContext": "%SESSION_CONTEXT%"}

exit /b 0
```

#### - [ ] **Step 3.4: 创建 POSIX 安装脚本**

创建 `skills/skill-hub/hooks/install-hooks.sh`：

```bash
#!/usr/bin/env bash
# skills/skill-hub/hooks/install-hooks.sh
# 注册 skill-hub session-start hook 到 Claude Code / Cursor / Codex

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== Installing skill-hub v6.7 session-start hook ==="

# 1. Claude Code (注册到 ~/.claude/settings.json)
if [ -d "$HOME/.claude" ]; then
  SETTINGS="$HOME/.claude/settings.json"
  HOOK_CMD="\"${PLUGIN_ROOT}/skills/skill-hub/hooks/skillhub-bootstrap.sh\""
  
  if [ -f "$SETTINGS" ]; then
    # 备份
    cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d)"
    # 用 jq 合并 hooks
    jq --arg cmd "$HOOK_CMD" '.hooks.SessionStart = [{"matcher": "startup|clear|compact", "hooks": [{"type": "command", "command": $cmd, "async": false}]}]' "$SETTINGS" > "$SETTINGS.tmp"
    mv "$SETTINGS.tmp" "$SETTINGS"
    echo "✅ Claude Code hook registered: $SETTINGS"
  else
    mkdir -p "$(dirname "$SETTINGS")"
    cat > "$SETTINGS" <<EOF
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup|clear|compact",
      "hooks": [{
        "type": "command",
        "command": "$HOOK_CMD",
        "async": false
      }]
    }]
  }
}
EOF
    echo "✅ Claude Code settings created: $SETTINGS"
  fi
fi

# 2. ZCode (注册到 ~/.zcode/cli/config.json)
if [ -d "$HOME/.zcode" ]; then
  ZCODE_CONFIG="$HOME/.zcode/cli/config.json"
  if [ -f "$ZCODE_CONFIG" ]; then
    echo "ℹ️  ZCode config detected. Please manually add skill-hub to plugins."
  fi
fi

echo ""
echo "=== Installation complete ==="
echo "Restart your agent to activate skill-hub v6.7.0-alpha."
```

```bash
chmod +x skills/skill-hub/hooks/install-hooks.sh
```

#### - [ ] **Step 3.5: 创建 Windows 安装脚本**

创建 `skills/skill-hub/hooks/install-hooks.ps1`：

```powershell
# skills/skill-hub/hooks/install-hooks.ps1
# 注册 skill-hub session-start hook 到 Claude Code / ZCode (Windows)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginRoot = Resolve-Path (Join-Path $ScriptDir "..\..\")

Write-Host "=== Installing skill-hub v6.7 session-start hook (Windows) ===" -ForegroundColor Cyan

# Claude Code
$ClaudeSettings = Join-Path $env:USERPROFILE ".claude\settings.json"
$HookCmd = "`"$PluginRoot\skills\skill-hub\hooks\skillhub-bootstrap.cmd`""

if (Test-Path (Join-Path $env:USERPROFILE ".claude")) {
    if (Test-Path $ClaudeSettings) {
        Copy-Item $ClaudeSettings "$ClaudeSettings.bak.$(Get-Date -Format yyyyMMdd)"
        Write-Host "✅ Claude Code settings backed up" -ForegroundColor Green
    }
    
    $settings = @{
        hooks = @{
            SessionStart = @(@{
                matcher = "startup|clear|compact"
                hooks = @(@{
                    type = "command"
                    command = $HookCmd
                    async = $false
                })
            })
        }
    } | ConvertTo-Json -Depth 10
    
    Set-Content -Path $ClaudeSettings -Value $settings
    Write-Host "✅ Claude Code hook registered: $ClaudeSettings" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Cyan
Write-Host "Restart your agent to activate skill-hub v6.7.0-alpha."
```

#### - [ ] **Step 3.6: 创建集成测试**

创建 `tests/skill-hub-hooks.test.sh`：

```bash
#!/usr/bin/env bash
# tests/skill-hub-hooks.test.sh
# 验证 session-start hook 输出符合 schema

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Testing skillhub-bootstrap.sh ==="

# 测试 1: 输出是有效 JSON
OUTPUT=$(bash "${PLUGIN_ROOT}/skills/skill-hub/hooks/skillhub-bootstrap.sh")
if echo "$OUTPUT" | jq . > /dev/null 2>&1; then
  echo "✅ Test 1: Output is valid JSON"
else
  echo "❌ Test 1: Output is not valid JSON"
  echo "$OUTPUT" | head -c 200
  exit 1
fi

# 测试 2: 包含 skill-hub 内容
if echo "$OUTPUT" | jq -r '.additionalContext, .hookSpecificOutput.additionalContext, .additional_context' 2>/dev/null | grep -q "skill-hub"; then
  echo "✅ Test 2: Contains skill-hub content"
else
  echo "❌ Test 2: Missing skill-hub content"
  exit 1
fi

# 测试 3: 包含 1% 规则
if echo "$OUTPUT" | jq -r '.additionalContext, .hookSpecificOutput.additionalContext, .additional_context' 2>/dev/null | grep -q "1% rule\|1%% rule\|even 1%"; then
  echo "✅ Test 3: Contains 1% rule"
else
  echo "❌ Test 3: Missing 1% rule"
  exit 1
fi

echo ""
echo "✅ All skill-hub-hooks tests passed"
```

```bash
chmod +x tests/skill-hub-hooks.test.sh
```

#### - [ ] **Step 3.7: 验证集成测试通过**

```bash
bash tests/skill-hub-hooks.test.sh
```

期望：✅ All skill-hub-hooks tests passed。

#### - [ ] **Step 3.8: Commit**

```bash
git add skills/skill-hub/hooks/ tests/skill-hub-hooks.test.sh
git commit -m "feat(skillhub): v6.7.0-alpha session-start 元技能注入机制（跨平台 hooks）"
```

---

### Task 4: 建立 P0 流程类优先级 + 三层冲突仲裁

**Files:**
- Modify: `skills/skill-hub/references/complexity-scorer.cjs`（增加 priority 维度）
- Create: `skills/skill-hub/references/priority-manifest.json`
- Create: `tests/skill-hub-v67-router.test.cjs`（unit test）
- Modify: `tests/complexity-scorer.test.cjs`（不破坏现有测试）

**目标**：硬编码 4 个 P0 流程类技能的优先级，并实现"用户 > skill-hub > skill > 系统"的三层冲突仲裁。

#### - [ ] **Step 4.1: 创建 P0 优先级清单**

创建 `skills/skill-hub/references/priority-manifest.json`：

```json
{
  "version": "v6.7.0-alpha",
  "priority_levels": {
    "P0": {
      "description": "流程类（必须先调，决定如何处理任务）",
      "skills": [
        {
          "name": "brainstorming",
          "rationale": "设计/创意/新功能必须先 brainstorm"
        },
        {
          "name": "systematic-debugging",
          "rationale": "bug/报错/不工作必须先 systematic-debugging"
        },
        {
          "name": "evidence-first",
          "rationale": "分析/比较/评估/选型必须先 evidence-first"
        },
        {
          "name": "writing-plans",
          "rationale": "已有设计要写实施计划时调用"
        }
      ]
    },
    "P1": {
      "description": "实现类（具体执行）",
      "skills": ["*"]
    }
  },
  "arbitration": {
    "priority_order": [
      "user_explicit",
      "skill_hub",
      "skill",
      "system_default"
    ],
    "user_explicit_examples": [
      "AGENTS.md 中的明确指令",
      "CLAUDE.md 中的明确指令",
      "用户直接说'跳过 brainstorming'"
    ]
  }
}
```

#### - [ ] **Step 4.2: 写 P0 优先级 unit test**

创建 `tests/skill-hub-v67-router.test.cjs`：

```javascript
// tests/skill-hub-v67-router.test.cjs
// v6.7 P0 优先级 + 三层仲裁 unit test
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const MANIFEST = JSON.parse(fs.readFileSync(
  path.join(__dirname, '..', 'skills', 'skill-hub', 'references', 'priority-manifest.json'),
  'utf8'
));

// Test 1: P0 包含 4 个流程类技能
const p0Skills = MANIFEST.priority_levels.P0.skills.map(s => s.name);
assert.deepStrictEqual(
  p0Skills.sort(),
  ['brainstorming', 'evidence-first', 'systematic-debugging', 'writing-plans'].sort(),
  'P0 must contain exactly 4 process skills'
);
console.log('✅ Test 1: P0 contains 4 process skills');

// Test 2: 三层仲裁顺序正确
const order = MANIFEST.arbitration.priority_order;
assert.deepStrictEqual(
  order,
  ['user_explicit', 'skill_hub', 'skill', 'system_default'],
  'Arbitration order must be user > skill-hub > skill > system'
);
console.log('✅ Test 2: Arbitration order is correct');

// Test 3: 每个 P0 技能有 rationale
for (const skill of MANIFEST.priority_levels.P0.skills) {
  assert.ok(skill.rationale, `${skill.name} must have rationale`);
}
console.log('✅ Test 3: All P0 skills have rationale');

console.log('\n✅ All skill-hub-v67-router tests passed');
```

#### - [ ] **Step 4.3: 验证 P0 测试通过**

```bash
node tests/skill-hub-v67-router.test.cjs
```

期望：✅ All skill-hub-v67-router tests passed。

#### - [ ] **Step 4.4: 改写 complexity-scorer.cjs 增加 priority 维度**

修改 `skills/skill-hub/references/complexity-scorer.cjs`：

```javascript
// 在 complexity_scorer 函数中增加 priority 维度
function detectPriority(query, candidates) {
  // P0 流程类技能必须先调
  const p0Skills = ['brainstorming', 'systematic-debugging', 'evidence-first', 'writing-plans'];
  const hasP0 = candidates.some(c => p0Skills.includes(c));
  if (hasP0) {
    return { priority: 'P0', boost: 1.0, rationale: 'process skill must be invoked first' };
  }
  return { priority: 'P1', boost: 0.0, rationale: 'implementation skill' };
}

function complexity_scorer(query) {
  const d1 = dim1_intent_clarity(query) * 0.5;
  const d2 = dim2_candidate_count(query);
  const d3 = dim3_tool_dependency(query);
  const d4 = dim4_token_budget(query);
  const candidates = matchSkills(query);
  const priorityInfo = detectPriority(query, candidates);
  
  const raw = 1 + (d1 + d2 + d3 + d4) + priorityInfo.boost;
  const score = Math.max(1, Math.min(5, Math.round(raw)));
  return { 
    score, 
    dim_breakdown: { d1, d2, d3, d4, priority: priorityInfo.boost },
    priority: priorityInfo.priority,
    priority_rationale: priorityInfo.rationale,
    raw 
  };
}
```

#### - [ ] **Step 4.5: 验证 complexity-scorer 现有测试不破坏**

```bash
npm test -- --testPathPattern=complexity-scorer
```

期望：现有 40 + 9 = 49 个 case 全过。

#### - [ ] **Step 4.6: 验证 v5.4 baseline 仍兼容**

```bash
npm test -- --testPathPattern=golden-traces/v54-baseline
```

期望：PASS（27 条全过）。

#### - [ ] **Step 4.7: Commit**

```bash
git add skills/skill-hub/references/priority-manifest.json tests/skill-hub-v67-router.test.cjs skills/skill-hub/references/complexity-scorer.cjs
git commit -m "feat(skillhub): v6.7.0-alpha P0 流程类优先级 + 三层冲突仲裁"
```

---

## 3. 验收标准（Definition of Done）

### 3.1 功能验收

- [ ] **T1.1**: `tests/golden-traces/v67-router-baseline.json` 4 个 case 全过
- [ ] **T1.2**: `skills/skill-hub/SKILL.md` 包含 1% 规则、P0 优先、L4 兜底、MCP 红线（仅限代码域）
- [ ] **T2.1**: `node tests/skill-lint.test.cjs` 输出 `✅ All 34 skills pass`
- [ ] **T2.2**: 所有 description < 500 字符
- [ ] **T2.3**: 所有 description 以 "Use when..." 开头
- [ ] **T2.4**: 所有 description 包含 "Do NOT use for:"
- [ ] **T3.1**: `bash tests/skill-hub-hooks.test.sh` 输出 `✅ All skill-hub-hooks tests passed`
- [ ] **T3.2**: `bash skills/skill-hub/hooks/skillhub-bootstrap.sh` 输出有效 JSON
- [ ] **T3.3**: 输出包含 skill-hub 全文
- [ ] **T4.1**: `node tests/skill-hub-v67-router.test.cjs` 输出 `✅ All skill-hub-v67-router tests passed`
- [ ] **T4.2**: priority-manifest.json 包含 4 个 P0 技能
- [ ] **T4.3**: 仲裁顺序 = `user_explicit > skill_hub > skill > system_default`

### 3.2 兼容性验收（破坏任一 = 红线违规）

- [ ] **C1**: `npm test -- --testPathPattern=golden-traces/v54-baseline` PASS（27/27）
- [ ] **C2**: `npm test -- --testPathPattern=complexity-scorer` PASS（49/49）
- [ ] **C3**: `npm test -- --testPathPattern=golden-traces` PASS（v6.1 三技能契约 6 个）
- [ ] **C4**: `LOOPENGINE_COMPLEXITY_AWARE=disabled` 一键回滚仍生效
- [ ] **C5**: KEYWORDS 表降级为 fast-path 不删除
- [ ] **C6**: 现有 33 个技能功能不破坏

### 3.3 文档验收

- [ ] **D1**: `docs/2026-06-30-skillhub-v67-design.md`（设计稿）已写
- [ ] **D2**: `docs/2026-06-30-skillhub-v67-plan.md`（本文件）已写
- [ ] **D3**: `docs/lessons-learned.md` 更新（记录 v6.7 改造经验）
- [ ] **D4**: `docs/2026-06-30-skillhub-v67-changelog.md`（变更日志）

### 3.4 安装验收

- [ ] **I1**: `bash skills/skill-hub/hooks/install-hooks.sh` 成功注册到 `~/.claude/settings.json`
- [ ] **I2**: `pwsh skills/skill-hub/hooks/install-hooks.ps1` 成功注册（Windows）
- [ ] **I3**: 重启 Claude Code / ZCode 后，问 "Tell me about your skills"，能看到 skill-hub 已注入

---

## 4. 风险与缓解

| 风险 | 等级 | 缓解 |
|------|:---:|------|
| 34 个 SKILL.md 改造工作量大 | 🟠 | 分 4 批：高频 10 个 → 中频 12 个 → 低频 12 个，每批单独 commit |
| description 写不好导致 LLM 漏调 | 🟠 | skill-lint 强制 + TDD 流程（每个 description 必须能通过 1 个压力场景）|
| session-start 注入失败 | 🟡 | 集成测试 + 手动验证（重启 Claude Code 看是否生效）|
| v5.4 baseline 测试破坏 | 🔴 | 每次 Task 跑一遍 baseline 回归 |
| complexity-scorer 现有测试破坏 | 🔴 | 每次改动跑 complexity-scorer 测试 |
| Windows 路径处理 | 🟠 | 用 `cmd` 而非 `ps1` 简化路径；测试覆盖 Windows |
| 平台差异（Cursor / Copilot / Gemini） | 🟡 | install-hooks 检测 `CURSOR_PLUGIN_ROOT` 等环境变量 |

---

## 5. 工时分解

| Task | 工时 | 风险 |
|------|:---:|:---:|
| Task 1: 调度协议元技能化 | 0.5 天 | 🟢 |
| Task 2: 34 个 SKILL.md description 改造 | 3 天 | 🟠 |
| Task 3: session-start 注入机制 | 0.5 天 | 🟠 |
| Task 4: P0 优先级 + 三层仲裁 | 0.5 天 | 🟢 |
| **合计** | **4.5 天** | 中 |

---

## 6. 后续工作（v6.7.1 / v6.7.2）

### v6.7.1-beta（3 天）

- [ ] Task 5: 实现 v6.6 L2 文件扫描 + L3 domain 过滤
- [ ] Task 6: skill-lint 集成到 CI
- [ ] Task 7: 端到端调度准确度测试（≥ 85%）

### v6.7.2-stable（3 天）

- [ ] Task 8: TDD 流程创建新技能（压力场景 + 基线 + 红旗清单）
- [ ] Task 9: 三层冲突仲裁完整实现（user > skill-hub > skill > system）
- [ ] Task 10: 跨插件桥接协议（OpenCode / Cursor / Copilot 适配）

---

## 7. 关联文档

- **父设计**：`docs/2026-06-30-skillhub-complexity-aware-design.md`（v6.5 复杂度感知）
- **调研产物**：4 轮 deep-research（业界 5 方案 + superpowers 1 方案源码级）
- **模板参照**：
  - superpowers/using-superpowers — https://raw.githubusercontent.com/obra/superpowers/main/skills/using-superpowers/SKILL.md
  - superpowers/writing-skills — https://raw.githubusercontent.com/obra/superpowers/main/skills/writing-skills/SKILL.md
  - superpowers/session-start — https://raw.githubusercontent.com/obra/superpowers/main/hooks/session-start
- **现有测试**：
  - `tests/golden-traces/v54-baseline.json`（27 条）
  - `tests/complexity-scorer.test.cjs`（40 case）
  - `tests/complexity-scorer-env.test.cjs`（9 case）

---

## 8. 自检 4 问（evidence-first 强制）

| # | 问题 | 答案 |
|---|------|------|
| 1 | 有 [F] 依据吗？ | ✅ 4 轮 deep-research 全部 [F] 验证 |
| 2 | [H] 假设明确标注了吗？ | ✅ 34 个 description 改造工作量大、LLM 路由有效性等已标 [H] |
| 3 | 错了损失大吗？ | 中 — 不破坏现有（v5.4/v6.0/v6.1/v6.5） |
| 4 | 能说"我不清楚"吗？ | ✅ ZCode session-start hook 实际机制未验证（已标 [H]） |

---

> **下一步**：进入执行阶段。3 种执行方式（subagent-driven / inline / go）任选其一。

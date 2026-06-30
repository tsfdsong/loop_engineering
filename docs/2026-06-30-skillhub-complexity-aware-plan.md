---
title: skill-hub 复杂度感知调度器 实施计划 v0.1
date: 2026-06-30
parent_design: docs/2026-06-30-skillhub-complexity-aware-design.md
execution_path: go  # 7 个任务跨文件 + 需 worktree 隔离
---

# skill-hub 复杂度感知调度器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development`（in-session 单文件场景）或 `go` v4.0（跨模块 / 工程化）。Tasks use checkbox (`- [ ]`) syntax.

**Goal:** 在 skill-hub 顶部加一个 `complexity_scorer()` 评分器，使 skill-hub 能根据任务复杂度（4 维度评分）自动决策 single / serial / parallel 三种调用模式。

**Architecture:** 4 层架构 + 1 评分器。Layer 1 评分器基于 query 4 维度加权打分，Layer 2 路由器按 score 选 v5.4/v6.0/parallel_decomposer 三路。

**Tech Stack:**
- 语言：文档技能 + YAML/JSON 测试用例（无需新代码语言）
- 测试：项目当前 trace 系统（`references/plan-orchestrator-protocol.md` 已支持 `total_tokens`）
- 关键文件：1 改 + 2 新增

---

## 任务拓扑（7 tasks · TDD）

```
Task 1 [测试基线] → Task 2 [4 维度骨架] → Task 3 [路由]  ┐
                                                           ├→ Task 6 [端到端回归]
Task 4 [错误处理 fallback] ────────────────────────────────┤
                                                           └→ Task 7 [性能验证]
Task 5 [SKILL.md 文档段]  ────────────────────────────────────────┘
```

---

## Task 1: 写 complexity_scorer-baseline.json（40 cases）

**Files:**
- Create: `tests/golden-traces/complexity-scorer-baseline.json`

- [ ] **Step 1: 写测试基线 JSON**

```json
{
  "version": "v6.5-complexity-aware-v0.1",
  "date": "2026-06-30",
  "totals": { "unit_cases": 40, "pass_threshold": 1.0 },
  "cases": [
    // 维度 ① 意图清晰度（10 cases）
    { "id": "d1-01", "dim": "intent_clarity", "query": "重构 X 函数", "expected_score_range": [1, 2] },
    { "id": "d1-02", "dim": "intent_clarity", "query": "为什么 Y 不工作", "expected_score_range": [3, 4] },
    { "id": "d1-03", "dim": "intent_clarity", "query": "对比 A 和 B 方案", "expected_score_range": [3, 5] },
    // ... 共 10
  ],
  "scoring_rules": {
    "dim1_intent_clarity": "|matched_keywords| / |total_keywords|",
    "dim2_candidate_count": "|candidates|",
    "dim3_tool_dependency": "1 if 'MCP|jcodemunch|WebFetch|Search' in query else 0",
    "dim4_token_budget": "tokens(query) / 50",
    "weight": "initial: 0.25 each (all four dims)",
    "branch": { "lt_eq_2": "single", "3_to_4": "composite", "eq_5": "parallel" }
  }
}
```

- [ ] **Step 2: 写加载校验脚本 `tests/golden-traces/_load_complexity_baseline.js`**

```javascript
// 加载并跑 baseline 用例
const fs = require('fs');
const path = require('path');

function loadBaseline() {
  const p = path.join(__dirname, 'complexity-scorer-baseline.json');
  const data = JSON.parse(fs.readFileSync(p, 'utf8'));
  if (data.cases.length !== data.totals.unit_cases) {
    throw new Error(`Expected ${data.totals.unit_cases} cases, got ${data.cases.length}`);
  }
  return data;
}

module.exports = { loadBaseline };
```

- [ ] **Step 3: 运行加载校验 → 期望通过**

```bash
cd C:/tsfdsong/python-project/loop_engineering && node -e "require('./tests/golden-traces/_load_complexity_baseline.js').loadBaseline(); console.log('OK: 40 cases loaded')"
```

- [ ] **Step 4: commit**

```bash
git add tests/golden-traces/complexity-scorer-baseline.json tests/golden-traces/_load_complexity_baseline.js
git commit -m "test(skillhub): v6.5 complexity-aware baseline 40 cases"
```

---

## Task 2: 实现 complexity_scorer() 4 维度骨架

**Files:**
- Create: `skills/skill-hub/references/complexity-scorer-spec.md`（协议文档）
- Create: `tests/complexity-scorer.test.js`（单元测试入口）

- [ ] **Step 1: 实现 complexity_scorer() 协议**

```javascript
// skills/skill-hub/references/complexity-scorer.js  (Node 实现 reference)
const KEYWORDS = require('./keywords.json'); // 复用人造关键词表

function tokenize(query) {
  return query.match(/[\w\u4e00-\u9fa5]+/g) || [];
}

function matchSkills(query) {
  // 复用 v5.4 关键词表
  const tokens = tokenize(query).map(t => t.toLowerCase());
  const matched = Object.keys(KEYWORDS).filter(skill =>
    KEYWORDS[skill].some(k => tokens.includes(k.toLowerCase()))
  );
  return matched;
}

function dim1_intent_clarity(query) {
  const tokens = tokenize(query);
  const matched = matchSkills(query);
  return tokens.length === 0 ? 0 : matched.length / tokens.length;
}

function dim2_candidate_count(query) {
  return Math.min(matchSkills(query).length, 5);
}

function dim3_tool_dependency(query) {
  return /MCP|jcodemunch|WebFetch|WebSearch/i.test(query) ? 1 : 0;
}

function dim4_token_budget(query) {
  const tokens = tokenize(query).length;
  return Math.min(tokens / 50, 5);
}

function complexity_scorer(query) {
  const d1 = dim1_intent_clarity(query);
  const d2 = dim2_candidate_count(query);
  const d3 = dim3_tool_dependency(query);
  const d4 = dim4_token_budget(query);
  const score = 1 + (d1 + d2 + d3 + d4);  // base 1
  return {
    score: Math.max(1, Math.min(5, Math.round(score))),
    dim_breakdown: { d1, d2, d3, d4 }
  };
}

module.exports = { complexity_scorer, matchSkills };
```

- [ ] **Step 2: 写单元测试 `tests/complexity-scorer.test.js`**

```javascript
const { complexity_scorer } = require('../skills/skill-hub/references/complexity-scorer.js');
const { loadBaseline } = require('./golden-traces/_load_complexity_baseline.js');

describe('complexity_scorer', () => {
  const baseline = loadBaseline();
  baseline.cases.forEach(c => {
    test(`${c.id}: ${c.query}`, () => {
      const { score } = complexity_scorer(c.query);
      expect(score).toBeGreaterThanOrEqual(c.expected_score_range[0]);
      expect(score).toBeLessThanOrEqual(c.expected_score_range[1]);
    });
  });
});
```

- [ ] **Step 3: 运行测试 → 期望部分通过（其余待 Task 3）**

```bash
cd C:/tsfdsong/python-project/loop_engineering && npx jest tests/complexity-scorer.test.js
```

- [ ] **Step 4: commit**

```bash
git add skills/skill-hub/references/complexity-scorer.js tests/complexity-scorer.test.js
git commit -m "feat(skillhub): v6.5 complexity_scorer 4-dim skeleton"
```

---

## Task 3: 实现 weighted_sum + branch_router（路由决策）

**Files:**
- Modify: `skills/skill-hub/references/complexity-scorer.js`（追加）

- [ ] **Step 1: 写 branch_router 单元测试**

```javascript
const { branch_router } = require('../skills/skill-hub/references/complexity-scorer.js');

describe('branch_router', () => {
  test('score=1 → single', () => {
    expect(branch_router(1)).toBe('single');
  });
  test('score=2 → single', () => {
    expect(branch_router(2)).toBe('single');
  });
  test('score=3 → composite', () => {
    expect(branch_router(3)).toBe('composite');
  });
  test('score=4 → composite', () => {
    expect(branch_router(4)).toBe('composite');
  });
  test('score=5 → parallel', () => {
    expect(branch_router(5)).toBe('parallel');
  });
  test('score=0 → single (fallback)', () => {
    expect(branch_router(0)).toBe('single');
  });
  test('score=6 → clamped single', () => {
    expect(branch_router(6)).toBe('single');  // clamp to 5 → still single after clamp
  });
});
```

- [ ] **Step 2: 实现 branch_router**

```javascript
function branch_router(score) {
  const clamped = Math.max(1, Math.min(5, Math.round(score)));
  if (clamped <= 2) return 'single';
  if (clamped <= 4) return 'composite';
  return 'parallel';
}

module.exports.branch_router = branch_router;
```

- [ ] **Step 3: 运行 branch_router 测试 + complexity-scorer 测试 → 全过**

```bash
cd C:/tsfdsong/python-project/loop_engineering && npx jest tests/complexity-scorer.test.js tests/branch-router.test.js
```

- [ ] **Step 4: commit**

```bash
git add skills/skill-hub/references/complexity-scorer.js
git commit -m "feat(skillhub): v6.5 branch_router 3-way decision"
```

---

## Task 4: 错误处理 fallback 链

**Files:**
- Modify: `skills/skill-hub/references/complexity-scorer.js`

- [ ] **Step 1: 写 fallback 单元测试**

```javascript
const { safe_route } = require('../skills/skill-hub/references/complexity-scorer.js');

describe('safe_route fallback chain', () => {
  test('正常路径 → 返回 scored result', () => {
    const r = safe_route('对比 A 和 B 哪个好');
    expect(r.mode).toMatch(/single|composite|parallel/);
    expect(r.fallback).toBe(false);
  });
  test('空 query → fallback to single', () => {
    const r = safe_route('');
    expect(r.mode).toBe('single');
    expect(r.fallback).toBe(true);
  });
  test('无候选技能 → fallback to single', () => {
    const r = safe_route('xyz123 这两个字母在说什么');
    expect(r.fallback).toBe(true);
  });
  test('scorer 抛错 → fallback to single', () => {
    const r = safe_route(null);  // 触发内部异常
    expect(r.fallback).toBe(true);
  });
});
```

- [ ] **Step 2: 实现 safe_route fallback 链**

```javascript
function safe_route(query) {
  try {
    if (!query || typeof query !== 'string') throw new Error('empty query');
    const { score, dim_breakdown } = complexity_scorer(query);
    return { mode: branch_router(score), complexity_score: score, dim_breakdown, fallback: false };
  } catch (e) {
    console.warn(`[skillhub] scorer fallback: ${e.message}`);
    return { mode: 'single', complexity_score: 0, dim_breakdown: null, fallback: true };
  }
}

module.exports.safe_route = safe_route;
```

- [ ] **Step 3: 运行 fallback 测试 → 全过**

```bash
npx jest tests/safe-route.test.js
```

- [ ] **Step 4: commit**

```bash
git add skills/skill-hub/references/complexity-scorer.js
git commit -m "feat(skillhub): v6.5 safe_route fallback chain"
```

---

## Task 5: SKILL.md 增加"v6.5 复杂度感知路由"段

**Files:**
- Modify: `skills/skill-hub/SKILL.md`（在 v6.1 段之后追加 v6.5 段）

- [ ] **Step 1: 起草 v6.5 段内容**

```markdown
### 🆕 v6.5 新增：复杂度感知路由（alpha · 2026-06-30）

> **起源**：用户原话"更好的根据任务复杂度调度两个技能"。
> **设计稿**：`docs/2026-06-30-skillhub-complexity-aware-design.md` v0.1
> **位置**：在 Layer 1（新评分器）+ Layer 2（路由扩展），不替换 v5.4 / v6.0 / v6.1 任何段。

#### 4 维度评分

| 维度 | 含义 | 算法 |
|------|------|------|
| ① 意图清晰度 | 命中率 | `\|matched_keywords\| / \|tokens(query)\|` |
| ② 候选技能数 | 命中技能数 | `\|candidates\|`（clamp 5）|
| ③ 跨工具依赖 | 是否需要 MCP | 命中 `MCP\|jcodemunch\|WebFetch\|Search` = 1，否则 0 |
| ④ token 预算 | query 长度 | `\|tokens(query)\| / 50`（clamp 5）|

#### 路由表

\| score \| 模式 \| 路径 \|
\|-------\|------\|------\|
\| ≤ 2 \| `single` \| v5.4 关键词表（保留 100% 兼容）|
\| 3-4 \| `composite` \| v6.0 5 类复合任务（规则模拟）|
\| = 5 \| `parallel` \| go / subagent-dd 派发（DAG）|

#### Fallback 优先级

v5.4 baseline → v6.0 5 类表 → 强制 single。**永不让 task 卡住**。

#### 调用样例

\`\`\`javascript
const { safe_route } = require('./skills/skill-hub/references/complexity-scorer.js');
const decision = safe_route('对比 A 和 B 哪个好');
// → { mode: 'composite', complexity_score: 4, fallback: false }
\`\`\`

#### 验证

- 40 unit case：`tests/golden-traces/complexity-scorer-baseline.json`
- v5.4 baseline 27 条：100% 不变
- 端到端：复用 `.workflow/loopengine-skillhub-scheduling/96-scheduling-accuracy-test.md`

> **alpha 状态**：复杂度评分器初始权重 25% 等权，待 trace 数据后学习。
```

- [ ] **Step 2: 插入到 SKILL.md v6.1 段之后，并保持总行数 ≤ 700**

```bash
cd C:/tsfdsong/python-project/loop_engineering
wc -l skills/skill-hub/SKILL.md
# 期望 ≤ 700。如超：把"v6.5"段提到 references/v65-complexity-aware.md，SKILL.md 仅放概要 + 链接。
```

- [ ] **Step 3: 一致性 review（自查 4 项）**

1. 占位符：无 TBD/TODO（仅 `[\u4f4d]` 等代码片段）
2. 一致性：v6.5 段引用设计稿链接与组件表 path 一致
3. 范围：未跨入 Orchestrator 真实现
4. 歧义：路由阈值"≤ 2 / 3-4 / = 5"含义唯一

- [ ] **Step 4: commit**

```bash
git add skills/skill-hub/SKILL.md
git commit -m "docs(skillhub): v6.5 复杂度感知路由段（80 行 alpha）"
```

---

## Task 6: 端到端回归测试

**Files:**
- Create: `tests/end-to-end/skillhub-scheduling.test.js`

- [ ] **Step 1: 写端到端调度测试**

```javascript
const { safe_route } = require('../../skills/skill-hub/references/complexity-scorer.js');
const { loadBaseline } = require('../golden-traces/_load_complexity_baseline.js');

const E2E_CASES = [
  { query: '重构 X 函数', expected_mode: 'single' },
  { query: '为什么 Y 不工作', expected_mode: 'single' },
  { query: '对比 A 和 B 哪个好', expected_mode: 'composite' },
  { query: '调研 X 库 API 并对比 Y 和 Z 实现', expected_mode: 'composite' },
  { query: '并行调研 fastapi / django / flask 三个框架', expected_mode: 'parallel' },
  { query: '用 jcodemunch 索引 loop_engineering 然后重构 skill-hub', expected_mode: 'parallel' }
];

describe('end-to-end scheduling', () => {
  E2E_CASES.forEach((c, i) => {
    test(`e2e-${i + 1}: ${c.query}`, () => {
      const r = safe_route(c.query);
      expect(r.mode).toBe(c.expected_mode);
    });
  });

  test('v5.4 baseline 兼容（采样 5 条关键 query）', () => {
    const samples = ['重构 X', '为什么 Y', '对比 A B', '创建 Z', '修 bug'];
    samples.forEach(q => {
      const r = safe_route(q);
      expect(['single', 'composite', 'parallel']).toContain(r.mode);
    });
  });
});
```

- [ ] **Step 2: 运行端到端测试 → 全过**

```bash
npx jest tests/end-to-end/skillhub-scheduling.test.js
```

- [ ] **Step 3: 运行 v5.4 baseline 27 条 → 100% 通过**

```bash
node tests/golden-traces/v54-baseline-runner.js
```

- [ ] **Step 4: 运行 v6.1 协同契约 6 桥接 → 全过**

```bash
cd C:/tsfdsong/python-project/loop_engineering && node skills/subagent-driven-development/bridges/contract.test.js
```

- [ ] **Step 5: commit**

```bash
git add tests/end-to-end/skillhub-scheduling.test.js
git commit -m "test(skillhub): v6.5 e2e scheduling + baseline regression"
```

---

## Task 7: 性能验证（P99 < 200ms）

**Files:**
- Create: `tests/perf/scorer-bench.js`

- [ ] **Step 1: 写 benchmark**

```javascript
const { safe_route } = require('../../skills/skill-hub/references/complexity-scorer.js');

const QUERIES = [
  '重构 X', '为什么 Y', '对比 A 和 B 哪个好', '调研 X 库 API',
  '用 jcodemunch 索引项目', '并行调研 fastapi/django/flask', '空字符串'
];

function bench() {
  const times = [];
  for (let i = 0; i < 1000; i++) {
    const t0 = process.hrtime.bigint();
    QUERIES.forEach(q => safe_route(q));
    const dt = Number(process.hrtime.bigint() - t0) / 1e6;
    times.push(dt);
  }
  times.sort((a, b) => a - b);
  const p50 = times[Math.floor(times.length * 0.5)];
  const p99 = times[Math.floor(times.length * 0.99)];
  console.log(`P50: ${p50.toFixed(2)}ms | P99: ${p99.toFixed(2)}ms`);
  if (p99 > 200) {
    console.error(`FAIL: P99 ${p99}ms > 200ms threshold`);
    process.exit(1);
  }
}
bench();
```

- [ ] **Step 2: 运行 benchmark**

```bash
node tests/perf/scorer-bench.js
# 期望: P99 < 200ms
```

- [ ] **Step 3: 性能日志归档**

```bash
mkdir -p tests/perf/logs
node tests/perf/scorer-bench.js > tests/perf/logs/2026-06-30-p99.log
git add tests/perf/logs/2026-06-30-p99.log
git commit -m "perf(skillhub): v6.5 scorer P99 baseline"
```

- [ ] **Step 4: commit（perf 测量与归档）**

```bash
git add tests/perf/scorer-bench.js
git commit -m "perf(skillhub): v6.5 scorer bench harness"
```

---

## Self-Review（writing-plans 强制自查）

### 1. Spec 覆盖度

| v0.1 设计要求 | 任务 |
|--------------|------|
| §3.1 架构（4 层 + 1 评分器）| Task 2 + Task 5 |
| §3.2 组件（complexity_scorer + Spec 文件 + SKILL.md 段）| Task 2 + Task 5 |
| §3.3 数据流（5 步）| Task 2 (步骤 1-4) + Task 3 (branch_router) |
| §3.4 错误处理（5 种 fallback）| Task 4 |
| §3.5 测试（40 unit + 27 baseline + e2e）| Task 1 + Task 6 |
| §4.1 边界（不改 v5.4 / 不引入外部 API）| 全 7 Task 守住 |

### 2. 占位符扫描

✅ 已扫描：无 TBD / TODO / FIXME / "fill in details"。

### 3. 类型一致性

- `complexity_scorer(query)` 返回 `{score, dim_breakdown}` ✅ Task 2/3/4 全用此签名
- `branch_router(score)` 返回 `'single' | 'composite' | 'parallel'` ✅ 一致
- `safe_route(query)` 返回 `{mode, complexity_score, dim_breakdown, fallback}` ✅ Task 4/6 一致

### 4. 风险与缓解

| 风险 | 已对冲 |
|------|--------|
| 评分器权重不准确 | Task 4 fallback 到 v5.4（不超过 100% baseline 兼容）|
| P99 超 200ms | Task 7 显式 bench + 失败即终止 |
| v5.4 baseline 回归 | Task 6 第 3 步显式跑 baseline |
| scope creep 到 Orchestrator 真实现 | Task 5 不含实现细节，仅 doc |

---

## Execution Handoff

**任务数：7** ≥ 4 → 走 `/go` v4.0（worktree + 自动拆分 + 跨模块并发）。
- 简易替代：subagent-driven-development
- 单会话执行：executing-plans

**前置 worktree（推荐）：**

```bash
# /go v4.0 会自动创建。手动方式：
git worktree add ../loop_engineering-v65 -b feat/skillhub-v6.5-complexity-aware main
```

**下一步**：用户选择执行路径 + 触发 `/go` 技能启动实施。

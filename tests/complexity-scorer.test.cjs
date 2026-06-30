// tests/complexity-scorer.test.cjs
// Run as: node tests/complexity-scorer.test.cjs

const assert = require('node:assert/strict');
const { complexity_scorer, matchSkills, branch_router } = require('../skills/skill-hub/references/complexity-scorer.cjs');
const { loadBaseline } = require('./golden-traces/_load_complexity_baseline.cjs');

const baseline = loadBaseline();

let pass = 0;
let fail = 0;
const failures = [];

for (const c of baseline.cases) {
  try {
    const { score } = complexity_scorer(c.query);
    const [lo, hi] = c.expected_score_range;
    assert.ok(
      score >= lo && score <= hi,
      `expected score in [${lo}, ${hi}], got ${score}`
    );
    if (c.expected_candidates_min !== undefined) {
      const candidates = matchSkills(c.query);
      assert.ok(
        candidates.length >= c.expected_candidates_min,
        `expected ≥ ${c.expected_candidates_min} candidates, got ${candidates.length} [${candidates.join(', ')}]`
      );
    }
    pass++;
  } catch (e) {
    fail++;
    failures.push(`  ${c.id}: ${c.query} → ${e.message}`);
  }
}

// branch_router 边界测试
const branchCases = [
  [0, 'single'], [1, 'single'], [2, 'single'],
  [3, 'composite'], [4, 'composite'],
  [5, 'parallel'], [6, 'parallel'], [NaN, 'single'],
];
for (const [input, expected] of branchCases) {
  try {
    const got = branch_router(input);
    assert.equal(got, expected, `branch_router(${input}): expected ${expected}, got ${got}`);
    pass++;
  } catch (e) {
    fail++;
    failures.push(`  branch_router(${input}): ${e.message}`);
  }
}

console.log(`\n=== complexity-scorer test ===`);
console.log(`Pass: ${pass}/${pass + fail}`);
if (fail > 0) {
  console.error(`Fail: ${fail}`);
  failures.forEach(f => console.error(f));
  process.exit(1);
}
console.log(`✓ All baseline + branch_router tests passed`);
process.exit(0);

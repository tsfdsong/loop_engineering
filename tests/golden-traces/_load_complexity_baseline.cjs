// tests/golden-traces/_load_complexity_baseline.js
// 加载 + 校验 complexity-scorer-baseline.json 完整性

const fs = require('fs');
const path = require('path');

const BASELINE_PATH = path.join(__dirname, 'complexity-scorer-baseline.json');

function loadBaseline() {
  if (!fs.existsSync(BASELINE_PATH)) {
    throw new Error(`Baseline not found: ${BASELINE_PATH}`);
  }
  const data = JSON.parse(fs.readFileSync(BASELINE_PATH, 'utf8'));

  // 校验 1: case 总数 = 40
  if (!data.cases || data.cases.length !== data.totals.unit_cases) {
    throw new Error(
      `Expected ${data.totals.unit_cases} cases, got ${data.cases?.length ?? 0}`
    );
  }

  // 校验 2: case id 唯一
  const ids = new Set();
  for (const c of data.cases) {
    if (ids.has(c.id)) throw new Error(`Duplicate case id: ${c.id}`);
    ids.add(c.id);
  }

  // 校验 3: 每 case 必含字段
  for (const c of data.cases) {
    for (const k of ['id', 'dim', 'query', 'expected_score_range']) {
      if (!(k in c)) throw new Error(`Case ${c.id}: missing field "${k}"`);
    }
    const [lo, hi] = c.expected_score_range;
    if (typeof lo !== 'number' || typeof hi !== 'number' || lo > hi) {
      throw new Error(`Case ${c.id}: invalid score range [${lo}, ${hi}]`);
    }
  }

  // 校验 4: 4 维度各 10 cases
  const dimCounts = {};
  for (const c of data.cases) {
    dimCounts[c.dim] = (dimCounts[c.dim] || 0) + 1;
  }
  const expected_d1_d2_d3_d4 = ['intent_clarity', 'candidate_count', 'tool_dependency', 'token_budget'];
  for (const d of expected_d1_d2_d3_d4) {
    if (dimCounts[d] !== 10) {
      throw new Error(`Dimension "${d}" should have 10 cases, got ${dimCounts[d] || 0}`);
    }
  }

  return data;
}

if (require.main === module) {
  try {
    const data = loadBaseline();
    console.log(`OK: ${data.cases.length} cases loaded (${data.version})`);
    console.log(`Date: ${data.date} | Threshold: ${data.totals.pass_threshold * 100}%`);
    process.exit(0);
  } catch (e) {
    console.error(`FAIL: ${e.message}`);
    process.exit(1);
  }
}

module.exports = { loadBaseline };

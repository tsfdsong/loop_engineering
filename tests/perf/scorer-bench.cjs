// tests/perf/scorer-bench.cjs
// Performance benchmark: complexity_scorer P99 latency

const { safe_route } = require('../../skills/skill-hub/references/complexity-scorer.cjs');

const QUERIES = [
  '重构 X', '为什么 Y', '对比 A 和 B 哪个好', '调研 X 库 API',
  '用 jcodemunch 索引项目', '并行调研 fastapi/django/flask', '空字符串',
  '', null, undefined,
  '对比 A 和 B 哪个适合我们', '分析下当前 skill-hub 的路由表',
  '用 jcodemunch 索引 loop_engineering 然后重构 skill-hub',
  '分析下当前 skill-hub 的路由表是否存在复杂度评估维度缺失的问题'
];

function bench() {
  const times = [];
  for (let i = 0; i < 1000; i++) {
    const t0 = process.hrtime.bigint();
    for (const q of QUERIES) {
      safe_route(q);
    }
    const dtMs = Number(process.hrtime.bigint() - t0) / 1e6;
    times.push(dtMs);
  }
  times.sort((a, b) => a - b);
  const p50 = times[Math.floor(times.length * 0.5)];
  const p90 = times[Math.floor(times.length * 0.9)];
  const p99 = times[Math.floor(times.length * 0.99)];
  const max = times[times.length - 1];

  const avgPerQuery = p99 / QUERIES.length;
  return { p50, p90, p99, max, queries: QUERIES.length, avgPerQuery };
}

const result = bench();
console.log(`Iterations: 1000 (each runs ${result.queries} queries = ${result.queries * 1000} total)`);
console.log(`P50: ${result.p50.toFixed(3)}ms  |  P90: ${result.p90.toFixed(3)}ms`);
console.log(`P99: ${result.p99.toFixed(3)}ms  |  Max: ${result.max.toFixed(3)}ms`);
console.log(`Per-query (P99 / 14): ${result.avgPerQuery.toFixed(4)}ms`);

const THRESHOLD_MS = 200;
if (result.p99 > THRESHOLD_MS) {
  console.error(`\nFAIL: P99 ${result.p99}ms exceeds ${THRESHOLD_MS}ms threshold`);
  process.exit(1);
}
console.log(`\n✓ P99 ${result.p99.toFixed(2)}ms < ${THRESHOLD_MS}ms threshold (v0.1 spec)`);

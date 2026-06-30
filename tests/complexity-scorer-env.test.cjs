// tests/complexity-scorer-env.test.cjs
// system-review S1-1 + S2-1 fix verification

const assert = require('node:assert/strict');
const scorer = require('../skills/skill-hub/references/complexity-scorer.cjs');

let pass = 0, fail = 0;
const failures = [];

// helper: capture stderr for tests involving emit_trace
function withStderrCapture(fn) {
  const chunks = [];
  const origWrite = process.stderr.write.bind(process.stderr);
  process.stderr.write = (chunk) => { chunks.push(chunk); return true; };
  try { fn(); } finally { process.stderr.write = origWrite; }
  return chunks.join('');
}

// 测试 1: 默认行为（v65 enabled + trace off）
try {
  delete process.env.LOOPENGINE_COMPLEXITY_AWARE;
  delete process.env.LOOPENGINE_COMPLEXITY_TRACE;
  const r = scorer.safe_route('重构 X 函数');
  assert.equal(r.fallback, false);
  assert.notEqual(r.v65, 'disabled');
  assert.ok(r.complexity_score !== null && r.complexity_score >= 1);
  pass++;
} catch (e) { fail++; failures.push(`test 1 (default): ${e.message}`); }

// 测试 2: LOOPENGINE_COMPLEXITY_AWARE=disabled → v65 返回 'disabled'
try {
  process.env.LOOPENGINE_COMPLEXITY_AWARE = 'disabled';
  const r = scorer.safe_route('对比 A 和 B 哪个好');
  assert.equal(r.v65, 'disabled');
  assert.equal(r.mode, 'single');
  assert.equal(r.complexity_score, null);
  assert.equal(r.fallback, false);
  pass++;
} catch (e) { fail++; failures.push(`test 2 (rollback): ${e.message}`); }
delete process.env.LOOPENGINE_COMPLEXITY_AWARE;

// 测试 3: 切回 enabled 后恢复正常评分
try {
  process.env.LOOPENGINE_COMPLEXITY_AWARE = 'enabled';
  const r = scorer.safe_route('对比 A 和 B 哪个好');
  assert.notEqual(r.v65, 'disabled');
  assert.ok(r.complexity_score !== null);
  pass++;
} catch (e) { fail++; failures.push(`test 3 (re-enable): ${e.message}`); }
delete process.env.LOOPENGINE_COMPLEXITY_AWARE;

// 测试 4: trace=on 时每个 safe_route 调用 emit 1 行 JSON 到 stderr
try {
  delete process.env.LOOPENGINE_COMPLEXITY_AWARE;
  process.env.LOOPENGINE_COMPLEXITY_TRACE = 'on';
  const output = withStderrCapture(() => {
    scorer.safe_route('用 jcodemunch 索引 loop_engineering');
  });
  const lines = output.trim().split('\n').filter(Boolean);
  assert.ok(lines.length >= 1, `trace should emit ≥ 1 line, got ${lines.length}\n${output}`);
  const entry = JSON.parse(lines[lines.length - 1]);
  assert.ok(typeof entry.ts === 'string', 'entry.ts 必须存在');
  assert.ok(typeof entry.query_hash === 'string', 'entry.query_hash 必须存在');
  assert.ok(typeof entry.latency_ms === 'number', 'entry.latency_ms 必须为数字');
  assert.ok(entry.latency_ms >= 0 && entry.latency_ms < 1000, `latency_ms ${entry.latency_ms} 应在 [0, 1000]ms`);
  assert.equal(entry.v65, 'enabled');
  pass++;
} catch (e) { fail++; failures.push(`test 4 (trace on): ${e.message}`); }
delete process.env.LOOPENGINE_COMPLEXITY_TRACE;

// 测试 5: trace=off 时 safe_route 静默（仅 try/catch 错误输出，但这里是 no-op）
try {
  delete process.env.LOOPENGINE_COMPLEXITY_TRACE;
  delete process.env.LOOPENGINE_COMPLEXITY_AWARE;
  const output = withStderrCapture(() => {
    scorer.safe_route('重构 X');
  });
  const lines = output.trim().split('\n').filter(Boolean);
  assert.equal(lines.length, 0, `trace=off should emit 0 lines, got: ${output}`);
  pass++;
} catch (e) { fail++; failures.push(`test 5 (trace off): ${e.message}`); }

// 测试 6: 失败路径 + trace 同时 emit (catch 块也应 emit)
try {
  process.env.LOOPENGINE_COMPLEXITY_AWARE = 'enabled';
  process.env.LOOPENGINE_COMPLEXITY_TRACE = 'on';
  const output = withStderrCapture(() => {
    scorer.safe_route(null);
  });
  const lines = output.trim().split('\n').filter(Boolean);
  assert.ok(lines.length >= 1);
  const entry = JSON.parse(lines[lines.length - 1]);
  assert.equal(entry.fallback, true);
  assert.ok(typeof entry.error === 'string', 'catch 路径必须记录 error');
  pass++;
} catch (e) { fail++; failures.push(`test 6 (failure path): ${e.message}`); }
delete process.env.LOOPENGINE_COMPLEXITY_TRACE;
delete process.env.LOOPENGINE_COMPLEXITY_AWARE;

// 测试 7: rollback + trace 同时启用，rollback 路径也应 emit
try {
  process.env.LOOPENGINE_COMPLEXITY_AWARE = 'disabled';
  process.env.LOOPENGINE_COMPLEXITY_TRACE = 'on';
  const output = withStderrCapture(() => {
    scorer.safe_route('some query');
  });
  const lines = output.trim().split('\n').filter(Boolean);
  assert.ok(lines.length >= 1);
  const entry = JSON.parse(lines[lines.length - 1]);
  assert.equal(entry.v65, 'disabled');
  assert.equal(entry.reason, 'v65-disabled');
  pass++;
} catch (e) { fail++; failures.push(`test 7 (rollback + trace): ${e.message}`); }
delete process.env.LOOPENGINE_COMPLEXITY_TRACE;
delete process.env.LOOPENGINE_COMPLEXITY_AWARE;

// 测试 8: 显式清空 env，应回退到默认（enabled）
try {
  delete process.env.LOOPENGINE_COMPLEXITY_AWARE;
  const r = scorer.safe_route('bug 排查');
  assert.notEqual(r.v65, 'disabled');
  pass++;
} catch (e) { fail++; failures.push(`test 8 (empty env=default): ${e.message}`); }

// 测试 9: 安全 — 同一查询多次调用，latency 必须非负且合理
try {
  let lastLatency = null;
  for (let i = 0; i < 100; i++) {
    const t0 = process.hrtime.bigint();
    scorer.safe_route('修复 bug');
    lastLatency = Number(process.hrtime.bigint() - t0) / 1e6;
  }
  assert.ok(lastLatency >= 0 && lastLatency < 50, `last latency ${lastLatency}ms`);
  pass++;
} catch (e) { fail++; failures.push(`test 9 (perf sanity): ${e.message}`); }

console.log(`\n=== complexity-scorer env+trace test ===`);
console.log(`Pass: ${pass}/${pass + fail}`);
if (fail > 0) {
  console.error(`Fail:`);
  failures.forEach(f => console.error(f));
  process.exit(1);
}
console.log(`✓ All env rollback + trace hook tests passed (v0.5 CRITICAL fix)`);
process.exit(0);

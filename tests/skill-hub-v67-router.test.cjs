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
console.log('Test 1: P0 contains 4 process skills');

// Test 2: 三层仲裁顺序正确
const order = MANIFEST.arbitration.priority_order;
assert.deepStrictEqual(
  order,
  ['user_explicit', 'skill_hub', 'skill', 'system_default'],
  'Arbitration order must be user > skill-hub > skill > system'
);
console.log('Test 2: Arbitration order is correct');

// Test 3: 每个 P0 技能有 rationale
for (const skill of MANIFEST.priority_levels.P0.skills) {
  assert.ok(skill.rationale, `${skill.name} must have rationale`);
}
console.log('Test 3: All P0 skills have rationale');

console.log('');
console.log('All skill-hub-v67-router tests passed');

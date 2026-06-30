// tests/skill-lint.test.cjs
// v6.7 description 格式校验
const fs = require('fs');
const path = require('path');

const SKILLS_DIR = path.join(__dirname, '..', 'skills');

function extractDescription(content) {
  // 提取 frontmatter block (--- ... ---)
  const parts = content.split(/^---\s*$/m);
  if (parts.length < 3) return null;
  const yaml = parts[1];
  // 提取 description 字段（单行或多行）
  const match = yaml.match(/^description:\s*(.+?)(?=\n[a-zA-Z]|\n*$)/ms);
  if (!match) return null;
  let desc = match[1].trim();
  // 去除引号
  desc = desc.replace(/^["']|["']$/g, '');
  return desc;
}

function lintDescription(desc) {
  const issues = [];
  if (!desc) {
    issues.push('missing description');
    return issues;
  }
  if (!desc.startsWith('Use when')) {
    issues.push('must start with "Use when"');
  }
  if (desc.length > 500) {
    issues.push(`exceeds 500 chars (${desc.length})`);
  }
  // 不应总结工作流（粗略检查）
  const workflowPatterns = /step.by.step|RED.GREEN|workflow|pipeline|process/i;
  if (workflowPatterns.test(desc) && !/Use when/.test(desc)) {
    issues.push('appears to summarize workflow (anti-pattern)');
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
  const desc = extractDescription(content);
  const issues = desc ? lintDescription(desc) : ['missing frontmatter'];
  tests.push({
    skill,
    description: (desc || '(none)').slice(0, 80),
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
    console.log(`    desc: ${t.description}...`);
  }
  process.exit(1);
}

console.log('\n✅ All skills pass skill-lint v6.7.0-alpha');

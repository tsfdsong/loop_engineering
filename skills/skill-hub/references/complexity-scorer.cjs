// skills/skill-hub/references/complexity-scorer.cjs
// v0.1 complexity-aware scheduler — Layer 1 scorer for skill-hub
//
// Project fact: package.json "type": "module" → 文件用 .cjs 后缀
// Implements 4-dimension complexity scoring:
//   d1 = intent clarity    = |matched_keywords| / |tokens(query)|
//   d2 = candidate count  = |candidates| (clamp 5)
//   d3 = tool dependency  = 1 if any MCP/jcodemunch/WebFetch/Search/repomix/headroom appears
//   d4 = token budget     = |tokens(query)| / 50 (clamp 5)
// score = clamp(round(1 + d1 + d2 + d3 + d4), [1, 5])
//
// branch_router(score):
//   <=2 → 'single'   | 3-4 → 'composite'   | =5 → 'parallel'

const KEYWORDS = {
  'brainstorming':              ['创意', '设计', '头脑风暴', '想法', '方案'],
  'evidence-first':             ['分析', '比较', '评估', '为什么', '应该', '该不该', '选型'],
  'systematic-debugging':       ['bug', '报错', '不工作', '调试', '排查', '修'],
  'verification-before-completion': ['完成', '验证', '通过', '确认'],
  'refactoring':                ['重构', '坏味道', '提取方法', '遗留代码'],
  'clean-code':                 ['规范', '可读', '命名'],
  'testing':                    ['测试', 'TDD', '单元测试', '端到端', 'mock'],
  'system-review':              ['审查', '架构', '检查', '自洽性'],
  'code-reviewer':              ['CR', 'review'],
  'code-complete':              ['代码大全'],
  'deep-research':              ['调研', '对比', '选型', '综述', '报告', '市场分析', '竞品'],
  'product-manager':            ['PRD', '需求', 'RICE', 'Kano'],
  'database-design':            ['数据库', 'SQL', '表设计', '索引'],
  'drawio-skill':               ['画图', '流程图', '架构图'],
  'agent-browser':              ['浏览器', '网页', '截图'],
  'github-actions-templates':   ['CI/CD', '部署', '流水线', 'GitHub Actions'],
};

// 停用词：单字 + 高频功能词，不参与技能匹配
const STOPWORDS = new Set([
  '和', '与', '或', '的', '了', '是', '在', '有', '我', '你',
  '他', '她', '它', '们', '这', '那', '哪', '什么', '怎么', '怎样',
  '个', '下', '上', '中', '里', '外', '前', '后', '并', '同时',
  '是否', '如果', '应该', '应当', '可能', '可以', '需要', '想',
  'a', 'an', 'the', 'and', 'or', 'but', 'to', 'of', 'for', 'in', 'on'
]);

function tokenize(query) {
  if (!query || typeof query !== 'string') return [];
  const raw = query.match(/[\u4e00-\u9fa5]+|[a-zA-Z]+/g) || [];
  return raw
    .map(t => t.toLowerCase())
    .filter(t => !STOPWORDS.has(t) && t.length > 0);
}

function matchSkills(query) {
  const tokens = tokenize(query);
  if (tokens.length === 0) return [];
  return Object.keys(KEYWORDS).filter(skill =>
    KEYWORDS[skill].some(k => tokens.includes(k.toLowerCase()))
  );
}

function dim1_intent_clarity(query) {
  const tokens = tokenize(query);
  const matched = matchSkills(query);
  if (tokens.length === 0) return 0;
  // 意图清晰度 = 命中关键词占清洗后 token 的比例
  return Math.min(matched.length / tokens.length, 1);
}

function dim2_candidate_count(query) {
  // 多技能命中本身只贡献 (candidates-1)*1.0；单技能不抬高复杂度
  const n = matchSkills(query).length;
  return n <= 1 ? 0 : Math.min((n - 1) * 1.0, 5);
}

function dim3_tool_dependency(query) {
  // MCP / jcodemunch / WebFetch / Search / Repomix / 中文搜索词 / Query
  return /MCP|jcodemunch|WebFetch|WebSearch|repomix|headroom|搜索|搜|查找|查询/i.test(query) ? 1 : 0;
}

function dim4_token_budget(query) {
  // query 越长越复杂；tokens 是清洗后，按 10 个一组作为"中等"档
  const tokens = tokenize(query).length;
  return Math.min(tokens / 10, 5);
}

function complexity_scorer(query) {
  const d1 = dim1_intent_clarity(query) * 0.5;  // 高意图清晰度只贡献 0.5（v0.1 evidence-driven calibration）
  const d2 = dim2_candidate_count(query);
  const d3 = dim3_tool_dependency(query);
  const d4 = dim4_token_budget(query);
  const raw = 1 + (d1 + d2 + d3 + d4);
  const score = Math.max(1, Math.min(5, Math.round(raw)));
  return { score, dim_breakdown: { d1, d2, d3, d4 }, raw };
}

function branch_router(score) {
  // NaN / 非数 → 强制 single（项目惯例：缺数据走最安全路径）
  if (typeof score !== 'number' || Number.isNaN(score)) return 'single';
  const clamped = Math.max(1, Math.min(5, Math.round(score)));
  if (clamped <= 2) return 'single';
  if (clamped <= 4) return 'composite';
  return 'parallel';
}

function safe_route(query) {
  try {
    if (!query || typeof query !== 'string') throw new Error('empty or non-string query');
    const { score, dim_breakdown } = complexity_scorer(query);
    return { mode: branch_router(score), complexity_score: score, dim_breakdown, fallback: false };
  } catch (e) {
    return { mode: 'single', complexity_score: 0, dim_breakdown: null, fallback: true, error: e.message };
  }
}

module.exports = {
  KEYWORDS,
  tokenize,
  matchSkills,
  complexity_scorer,
  branch_router,
  safe_route,
  dim1_intent_clarity,
  dim2_candidate_count,
  dim3_tool_dependency,
  dim4_token_budget,
};

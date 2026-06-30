# L4 显式求助兜底模板

> v6.7.0-alpha 新增 · 参照 superpowers using-superpowers 1% 规则 + evidence-first 铁律

**触发条件**：L1 关键词表 fast-path + L2 文件扫描 + L3 domain 过滤 + LLM 语义匹配 全部 miss。

## 硬规则

- ❌ **禁止** AI 自行选一个最像的技能
- ❌ **禁止** 跳过技能直接执行
- ❌ **禁止** 静默回退到无技能模式
- ✅ **必须** 用 `AskUserQuestion` 列出 top-3 候选

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

## 决策记录

用户选择后，记录到 `docs/lessons-learned.md`：

```markdown
## [YYYY-MM-DD] 路由失败案例
- query: <用户原话>
- 候选: <列出的 top-3>
- 实际选择: <用户选哪个>
- 教训: <应该如何改进 description 或 KEYWORDS>
```

## 累积改进

每季度审查 lessons-learned，识别高频失败 query，更新对应 skill 的 description 或 KEYWORDS 表。

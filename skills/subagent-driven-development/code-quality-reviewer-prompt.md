# Code Quality Reviewer Prompt 模板

派遣 code quality reviewer subagent 时使用此模板。

**用途：** 验证实现质量（干净、有测试、可维护）

**仅在 spec 合规评审通过后派遣。**

```
Task tool (general-purpose):
  Use template at requesting-code-review/code-reviewer.md

  DESCRIPTION: [task summary, from implementer's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
```

**除标准代码质量关注点外，reviewer 还应检查：**
- 每个文件是否职责单一、接口清晰？
- 单元是否拆分到可独立理解与测试？
- 实现是否遵循计划中的文件结构？
- 本次实现是否新建了已属大文件的新文件、或显著增大了既有文件？（不追责既有文件大小——只看本次改动贡献了什么。）
- reviewer 不得派遣自己的 subagent —— 直接审 diff（递归派遣曾产生重复评审）。

**Code reviewer 回报：** Strengths（优点）、Issues（Critical/Important/Minor 三层）、Assessment（结论）

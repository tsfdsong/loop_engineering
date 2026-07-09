---
description: 多技能编排器（orch v2 · 自然语言优先 · family-first）
allowed-tools: Skill, Read, Bash, TodoWrite, WebFetch, WebSearch
---

使用 `orch` 技能进行多技能编排。

加载 `skills/orch/SKILL.md` 获取完整编排方法论。

orch v2 识别 scenario family（review / debug_fix / design_build / research_compare / web_qa / parallel_investigation / refactor / test），在 family 内组装串行/并行 DAG，按 rule-first 规则委托 direct_skill / loop / go。

## 触发词

`/orch`、多技能编排、2+ 技能组合

## 不适用

- 单技能任务（由原生 description 匹配自动处理）
- 明确的闭环编码（用 `/loop`）
- 跨模块工程任务（用 `/go`）

# SKILL.md description 改造模板

> v6.7.0-alpha · 参照 superpowers writing-skills 规范

## 格式硬性要求

```yaml
---
name: skill-name
description: Use when [specific triggering conditions]. Do NOT use for: [exclusion scenarios].
---
```

## 关键规则

1. **必须以 "Use when..." 开头**
2. **第三人称**（注入系统提示的）
3. **< 500 字符**
4. **不总结工作流**（避免 LLM 跳过读全文）
5. **包含 "Do NOT use for:" 反向触发**
6. **埋关键词**：错误信息、症状、工具名、同义词

## 正反对比

```yaml
# ❌ 错误：总结了工作流
description: "代码质量超级技能 —— 4 源风格融合（Martin 原则式 + McConnell 要点式 + self 规范表格式 + pragmatic-programmer 工程决策式）"

# ✅ 正确：只有触发条件
description: "Use when writing or reviewing code, when code quality issues are noticed (naming, comments, complexity), or when the user asks for cleanup/standards/refactoring. Do NOT use for: architecture design (use software-architecture), debugging (use systematic-debugging), or specific language features."
```

## 改造工作流

每个 SKILL.md 改造步骤：
1. 读原 description
2. 提取核心场景（3-5 个）
3. 写 "Use when..." 触发条件
4. 写 "Do NOT use for:" 反向触发
5. 校验 < 500 字符
6. 验证不总结工作流
7. 跑 skill-lint 通过

# SKILL.md 规范概要

## frontmatter 要求（必须）

```yaml
---
name: 技能名         # 1-64 字符，仅小写字母/数字/连字符
description: 描述    # 1-1024 字符，必填
compatibility: 兼容性 # 可选，≤500 字符
---
```

## 格式规则

- 必须以 `---` 开头和闭合 frontmatter 区域
- frontmatter 必须是 YAML 键值对（mapping），不能是纯文本或列表
- name 不允许空格、下划线、大写字母或中文
- name 必须与 slug 一致（slug 由发布时指定或从 name 提取）

## 常见错误

| 错误 | 原因 | 修正 |
|---|---|---|
| `name 不允许空格` | name 含空格 | 改为 `my-skill` 格式 |
| `description 为必填项` | 缺少 description | 添加 description 字段 |
| `frontmatter 未闭合` | 缺少结尾的 `---` | 在首行 YAML 之后加 `---` |
| `name 必须与 slug 一致` | name 与发布时的 slug 不同 | 统一为同一值 |

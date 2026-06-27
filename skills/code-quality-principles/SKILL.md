---
name: code-quality-principles
description: 代码质量原则 —— 异常三分、契约测试、commit规范、测试金字塔、防御式编程等代码级架构规范。编码或审查代码时自动加载。
metadata:
  version: "1.0"
  type: rule
  mode: coding-review
---

# 代码质量原则

编写或审查代码时自动加载。

## 异常三分

| 类型 | 特征 | 处理 |
|------|------|------|
| **可恢复** | 重试可能成功（网络超时） | 重试+退避，warning |
| **不可恢复** | 重试无意义（参数错误） | 快速失败，error |
| **需人工** | 需运维介入（资源耗尽） | 报警+降级，critical |

## 契约测试
- API 响应字段白名单检查
- 函数签名兼容性检查
- DB schema diff 检查

## Commit 规范
- 原子：一个 commit 只做一件事
- 语义化：`feat:` / `fix:` / `refactor:` / `test:` / `docs:`
- diff < 200 行

## 防御式编程
- 输入在边界处校验
- 空/零/null/超大值 四类边界必有测试
- 外部依赖不可用时优雅降级

## 测试金字塔
```
    ╱ E2E ╲      ~10%
   ╱ 集成 ╲     ~20%
  ╱  单测   ╲  ~70%
```
- 单测覆盖：正常 + 边界 + 异常
- 集成测试：真实依赖，不 mock DB
- E2E：只测核心流程

---

完整规范: [code-quality-principles.md](../../../../tsfdsong/python-project/yimi-ai-hub/docs/superpowers/specs/code-quality-principles.md)

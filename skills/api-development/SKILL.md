---
name: api-development
description: "API 设计与开发超级技能 —— API 设计原则 + API 安全 + 认证授权三合一。涵盖 REST/GraphQL 设计、安全模式、JWT/OAuth2、限流、输入验证。"
metadata:
  version: "2.0"
  type: skill
  sources:
    - community (api-design-principles)
    - community (api-security-best-practices)
    - community (auth-implementation-patterns)
  merged_from:
    - api-design-principles
    - api-security-best-practices
    - auth-implementation-patterns
  merge_date: "2026-06-29"
  merge_reason: "3 个 API 相关技能内容高度互补，整合为单一入口"
---

# API Development 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

整合 3 个 API 相关技能：
- **api-design-principles**（community）—— REST/GraphQL API 设计
- **api-security-best-practices**（community）—— API 安全模式
- **auth-implementation-patterns**（community）—— 认证授权实现

## 触发关键词（合并后）

API 设计、REST、GraphQL、接口、API 安全、限流、输入验证、登录、JWT、OAuth、认证、权限、CORS、CSRF、auth

## 使用方式

| 任务 | 读哪一章 |
|------|---------|
| 设计新 API | 设计原则 + REST 最佳实践 + GraphQL 设计 |
| 审查 API 设计 | 设计原则 + 安全审查清单 |
| 实现 API 安全 | API 安全 + 输入验证 + 限流 |
| 实现认证/授权 | 认证授权 + JWT/OAuth2 |
| 加固现有 API | 完整内容 references/api-security-full.md |
| 详细认证实现 | references/auth-implementation-full.md |

## 设计原则（api-design-principles · community）

### 何时使用

- 设计新的 REST 或 GraphQL API
- 重构现有 API 提升可用性
- 建立团队 API 设计标准
- 实现前的 API 规范审查
- 迁移 API 范式（REST → GraphQL 等）
- 创建设计者友好的 API 文档
- 优化特定场景 API（移动端、第三方集成）

### 何时不用

- 只需特定框架实现指南
- 纯基础设施工作，无 API 契约
- 无法更改/版本化公共接口

### Instructions

1. **定义消费者**、用例、约束
2. **选择 API 风格** + 建模资源或类型
3. **规范错误**、版本化、分页、认证策略
4. **示例验证** + 一致性审查

详细模式：references/rest-best-practices.md + references/graphql-schema-design.md

## API 安全（api-security-best-practices · community）

### 何时使用

- 设计新 API 端点
- 加固现有 API
- 实现认证授权
- 防护 API 攻击（注入、DDoS）
- 进行 API 安全审查
- 准备安全审计
- 实现限流和节流
- 处理 API 敏感数据

### 关键防护（10 大要点）

1. **认证与授权**（AuthN / AuthZ）
2. **输入验证**（白名单 + 长度限制）
3. **限流与节流**（Rate Limiting）
4. **CORS 配置**（白名单 origin）
5. **CSRF 防护**（CSRF token + SameSite cookie）
6. **注入防护**（参数化查询 + ORM）
7. **敏感数据保护**（加密 + 脱敏）
8. **错误处理**（不泄露栈信息）
9. **审计日志**（关键操作 + 不可篡改）
10. **依赖安全**（定期更新 + 漏洞扫描）

> 完整 902 行内容：[references/api-security-full.md](references/api-security-full.md)

## 认证授权（auth-implementation-patterns · community）

### 何时使用

- 实现用户认证系统
- 加固 REST/GraphQL API
- 接入 OAuth2 / 社交登录 / SSO
- 设计 session 管理或 RBAC
- 调试认证授权问题

### 何时不用

- 只需 UI 文案或登录页样式
- 纯基础设施工作，无身份相关
- 无法修改认证策略或凭证存储

### Instructions

1. **定义用户、租户、流程、威胁模型约束**
2. **选择认证策略**（session / JWT / OIDC）+ token 生命周期
3. **设计授权模型** + 策略执行点
4. **规划密钥存储**、轮换、日志、审计

### Safety（红线）

- ❌ **绝不**记录密钥、token、凭证
- ✅ 强制最小权限 + 安全密钥存储

> 完整 47 行内容：[references/auth-implementation-full.md](references/auth-implementation-full.md)

## 整合使用流程

```
设计新 API
├─ 步骤 1: 设计原则 (REST/GraphQL)
├─ 步骤 2: 安全审查清单 (10 大要点)
├─ 步骤 3: 认证授权方案 (JWT/OAuth2)
├─ 步骤 4: 限流策略
└─ 步骤 5: 测试 + 文档

加固现有 API
├─ 步骤 1: 完整阅读 references/api-security-full.md
├─ 步骤 2: 修复 Critical 风险
├─ 步骤 3: 修复 Important 风险
└─ 步骤 4: 重新审计
```

## Resources

- `resources/implementation-playbook.md`（来自 api-design-principles）—— 实施手册
- `references/rest-best-practices.md`（来自 api-design-principles）—— REST 详细模式
- `references/graphql-schema-design.md`（来自 api-design-principles）—— GraphQL 详细模式
- `references/api-security-full.md`（来自 api-security-best-practices）—— 完整 915 行
- `references/auth-implementation-full.md`（来自 auth-implementation-patterns）—— 完整 47 行
- `assets/api-design-checklist.md`（来自 api-design-principles）—— 设计检查清单
- `assets/rest-api-template.py`（来自 api-design-principles）—— REST 模板

## 限制

- 本技能不替代环境特定的验证、测试、专家审查
- 缺少必需输入、权限、安全边界、成功标准时停止并询问

---

## 迁移说明

- v6.2 合并前：api-design-principles + api-security-best-practices + auth-implementation-patterns 三个独立技能
- v6.2 合并后：api-development 一个超级技能
- 完整内容保留在 references/ 子目录
- skill-hub 调度表已同步
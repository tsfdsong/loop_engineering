---
name: testing
description: "测试超级技能 —— 单元/集成测试 + TDD 严格方法 + E2E 端到端测试三合一。涵盖 Jest 模式、TDD 红绿重构、Cypress/Playwright 端到端。"
metadata:
  version: "2.0"
  type: skill
  sources:
    - community (testing-patterns)
    - superpowers (test-driven-development)
    - community (e2e-testing-patterns)
  merged_from:
    - testing-patterns
    - test-driven-development
    - e2e-testing-patterns
  merge_date: "2026-06-29"
  merge_reason: "3 个测试相关技能（单元/TDD/E2E）整合为单一入口"
---

# Testing 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

整合 3 个测试相关技能：
- **testing-patterns**（community）—— Jest 模式、工厂函数、Mock
- **test-driven-development**（superpowers）—— 严格 TDD 红绿重构循环
- **e2e-testing-patterns**（community）—— 端到端测试自动化

## 触发关键词（合并后）

单元测试、Mock、测试用例、Jest、测试模式、TDD、红绿重构、测试先行、端到端、E2E、浏览器测试、回归、CI

## 使用方式

| 任务 | 读哪一章 |
|------|---------|
| 写单元测试 | 测试模式 + 工厂函数 |
| 实现 TDD 严格流程 | TDD 红绿重构循环 |
| E2E 自动化 | 端到端测试模式 |
| 调试 flaky 测试 | E2E + 测试模式 |
| 集成其他技能 | systematic-debugging + subagent-driven-development |

## 测试模式（testing-patterns · community · 270 行）

### 核心原则

- **TDD**: 失败测试 → 实现 → 重构
- **行为测试**: 测试行为而非实现
- **工厂模式**: `getMockX(overrides?)` 函数

### 工厂函数示例

```typescript
const getMockUser = (overrides?: Partial<User>): User => ({
  id: '123', name: 'John Doe', email: 'john@example.com', role: 'user',
  ...overrides,
});
```

### Mock 模式

```typescript
jest.mock('utils/analytics', () => ({
  Analytics: { logEvent: jest.fn() },
}));
```

> 完整 270 行内容：[references/testing-patterns-full.md](references/testing-patterns-full.md)

## TDD 严格方法（test-driven-development · superpowers · 371 行）

### Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

写代码前写测试？**删除。** 从测试重新开始。

### Red-Green-Refactor

```
RED → 写失败测试 → 验证失败
GREEN → 写最小代码 → 验证通过
REFACTOR → 清理代码 → 保持绿色
```

### TDD 适用场景

**始终用**：新功能、Bug 修复、重构、行为变更  
**询问人类合作伙伴**：临时原型、生成的代码、配置文件

> 完整 371 行内容：[references/tdd-full.md](references/tdd-full.md)

## 端到端测试（e2e-testing-patterns · community · 49 行）

### 何时使用

- 实现 E2E 自动化
- 调试 flaky/不可靠测试
- 测试关键用户工作流
- 设置 CI/CD 测试流水线
- 跨浏览器测试
- 验证无障碍要求
- 测试响应式设计

### 何时不用

- 只需单元/集成测试
- 环境不支持稳定 UI 自动化
- 无法提供安全测试账户/数据

### Instructions

1. **识别关键用户旅程**和成功标准
2. **构建稳定选择器**和测试数据策略
3. **实现测试**：retries、tracing、isolation
4. **CI 中运行**：并行化 + artifact 捕获

> 完整 49 行内容：[references/e2e-testing-full.md](references/e2e-testing-full.md)

## 整合使用流程

```
新功能开发
├─ 步骤 1: TDD 红绿重构（先写失败测试）
├─ 步骤 2: 单元测试（工厂函数 + Mock）
├─ 步骤 3: 集成测试（多个模块协作）
└─ 步骤 4: E2E 测试（关键用户旅程）

Bug 修复
├─ 步骤 1: TDD（先写失败测试复现 bug）
├─ 步骤 2: 单元测试覆盖边界
└─ 步骤 3: 验证修复 + 防止回归
```

## Resources

- `resources/e2e-playbook.md`（来自 e2e-testing-patterns）—— E2E 详细模式
- `references/testing-patterns-full.md`（来自 testing-patterns）—— 完整 270 行
- `references/tdd-full.md`（来自 test-driven-development）—— 完整 371 行
- `references/e2e-testing-full.md`（来自 e2e-testing-patterns）—— 完整 49 行

## 限制

- TDD 铁律：写代码前必须有失败测试，否则删除
- E2E 测试必须有专用测试数据 + 清理敏感输出
- 完整内容在 references/，按需查阅

---

## 迁移说明

- v6.2 合并前：testing-patterns + test-driven-development + e2e-testing-patterns 三个独立技能
- v6.2 合并后：testing 一个超级技能
- 完整内容保留在 references/ 和 resources/
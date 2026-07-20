---
name: testing
description: |
  TRIGGER: 写测试 / TDD / 加测试覆盖 / 设计测试策略 / '测试' / 'TDD' / '单元测试' / '端到端' / 'mock' / 'test'（通用测试金字塔方法论：unit/integration/E2E + POM + fixtures + selectors；web 项目 E2E 脚手架 + CI 集成用 web-regression-e2e；不用于：修测试失败用 systematic-debugging，代码审查用 code-reviewer）
  RULE: no specific rule（方法论 skill · 测试金字塔方法论）
  DETAIL: 本 SKILL.md（unit 70% / integration 20% / e2e 10% + TDD 横切）
metadata:
  version: "2.1"
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
  merge_date_v2_1: "2026-06-30"  # v6.4 强化测试金字塔结构
  merge_reason: |
    v6.2 合并 → 3 源并排；v6.4 重组为"测试金字塔"4 层次（单元 → 集成 → E2E），
    TDD 作为横切方法论贯穿所有层次。
  test_pyramid:
    - layer_1: unit (70%)
    - layer_2: integration (20%)
    - layer_3: e2e (10%)
  crosscutting:
    - tdd_methodology (red-green-refactor)
---

# Testing 超级技能

## 核心定位：4 层测试金字塔 + TDD 横切

```
        ╱ E2E ╲         10%   端到端：关键用户旅程
       ╱  集成  ╲       20%   跨模块：真实依赖，不 mock DB
      ╱   单测   ╲     70%    业务逻辑：纯函数 + 边界 + 异常
     ───────────────────
     TDD 铁律贯穿所有层
     NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

**何时该用 testing**：
- 写新功能 / 改 bug / 重构（任意代码改动前）
- 调试失败测试
- 评估代码质量（覆盖率）
- 设立 CI 流水线

**何时不该用**：
- ❌ 纯文档 / 配置文件（不需要测试）
- ❌ 临时一次性脚本（无长期价值）
- ❌ 探索性实验（用原型，不用测试）

---

## Layer 1 · 单元测试（70% · testing-patterns）

> 目标：业务逻辑 + 边界 + 异常，快（毫秒级）

### 核心原则

- **TDD**：失败测试 → 实现 → 重构
- **行为测试**：测试行为而非实现（不耦合内部结构）
- **工厂模式**：`getMockX(overrides?)` 函数生成可定制 mock
- **AAA 模式**：Arrange（准备）→ Act（执行）→ Assert（断言）
- **一个测试一个断言**（或一组紧密相关断言）
- **测试名是句子**：`should_<expected>_when_<condition>`

### 工厂函数示例

```typescript
// ✅ 工厂函数 + overrides
const getMockUser = (overrides?: Partial<User>): User => ({
  id: '123',
  name: 'John Doe',
  email: 'john@example.com',
  role: 'user',
  createdAt: new Date('2026-01-01'),
  ...overrides,  // 可定制任一字段
});

// 用法
const admin = getMockUser({ role: 'admin' });
const newUser = getMockUser({ createdAt: new Date() });
```

### Mock 模式

```typescript
// ✅ 模块 mock
jest.mock('utils/analytics', () => ({
  Analytics: { logEvent: jest.fn() },
}));

// ✅ 部分 mock
jest.spyOn(Date, 'now').mockReturnValue(new Date('2026-01-01').getTime());

// ✅ 异步 mock
jest.mock('./api', () => ({
  fetchUser: jest.fn().mockResolvedValue({ id: '1', name: 'Alice' }),
}));
```

### 边界测试清单（4 类必测）

- [ ] **空**：`null` / `[]` / `""`
- [ ] **零**：`0` / `0.0` / `0,0,0`
- [ ] **null**：`undefined` / `None` / `nil`
- [ ] **超大值**：`Number.MAX_SAFE_INTEGER` / 1MB 字符串

### 何时用 vs 不用 mock

| 用 mock | 不用 mock（用真实） |
|--------|------------------|
| 外部 HTTP API | 项目内领域对象 |
| 时间 / 随机数 | 文件系统（小文件） |
| 数据库（大集成） | — |
| 第三方付费服务 | — |

### 异步测试

```typescript
// ✅ async/await
test('fetches user', async () => {
  const user = await fetchUser('123');
  expect(user.name).toBe('Alice');
});

// ✅ 错误处理
test('throws on 404', async () => {
  await expect(fetchUser('not-found')).rejects.toThrow('Not found');
});
```

> 详细 Jest 模式（270 行）：通过 testing-patterns 历史规则文件查阅（v6.4 已合并入 SKILL.md）

---

## Layer 2 · 集成测试（20% · 真实依赖）

> 目标：验证跨模块协作，使用真实依赖（DB / 消息队列），不 mock。

### 核心原则

- **真实数据库**：用 TestContainers / Docker 起临时 DB
- **真实 HTTP**：用 supertest / httpx 起 server
- **真实消息队列**：用 in-memory 实现或 TestContainers
- **真实文件系统**：用 tmp 目录
- ❌ **不**用 mock DB（违背集成测试初衷）

### Python 集成测试示例

```python
import pytest
from httpx import AsyncClient
from myapp.main import app

@pytest.mark.asyncio
async def test_create_user_persists_to_db(test_db):
    # Arrange: 真实 DB
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act: 真实 HTTP + 真实 DB
        resp = await client.post("/users", json={"name": "Alice"})

    # Assert: 直接查 DB 验证持久化
    assert resp.status_code == 201
    users = await test_db.fetch_all("SELECT * FROM users")
    assert len(users) == 1
    assert users[0]["name"] == "Alice"
```

### TestContainers 模式

```python
# 真实 PostgreSQL 容器
@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()

@pytest.fixture
def test_db(postgres_container):
    # 每次测试前清表
    db = Database(postgres_container)
    db.execute("TRUNCATE users, orders")
    return db
```

### 集成测试 vs 单元测试选择

| 场景 | 单元 | 集成 |
|------|:---:|:---:|
| 业务规则（纯函数） | ✅ | — |
| 业务规则（带 DB） | — | ✅ |
| API endpoint | — | ✅ |
| 数据访问层（Repository） | — | ✅ |
| 业务规则 + 外部 API | — | ✅ |
| UI 组件 | ✅ | — |
| 关键用户旅程 | — | ✅ |

---

## Layer 3 · E2E 测试（10% · 端到端用户旅程）

> 目标：模拟真实用户在真实浏览器/应用中的关键操作

### 何时用 E2E

- 关键用户旅程（注册 / 下单 / 支付）
- 跨多个服务/页面的工作流
- 视觉/响应式/无障碍验证
- 端到端性能（首屏 / TTI）

### 何时不用

- ❌ 业务规则（用单元测试）
- ❌ 边缘 UI 状态（成本太高）
- ❌ 一次性验证（手动做）

### E2E 编写原则

1. **关键用户旅程优先**：注册 → 登录 → 核心操作 → 支付
2. **稳定选择器**：`data-testid` > 文本 > CSS 选择器
3. **测试数据隔离**：每个测试用独立用户/数据，不共享
4. **重试机制**：网络/CI 不稳定时自动重试（≤ 3 次）
5. **Tracing**：失败时捕获 trace + screenshot + 视频
6. **CI 并行**：独立测试并行跑，artifact 集中收集
7. **隔离状态**：每个测试前重置数据（不要依赖顺序）

### Playwright 示例

```typescript
import { test, expect } from '@playwright/test';

test('user can register and login', async ({ page }) => {
  // 注册
  await page.goto('/register');
  await page.fill('[data-testid="email"]', 'alice@example.com');
  await page.fill('[data-testid="password"]', 'Pass1234');
  await page.click('[data-testid="submit"]');
  await expect(page.locator('[data-testid="welcome"]')).toBeVisible();

  // 登出
  await page.click('[data-testid="logout"]');

  // 登录
  await page.goto('/login');
  await page.fill('[data-testid="email"]', 'alice@example.com');
  await page.fill('[data-testid="password"]', 'Pass1234');
  await page.click('[data-testid="submit"]');
  await expect(page.locator('[data-testid="welcome"]')).toBeVisible();
});
```

### E2E 失败调试

- **Trace Viewer**（Playwright）：失败时捕获完整 trace
- **Headed 模式**：本地调试时 `--headed` 看真实交互
- **Retry 机制**：CI 用 `retries: 2`，本地 `retries: 0`
- **视频录制**：失败时保留视频

### Safety（红线）

- ❌ **绝不**对生产环境跑 E2E
- ✅ 用专用测试数据（test database / 沙箱账户）
- ✅ 测试输出脱敏（不记录真实密码/token）
- ✅ 定期清理测试数据（避免累积）

### E2E 详细模式（531 行）

- [resources/e2e-playbook.md](resources/e2e-playbook.md)

---

## TDD · 严格红绿重构循环（横切所有层）

> 核心原则：**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**
> 写代码前写测试？**删除。从测试重新开始。**

### Iron Law

```
任何生产代码（不只是功能代码）的写，都必须先有失败测试。

包括但不限于：
- 新功能
- Bug 修复
- 重构（先有保护测试）
- 配置变更（要测配置生效）
- 性能优化（要测性能提升）
```

### Red-Green-Refactor 循环

```
┌─ RED ─────────────────────────────────┐
│ 写一个失败测试                        │
│ → 验证它确实失败（不是因为写错）       │
└────────────────────────────────────┘
         ↓
┌─ GREEN ──────────────────────────────┐
│ 写最小代码让测试通过                   │
│ → 写最丑最直白的代码                  │
│ → 不要顺手"改进"                      │
└────────────────────────────────────┘
         ↓
┌─ REFACTOR ───────────────────────────┐
│ 清理代码（命名 / 提取 / 重构）         │
│ → 保持测试绿色                        │
│ → 每次小步                          │
└────────────────────────────────────┘
         ↓
       （循环）
```

### TDD 适用场景

| 始终用 TDD | 询问人类合作伙伴 |
|-----------|----------------|
| 新功能 | 临时原型（一次丢弃） |
| Bug 修复 | 生成的代码（OpenAPI 生成） |
| 重构（先有保护测试） | 配置文件（无逻辑） |
| 行为变更 | 实验性 spike |
| API 新增 | — |

### TDD 反模式

- ❌ **写完代码再补测试**（违反铁律，等于没 TDD）
- ❌ **测试已经通过的代码**（不是 TDD，是 regression test）
- ❌ **跳过红步骤**（"我心里知道会失败" ≠ 真的失败过）
- ❌ **批量写测试再实现**（失去红绿反馈节奏）
- ❌ **测试通过了就跳过重构**（技术债累积）

### TDD 详细方法（371 行）

- [references/tdd-full.md](references/tdd-full.md)

---

## 整合使用流程

### 场景 1 · 新功能开发

```
Step 1: TDD RED - 写失败单元测试
  → 测试一个具体业务规则
  → 跑测试，验证它失败
Step 2: TDD GREEN - 写最小实现
  → 只让测试通过，不要顺手"改进"
Step 3: TDD REFACTOR - 清理代码
  → 命名 / 提取 / 重构，保持绿色
Step 4: 补充边界测试（空/零/null/超大）
Step 5: 写集成测试（真实 DB / HTTP）
Step 6: 写 E2E 测试（关键用户旅程）
Step 7: 提交（按 commit 规范）
```

### 场景 2 · Bug 修复

```
Step 1: 写失败测试复现 bug（RED）
  → 这个测试在修复前必须失败
Step 2: 跑测试，验证失败
Step 3: 修复 bug（GREEN）
Step 4: 跑测试，验证通过
Step 5: 加边界测试，防止回归
Step 6: 提交
```

### 场景 3 · 重构（已有代码）

```
Step 1: 写特征测试（记录当前行为）
  → 即使是 bug 也要记录
Step 2: 重构一处
Step 3: 跑全部测试，验证行为不变
Step 4: 提交（refactor: 提交信息）
Step 5: 重复 Step 2-4 到目标坏味道消除
```

### 场景 4 · 调试 flaky 测试

```
Step 1: 是网络问题？→ 加 retry
Step 2: 是时间问题？→ 用确定性时间（mock clock）
Step 3: 是状态污染？→ 隔离测试数据
Step 4: 是并发？→ 减并发或加锁
Step 5: 是 E2E？→ 加 wait + trace
Step 6: 还 flaky？→ 标记为 known flaky，跳过 CI（但要修）
```

---

## 测试金字塔健康度检查

### 黄金比例（参考）

```
70 / 20 / 10 = 70% 单元 / 20% 集成 / 10% E2E
```

### 反模式信号

| 信号 | 含义 | 行动 |
|------|------|------|
| **E2E > 30%** | E2E 当单测用 | 拆 E2E → 集成/单测 |
| **集成 < 10%** | 集成覆盖不足 | 加真实 DB 测试 |
| **单测 < 50%** | 业务逻辑无单测 | 重构：提纯函数 + 加单测 |
| **执行时间 单元 > 1s** | 单测有 IO 依赖 | mock 外部依赖 |
| **集成 > 30s** | 数据准备太重 | 用 fixture 复用 |

### 覆盖率目标

| 层级 | 覆盖率目标 |
|------|:---:|
| **业务核心** | ≥ 90% |
| **API endpoint** | 100% |
| **UI 组件** | ≥ 70% |
| **E2E 关键路径** | 100%（数量少但全） |

---

## 触发关键词

单元测试、Mock、测试用例、Jest、测试模式、TDD、红绿重构、测试先行、端到端、E2E、浏览器测试、回归、CI、覆盖率、特征测试、行为测试、集成测试、TestContainers

---

## 与其他技能配合

| 场景 | 配合技能 |
|------|---------|
| 重构保护 | `refactoring`（本技能 + 重构手法） |
| 调试失败 | `systematic-debugging` |
| 代码审查 | `code-reviewer`（Stage 1 单测覆盖检查） |
| 上线前测试 | `production-readiness`（覆盖率审计） |
| 系统测试 | `agent-browser`（交互式 E2E 调试） |

---

## 限制

- **TDD 铁律** — 写代码前必须有失败测试，否则删除
- **E2E 必须有专用测试数据** + 清理敏感输出
- **完整内容在 references/** — 按需查阅
- **不替代人工探索性测试** — 复杂场景手动验证
- **覆盖率是手段不是目的** — 100% 覆盖不代表无 bug

---

## 迁移说明

- v6.2 合并前：testing-patterns + test-driven-development + e2e-testing-patterns
- v6.2 合并后：testing 超级技能（3 源并排）
- **v6.4 重组**：从并排 → 4 层测试金字塔（单测/集成/E2E/TDD横切）
- 内联：e2e-testing 49 行要点已融入 Layer 3 章节
- 保留：tdd-full.md（371 行）+ e2e-playbook.md（531 行）
- 内联：testing-patterns 270 行内容已融入 Layer 1 章节
- go family 路由表已同步

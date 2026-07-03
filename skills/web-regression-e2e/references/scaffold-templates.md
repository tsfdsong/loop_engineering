# 脚手架模板源（Scaffolding）

> 本文件提供 SKILL.md Phase 2 列出的全部脚手架文件源码。
> 当 `NEEDS_SCAFFOLD` 时，按本文件内容在目标项目生成 `e2e/` 目录。
> 与 `ci-integration-templates.md` 互补：本文件管 `e2e/` 目录内，那一份管 `.github/workflows/`。

## 目录结构（生成顺序）

```
e2e/
├── package.json              # §1
├── playwright.config.ts      # §2
├── tsconfig.json             # §3
├── .env.example              # §4
├── fixtures/
│   ├── auth.ts               # §5（详细版见 auth-bypass-patterns.md）
│   └── test-users.ts         # §6
├── utils/
│   ├── api-helpers.ts        # §7
│   ├── selectors.ts          # §8
│   └── wait-helpers.ts       # §9（详细版见 antd-wait-patterns.md）
└── tests/
    ├── p0/                   # §10 示例
    └── ux/                   # §10 示例
```

---

## §1. e2e/package.json

```json
{
  "name": "<project>-e2e",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:ui": "playwright test --ui",
    "report": "playwright show-report",
    "codegen": "playwright codegen"
  },
  "devDependencies": {
    "@playwright/test": "^1.50.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.4.0"
  }
}
```

依赖按需追加：`@axe-core/playwright`（a11y）、`playwright-lighthouse`（perf）。

## §2. e2e/playwright.config.ts

```typescript
import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.BASE_URL ?? "http://localhost:3000";
const isCI = !!process.env.CI;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: !isCI,           // CI 串行避免端口冲突
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 1 : undefined,
  reporter: isCI
    ? [["html"], ["list"], ["github"]]
    : [["html"], ["list"]],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    // 视觉/a11y/perf 按需启用其他浏览器：
    // { name: "firefox",  use: { ...devices["Desktop Firefox"] } },
    // { name: "webkit",   use: { ...devices["Desktop Safari"] } },
    // { name: "mobile",   use: { ...devices["iPhone 13"] } },
  ],
});
```

## §3. e2e/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "types": ["node"],
    "lib": ["ES2022", "DOM"]
  },
  "include": ["**/*.ts"]
}
```

## §4. e2e/.env.example

```bash
# 目标站点（dev/staging，绝不指向生产）
BASE_URL=http://localhost:3000

# 鉴权（三选一，详见 auth-bypass-patterns.md）
# 模式1：dev login
ALLOW_DEV_LOGIN=true

# 模式2：注入 session cookie（staging 用）
# SESSION_COOKIE=

# 模式3：admin 账号
ADMIN_USER=admin
ADMIN_PASS=changeme
```

> **安全**：`.env`（非 `.env.example`）必须加入 `.gitignore`，真实凭据从 CI Secret 注入。

## §5. e2e/fixtures/auth.ts（骨架，完整模式见 auth-bypass-patterns.md）

```typescript
import { test as base, expect, type Page } from "@playwright/test";

// 默认走 Dev Login（模式1）；其他模式见 auth-bypass-patterns.md
async function devLogin(page: Page): Promise<void> {
  const res = await page.request.post("/api/v1/auth/dev-login", {
    data: { username: process.env.ADMIN_USER ?? "dev_user" },
  });
  expect(res.ok(), `dev-login failed: ${res.status()}`).toBeTruthy();
}

export const test = base.extend<{ userPage: Page }>({
  userPage: async ({ page }, use) => {
    await devLogin(page);
    await page.goto("/");
    await use(page);
  },
});

export { expect };
```

## §6. e2e/fixtures/test-users.ts

```typescript
export type TestUser = { email: string; password: string; name: string };

// 工厂函数：生成可定制测试用户（避免硬编码散落）
export const getTestUser = (overrides?: Partial<TestUser>): TestUser => ({
  email: `e2e-${Date.now()}@example.com`,
  password: "Test123!@#",
  name: "E2E User",
  ...overrides,
});

export const adminUser = (): TestUser => ({
  email: process.env.ADMIN_USER ?? "admin",
  password: process.env.ADMIN_PASS ?? "",
  name: "Admin",
});
```

## §7. e2e/utils/api-helpers.ts

```typescript
import type { APIRequestContext } from "@playwright/test";

// 直接走 API 准备/清理数据，比 UI 点击快得多
export async function apiCreate(request: APIRequestContext, path: string, body: unknown) {
  const res = await request.post(path, { data: body });
  if (!res.ok()) throw new Error(`POST ${path} failed: ${res.status()}`);
  return res.json();
}

export async function apiDelete(request: APIRequestContext, path: string) {
  const res = await request.delete(path);
  if (!res.ok()) throw new Error(`DELETE ${path} failed: ${res.status()}`);
}
```

## §8. e2e/utils/selectors.ts

```typescript
// 所有 data-testid 集中注册，禁止在测试文件里散落 [data-testid="..."]
// 命名规范见 data-testid-conventions.md
export const SEL = {
  // auth
  loginModal: "login-modal",
  loginSubmit: "login-submit",
  // hub
  hubSwitcher: "hub-switcher",
  // loading / empty / error
  loadingSkeleton: "loading-skeleton",
  emptyState: "empty-state-container",
  errorToast: "error-toast",
} as const;

// 用法：page.getByTestId(SEL.loginSubmit)
```

## §9. e2e/utils/wait-helpers.ts（骨架，完整版见 antd-wait-patterns.md）

```typescript
import { expect, type Page } from "@playwright/test";

// Antd Modal/Drawer/Tabs 等待函数见 antd-wait-patterns.md
// 这里仅放通用 helper：

export async function waitForReady(page: Page) {
  await page.waitForLoadState("networkidle");
}

export async function waitForVisible(page: Page, testId: string, timeout = 10_000) {
  await expect(page.getByTestId(testId)).toBeVisible({ timeout });
}
```

## §10. e2e/tests/ 示例

### tests/p0/auth.spec.ts

```typescript
import { test, expect } from "@fixtures/auth"; // 或相对路径 ../../fixtures/auth
import { SEL } from "@utils/selectors";

test("登录后可见 dashboard", async ({ userPage }) => {
  // userPage 已自动 dev-login，直接验证
  await expect(userPage).toHaveURL(/\/dashboard/);
});

test("session 失效弹出登录框", async ({ userPage, context }) => {
  await userPage.goto("/dashboard");
  await context.clearCookies();
  await userPage.goto("/dashboard/skills");
  await expect(userPage.getByTestId(SEL.loginModal)).toBeVisible();
});
```

### tests/ux/loading.spec.ts

```typescript
import { test, expect } from "@playwright/test";
import { SEL } from "@utils/selectors";

test("首次进入显示 loading 后显示内容", async ({ page }) => {
  await page.goto("/");
  // 等待 loading 消失后内容区出现（可选断言 skeleton 可见，按需加）
  await expect(page.getByTestId(SEL.loadingSkeleton)).toBeHidden();
  await expect(page.getByTestId(SEL.emptyState)).toBeVisible();
});
```

---

## 生成后检查清单

- [ ] `e2e/package.json` 依赖与项目一致（Antd 项目可加 `@axe-core/playwright`）
- [ ] `playwright.config.ts` 的 `baseURL` 指向 dev/staging（绝不生产）
- [ ] `.env` 加入 `.gitignore`
- [ ] `tsconfig.json` 的 `moduleResolution` 与项目 TS 版本匹配（TS 5.0+ 用 Bundler）
- [ ] 跑 `cd e2e && npx playwright install chromium` 确认浏览器可装

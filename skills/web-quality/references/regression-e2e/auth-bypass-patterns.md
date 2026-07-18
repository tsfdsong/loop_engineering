# 鉴权绕过模式

## 模式 1: Dev Login (推荐)

**适用**：后端有 `ALLOW_DEV_LOGIN=true` 模式（仅 localhost）

```typescript
// fixtures/auth.ts
import { test as base, expect } from "@playwright/test";

async function devLogin(page: Page): Promise<void> {
  const res = await page.request.post("/api/v1/auth/dev-login", {
    data: { username: "dev_user" },
  });
  expect(res.ok(), `dev-login failed: ${res.status()}`).toBeTruthy();
}

export const test = base.extend({
  userPage: async ({ page, baseURL }, use) => {
    await devLogin(page);
    await page.goto("/");
    await use(page);
  },
});
```

**安全注意**：dev-login 端点必须仅在 `DEBUG=true && ALLOW_DEV_LOGIN=true && request.host == "localhost"` 三重条件下启用。

## 模式 2: Cookie 注入

**适用**：已有 session cookie（如生产 staging 环境）

```typescript
async function injectSession(page: Page, sessionCookie: string) {
  await page.context().addCookies([
    {
      name: "session",
      value: sessionCookie,
      domain: new URL(page.context()._options.baseURL!).hostname,
      path: "/",
      httpOnly: true,
      secure: true,
    },
  ]);
}
```

## 模式 3: Admin JSON Store Login

**适用**：admin 站点用文件存储的账号（典型 FastAPI 项目）

```typescript
async function adminLogin(page: Page) {
  const res = await page.request.post("/api/v1/admin/auth/login", {
    form: {
      username: "admin",
      password: "admin888888",  // 来自 ADMIN_INITIAL_PASSWORD 环境变量
    },
  });
  expect(res.ok()).toBeTruthy();
}
```

## 模式 4: 401 → LoginModal 模拟

**适用**：测试 session 过期流程

```typescript
test("session expiry shows login modal", async ({ userPage, context }) => {
  await userPage.goto("/dashboard");
  await context.clearCookies();  // 模拟 session 失效
  await userPage.goto("/dashboard/skills");
  // axios 拦截器会检测 401 → 打开 LoginModal
  await expect(userPage.getByTestId("login-modal")).toBeVisible();
});
```

## 模式 5: Mock JWT (仅 mock 模式)

**适用**：纯前端 demo / 教学项目

```typescript
// 仅用于纯前端项目，不接真实后端
await page.addInitScript(() => {
  window.localStorage.setItem("mock-jwt", "eyJhbGciOiJIUzI1NiJ9.mock");
});
```

## 反例

- ❌ 在测试里 `page.fill()` 用户名密码 → 慢、脆弱
- ❌ 复用生产账号 → 安全风险
- ❌ 跳过鉴权测试 → 失去鉴权链路保证

# E2E 测试模式实施手册

本文件承载技能引用的详细模式、清单与代码样例。

## 核心概念

### 1. E2E 测试基础

**E2E 该测什么：**
- 关键用户旅程（登录、结账、注册）
- 复杂交互（拖放、多步表单）
- 跨浏览器兼容
- 真实 API 集成
- 认证流程

**E2E 不该测什么：**
- 单元级逻辑（用单元测试）
- API 契约（用集成测试）
- 边界情况（太慢）
- 内部实现细节

### 2. 测试哲学

**测试金字塔：**
```
        /\
       /E2E\         ← Few, focused on critical paths
      /─────\
     /Integr\        ← More, test component interactions
    /────────\
   /Unit Tests\      ← Many, fast, isolated
  /────────────\
```
（E2E 少而聚焦关键路径；集成多测组件交互；单元多而快、隔离。）

**最佳实践：**
- 测用户行为，不测实现
- 测试保持独立
- 测试保持确定性
- 为速度优化
- 用 data-testid，不用 CSS 选择器

## Playwright 模式

### 安装与配置

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './e2e',
    timeout: 30000,
    expect: {
        timeout: 5000,
    },
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: [
        ['html'],
        ['junit', { outputFile: 'results.xml' }],
    ],
    use: {
        baseURL: 'http://localhost:3000',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
    },
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
        { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
        { name: 'webkit', use: { ...devices['Desktop Safari'] } },
        { name: 'mobile', use: { ...devices['iPhone 13'] } },
    ],
});
```

### Pattern 1: Page Object Model（页对象模型）

```typescript
// pages/LoginPage.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
    readonly page: Page;
    readonly emailInput: Locator;
    readonly passwordInput: Locator;
    readonly loginButton: Locator;
    readonly errorMessage: Locator;

    constructor(page: Page) {
        this.page = page;
        this.emailInput = page.getByLabel('Email');
        this.passwordInput = page.getByLabel('Password');
        this.loginButton = page.getByRole('button', { name: 'Login' });
        this.errorMessage = page.getByRole('alert');
    }

    async goto() {
        await this.page.goto('/login');
    }

    async login(email: string, password: string) {
        await this.emailInput.fill(email);
        await this.passwordInput.fill(password);
        await this.loginButton.click();
    }

    async getErrorMessage(): Promise<string> {
        return await this.errorMessage.textContent() ?? '';
    }
}

// Test using Page Object
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';

test('successful login', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('user@example.com', 'password123');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' }))
        .toBeVisible();
});

test('failed login shows error', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('invalid@example.com', 'wrong');

    const error = await loginPage.getErrorMessage();
    expect(error).toContain('Invalid credentials');
});
```

### Pattern 2: 测试数据 Fixtures

```typescript
// fixtures/test-data.ts
import { test as base } from '@playwright/test';

type TestData = {
    testUser: {
        email: string;
        password: string;
        name: string;
    };
    adminUser: {
        email: string;
        password: string;
    };
};

export const test = base.extend<TestData>({
    testUser: async ({}, use) => {
        const user = {
            email: `test-${Date.now()}@example.com`,
            password: 'Test123!@#',
            name: 'Test User',
        };
        // Setup: Create user in database
        await createTestUser(user);
        await use(user);
        // Teardown: Clean up user
        await deleteTestUser(user.email);
    },

    adminUser: async ({}, use) => {
        await use({
            email: 'admin@example.com',
            password: process.env.ADMIN_PASSWORD!,
        });
    },
});

// Usage in tests
import { test } from './fixtures/test-data';

test('user can update profile', async ({ page, testUser }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(testUser.email);
    await page.getByLabel('Password').fill(testUser.password);
    await page.getByRole('button', { name: 'Login' }).click();

    await page.goto('/profile');
    await page.getByLabel('Name').fill('Updated Name');
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Profile updated')).toBeVisible();
});
```

### Pattern 3: 等待策略

```typescript
// ❌ Bad: Fixed timeouts
await page.waitForTimeout(3000);  // Flaky!

// ✅ Good: Wait for specific conditions
await page.waitForLoadState('networkidle');
await page.waitForURL('/dashboard');
await page.waitForSelector('[data-testid="user-profile"]');

// ✅ Better: Auto-waiting with assertions
await expect(page.getByText('Welcome')).toBeVisible();
await expect(page.getByRole('button', { name: 'Submit' }))
    .toBeEnabled();

// Wait for API response
const responsePromise = page.waitForResponse(
    response => response.url().includes('/api/users') && response.status() === 200
);
await page.getByRole('button', { name: 'Load Users' }).click();
const response = await responsePromise;
const data = await response.json();
expect(data.users).toHaveLength(10);

// Wait for multiple conditions
await Promise.all([
    page.waitForURL('/success'),
    page.waitForLoadState('networkidle'),
    expect(page.getByText('Payment successful')).toBeVisible(),
]);
```

### Pattern 4: 网络 Mock 与拦截

```typescript
// Mock API responses
test('displays error when API fails', async ({ page }) => {
    await page.route('**/api/users', route => {
        route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Internal Server Error' }),
        });
    });

    await page.goto('/users');
    await expect(page.getByText('Failed to load users')).toBeVisible();
});

// Intercept and modify requests
test('can modify API request', async ({ page }) => {
    await page.route('**/api/users', async route => {
        const request = route.request();
        const postData = JSON.parse(request.postData() || '{}');

        // Modify request
        postData.role = 'admin';

        await route.continue({
            postData: JSON.stringify(postData),
        });
    });

    // Test continues...
});

// Mock third-party services
test('payment flow with mocked Stripe', async ({ page }) => {
    await page.route('**/api/stripe/**', route => {
        route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'mock_payment_id',
                status: 'succeeded',
            }),
        });
    });

    // Test payment flow with mocked response
});
```

## Cypress 模式

### 安装与配置

```typescript
// cypress.config.ts
import { defineConfig } from 'cypress';

export default defineConfig({
    e2e: {
        baseUrl: 'http://localhost:3000',
        viewportWidth: 1280,
        viewportHeight: 720,
        video: false,
        screenshotOnRunFailure: true,
        defaultCommandTimeout: 10000,
        requestTimeout: 10000,
        setupNodeEvents(on, config) {
            // Implement node event listeners
        },
    },
});
```

### Pattern 1: 自定义命令

```typescript
// cypress/support/commands.ts
declare global {
    namespace Cypress {
        interface Chainable {
            login(email: string, password: string): Chainable<void>;
            createUser(userData: UserData): Chainable<User>;
            dataCy(value: string): Chainable<JQuery<HTMLElement>>;
        }
    }
}

Cypress.Commands.add('login', (email: string, password: string) => {
    cy.visit('/login');
    cy.get('[data-testid="email"]').type(email);
    cy.get('[data-testid="password"]').type(password);
    cy.get('[data-testid="login-button"]').click();
    cy.url().should('include', '/dashboard');
});

Cypress.Commands.add('createUser', (userData: UserData) => {
    return cy.request('POST', '/api/users', userData)
        .its('body');
});

Cypress.Commands.add('dataCy', (value: string) => {
    return cy.get(`[data-cy="${value}"]`);
});

// Usage
cy.login('user@example.com', 'password');
cy.dataCy('submit-button').click();
```

### Pattern 2: Cypress Intercept

```typescript
// Mock API calls
cy.intercept('GET', '/api/users', {
    statusCode: 200,
    body: [
        { id: 1, name: 'John' },
        { id: 2, name: 'Jane' },
    ],
}).as('getUsers');

cy.visit('/users');
cy.wait('@getUsers');
cy.get('[data-testid="user-list"]').children().should('have.length', 2);

// Modify responses
cy.intercept('GET', '/api/users', (req) => {
    req.reply((res) => {
        // Modify response
        res.body.users = res.body.users.slice(0, 5);
        res.send();
    });
});

// Simulate slow network
cy.intercept('GET', '/api/data', (req) => {
    req.reply((res) => {
        res.delay(3000);  // 3 second delay
        res.send();
    });
});
```

## 高级模式

### Pattern 1: 视觉回归测试

```typescript
// With Playwright
import { test, expect } from '@playwright/test';

test('homepage looks correct', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('homepage.png', {
        fullPage: true,
        maxDiffPixels: 100,
    });
});

test('button in all states', async ({ page }) => {
    await page.goto('/components');

    const button = page.getByRole('button', { name: 'Submit' });

    // Default state
    await expect(button).toHaveScreenshot('button-default.png');

    // Hover state
    await button.hover();
    await expect(button).toHaveScreenshot('button-hover.png');

    // Disabled state
    await button.evaluate(el => el.setAttribute('disabled', 'true'));
    await expect(button).toHaveScreenshot('button-disabled.png');
});
```

### Pattern 2: 分片并行测试

```typescript
// playwright.config.ts
export default defineConfig({
    projects: [
        {
            name: 'shard-1',
            use: { ...devices['Desktop Chrome'] },
            grepInvert: /@slow/,
            shard: { current: 1, total: 4 },
        },
        {
            name: 'shard-2',
            use: { ...devices['Desktop Chrome'] },
            shard: { current: 2, total: 4 },
        },
        // ... more shards
    ],
});

// Run in CI
// npx playwright test --shard=1/4
// npx playwright test --shard=2/4
```

### Pattern 3: 无障碍测试

```typescript
// Install: npm install @axe-core/playwright
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('page should not have accessibility violations', async ({ page }) => {
    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page })
        .exclude('#third-party-widget')
        .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
});

test('form is accessible', async ({ page }) => {
    await page.goto('/signup');

    const results = await new AxeBuilder({ page })
        .include('form')
        .analyze();

    expect(results.violations).toEqual([]);
});
```

## 最佳实践

1. **用数据属性**：`data-testid` 或 `data-cy` 做稳定选择器
2. **避免脆选择器**：不依赖 CSS 类或 DOM 结构
3. **测用户行为**：点击、输入、看见——不是实现细节
4. **测试保持独立**：每个测试隔离运行
5. **清理测试数据**：每个测试内创建并销毁
6. **用 Page Object**：封装页面逻辑
7. **有意义的断言**：检查用户真实可见的行为
8. **为速度优化**：能 mock 就 mock、并行执行

```typescript
// ❌ Bad selectors
cy.get('.btn.btn-primary.submit-button').click();
cy.get('div > form > div:nth-child(2) > input').type('text');

// ✅ Good selectors
cy.getByRole('button', { name: 'Submit' }).click();
cy.getByLabel('Email address').type('user@example.com');
cy.get('[data-testid="email-input"]').type('user@example.com');
```

## 常见坑

- **flaky 测试**：用恰当的等待，不用固定超时
- **测试慢**：mock 外部 API、并行执行
- **过度测试**：不要每个边界都用 E2E 测
- **测试耦合**：测试之间不应相互依赖
- **烂选择器**：避免 CSS 类与 nth-child
- **不清理**：每个测试后清理测试数据
- **测实现**：测用户行为，不测内部

## 调试失败测试

```typescript
// Playwright debugging
// 1. Run in headed mode
npx playwright test --headed

// 2. Run in debug mode
npx playwright test --debug

// 3. Use trace viewer
await page.screenshot({ path: 'screenshot.png' });
await page.video()?.saveAs('video.webm');

// 4. Add test.step for better reporting
test('checkout flow', async ({ page }) => {
    await test.step('Add item to cart', async () => {
        await page.goto('/products');
        await page.getByRole('button', { name: 'Add to Cart' }).click();
    });

    await test.step('Proceed to checkout', async () => {
        await page.goto('/cart');
        await page.getByRole('button', { name: 'Checkout' }).click();
    });
});

// 5. Inspect page state
await page.pause();  // Pauses execution, opens inspector
```

## 资源

- **references/playwright-best-practices.md**：Playwright 专用模式
- **references/cypress-best-practices.md**：Cypress 专用模式
- **references/flaky-test-debugging.md**：调试不可靠测试
- **assets/e2e-testing-checklist.md**：E2E 该测什么
- **assets/selector-strategies.md**：找可靠选择器
- **scripts/test-analyzer.ts**：分析测试 flakiness 与时长

# Antd 等待模式

## 通则

**Antd 5.x 组件用 CSS transition 做动画（默认 200ms）。Playwright 的 `expect().toBeVisible()` 会等动画结束，但**有些场景要更精确的信号**。

## Modal

```typescript
// ✅ 推荐：等到 aria-hidden=false（动画完成）
export async function waitForModalOpen(page: Page, testId: string) {
  const modal = page.getByTestId(testId);
  await expect(modal).toBeVisible();
  await expect(modal).toHaveAttribute("aria-hidden", "false", { timeout: 5_000 });
}

export async function waitForModalClose(page: Page, testId: string) {
  await expect(page.getByTestId(testId)).toBeHidden();
}
```

## Drawer

Drawer 类似 Modal，但用 `aria-expanded` 而不是 `aria-hidden`：

```typescript
export async function waitForDrawerOpen(page: Page, testId: string) {
  const drawer = page.getByTestId(testId);
  await expect(drawer).toBeVisible();
  await expect(drawer).toHaveAttribute("aria-expanded", "true");
}
```

## Tabs

```typescript
export async function switchTab(page: Page, tabKey: string) {
  await page.getByRole("tab", { name: tabKey }).click();
  await expect(page.getByRole("tab", { name: tabKey })).toHaveAttribute(
    "aria-selected",
    "true",
  );
}
```

## Form 错误提示

```typescript
// 表单提交后等错误出现
await page.getByRole("button", { name: /保存|save/i }).click();
await expect(page.getByRole("alert").first()).toBeVisible({ timeout: 5_000 });
```

## Upload

```typescript
// Antd Upload 触发文件选择对话框
const fileChooserPromise = page.waitForEvent("filechooser");
await page.getByRole("button", { name: /上传|upload/i }).click();
const fileChooser = await fileChooserPromise;
await fileChooser.setFiles(["./fixtures/test-file.pdf"]);
```

## Table 加载

```typescript
// 等表格行出现（说明数据加载完）
await expect(page.getByRole("row").nth(1)).toBeVisible({ timeout: 10_000 });
```

## Notification / Message

```typescript
// Antd Message 默认 3 秒自动消失，断言要快
await expect(page.locator(".ant-message-notice").first()).toBeVisible({ timeout: 1_000 });
```

## 等待时不要

- ❌ `page.waitForTimeout(1000)` — 固定等待会变 flaky
- ❌ `page.waitForSelector` — 已被 `expect().toBeVisible()` 取代
- ❌ 自己实现 sleep — 用 Playwright auto-wait

# 动态内容屏蔽

## 常见动态内容

- 时间戳（"3 分钟前更新"）
- 实时数据（股票、天气、计数器）
- 广告位（轮播）
- 用户头像/昵称
- 随机验证码/Captcha
- 通知 toast

## 屏蔽策略

### 策略 1: CSS 隐藏

```typescript
await page.addStyleTag({
  content: `
    .timestamp, .live-counter, .ad-banner { visibility: hidden !important; }
  `,
});
```

### 策略 2: mockDate

```typescript
// 固定时间，避免每次截图时间不同
await page.addInitScript(() => {
  const fixedDate = new Date("2026-07-02T00:00:00Z").getTime();
  const _Date = Date;
  // @ts-ignore
  window.Date = class extends _Date {
    constructor(...args) {
      if (args.length === 0) super(fixedDate);
      else super(...args);
    }
    static now() { return fixedDate; }
  };
});
```

### 策略 3: network 拦截

```typescript
await page.route("**/api/v1/live-data*", (route) => {
  route.fulfill({ json: { value: 1234 } });
});
```

### 策略 4: mask 区域

```typescript
await expect(page).toHaveScreenshot("home.png", {
  mask: [
    page.locator("[data-testid='live-counter']"),
    page.locator("[data-testid='ad-banner']"),
  ],
});
```

## 优先级

1. **mockDate 固定时间**——最干净，优先用
2. **CSS 隐藏**——对周期性内容有效
3. **network 拦截**——对 API 数据有效
4. **mask 区域**——最后手段（diff 报告会显示灰色蒙版）

## 验证

跑测试时故意让一个动态区域可见，确认它在 diff 中被正确忽略：
```bash
# 删掉 mockDate 跑一次，看 diff 是否爆出 → 确认 mask 真的生效
```

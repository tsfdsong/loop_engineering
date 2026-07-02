# 误报处理

## 抑制单条规则

```typescript
const results = await new AxeBuilder({ page })
  .withTags(["wcag2aa"])
  .disableRules(["color-contrast"])  // 已知误报
  .analyze();
```

## 抑制单元素

```typescript
// 在元素上加 data-axe-disable 或 aria-hidden
<div data-axe-disable="true">装饰性内容</div>
```

## 常见误报清单

### 1. `color-contrast` 对 SVG/Canvas 误报

**原因**：axe 静态分析无法读 SVG 内部颜色
**解决**：`.disableRules(["color-contrast"])` 后手动用工具（Stark / Lighthouse）验

### 2. `region` 报"页面缺少 main landmark"

**原因**：自定义 layout 没有 `<main>` 包裹
**解决**：在 layout 根加 `<main>` 或 `role="main"`

### 3. `heading-order` 报"跳级"

**原因**：动态内容导致 h1 → h3（跳 h2）
**解决**：用 `<h2>` 占位（视觉隐藏）保持顺序：
```tsx
<h2 style={{ position: "absolute", left: "-9999px" }}>占位</h2>
<h3>实际内容</h3>
```

### 4. `aria-allowed-attr` 在第三方 widget

**原因**：Recharts/echarts 等加了自己的 aria 属性
**解决**：`.exclude(".third-party-chart")` 排除该区域

### 5. `duplicate-id` 动态生成 ID

**原因**：Antd Form 用 random ID，正常
**解决**：`.exclude(".ant-form")` 排除表单容器

## 抑制规则文件

集中管理（推荐）：

```typescript
// a11y/axe-config.ts
export const axeConfig = {
  disableRules: [
    "color-contrast",  // 已知误报，单独验
  ],
  exclude: [
    ".ant-form",         // Antd Form 动态 ID
    ".third-party-chart",
  ],
  tags: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
};
```

```typescript
// tests/a11y/home.spec.ts
import { axeConfig } from "../a11y/axe-config";
test("home a11y", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(axeConfig.tags)
    .disableRules(axeConfig.disableRules)
    .exclude(axeConfig.exclude)
    .analyze();
  expect(results.violations).toEqual([]);
});
```

## 人工测试清单（axe 覆盖不到）

- [ ] 键盘 Tab 顺序是否符合视觉顺序
- [ ] Skip link 是否存在（"跳到主内容"）
- [ ] Focus 状态是否明显（不仅是 outline）
- [ ] Modal 打开时 focus 是否在 modal 内
- [ ] 屏幕阅读器朗读是否自然（用 NVDA/VoiceOver 实测）
- [ ] 缩放 200% 是否仍然可用

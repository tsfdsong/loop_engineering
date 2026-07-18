# pixelmatch 配置

## 阈值参数

| 参数 | 含义 | 推荐值 | 严格 → 宽松 |
|---|---|---|---|
| `threshold` | 颜色相似度（0=完全相同）| 0.1 | 0.05 / 0.1 / 0.2 |
| `maxDiffPixelRatio` | 差异像素占比上限 | 0.01 (1%) | 0.001 / 0.01 / 0.05 |
| `includeAA` | 是否包含抗锯齿像素 | false | — |

## 推荐配置

**严格**（金融/医疗等高合规）：
```typescript
threshold: 0.05, maxDiffPixelRatio: 0.001
```

**中等**（一般 web app，默认）：
```typescript
threshold: 0.1, maxDiffPixelRatio: 0.01
```

**宽松**（内容型网站/电商）：
```typescript
threshold: 0.2, maxDiffPixelRatio: 0.05
```

## 抗锯齿处理

不同浏览器/不同 GPU 渲染的抗锯齿不同，会导致像素差但视觉无差。两种策略：

1. **接受小差异**：`threshold: 0.1` 容忍颜色微差
2. **关闭抗锯齿**：在 `page.addStyleTag` 中：
   ```typescript
   await page.addStyleTag({ content: "* { -webkit-font-smoothing: none !important; }" });
   ```

## 忽略区域

某些区域总在变（广告位/股票报价/时间戳），可以屏蔽：

```typescript
await expect(page).toHaveScreenshot("home.png", {
  mask: [page.locator(".ad-banner"), page.locator(".stock-ticker")],
});
```

## 字体一致性

CI 容器字体与本地不同是常见 flaky 源：

```dockerfile
# Dockerfile
RUN apt-get install -y fonts-noto-cjk fonts-liberation
```

或在 CSS 中：
```css
* { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif !important; }
```

## 跨浏览器容忍

| 浏览器对 | 容忍度 |
|---|---|
| Chromium vs Chromium | 0.1% |
| Chromium vs Firefox | 1-2% |
| Chromium vs WebKit | 2-3% |

**建议**：在 CI 上只用 Chromium（默认），其他浏览器可单独 nightly 跑。

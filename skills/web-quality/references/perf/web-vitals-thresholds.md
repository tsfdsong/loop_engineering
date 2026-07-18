# Web Vitals 阈值建议

## Google 官方 "Good" 阈值

| 指标 | Good | Needs Improvement | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤ 2500ms | 2500-4000ms | > 4000ms |
| INP (Interaction to Next Paint) | ≤ 200ms | 200-500ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | 0.1-0.25 | > 0.25 |
| FCP (First Contentful Paint) | ≤ 1800ms | 1800-3000ms | > 3000ms |
| TTFB (Time to First Byte) | ≤ 800ms | 800-1800ms | > 1800ms |

## 按项目类型定制

### 电商 / 内容型（推荐严格）

```json
{
  "lcp": 2000,
  "cls": 0.05,
  "inp": 150,
  "fcp": 1500
}
```

### SaaS 工具（中等）

```json
{
  "lcp": 2500,
  "cls": 0.1,
  "inp": 200,
  "fcp": 1800
}
```

### 后台管理系统（宽松）

```json
{
  "lcp": 3500,
  "cls": 0.15,
  "inp": 300,
  "fcp": 2500
}
```

### 富媒体 / 视频（最宽松）

```json
{
  "lcp": 4000,
  "cls": 0.25,
  "inp": 500,
  "fcp": 3000
}
```

## 移动端 vs 桌面端

| 维度 | 移动端 | 桌面端 |
|---|---|---|
| 默认网络 | Slow 4G (1.6Mbps) | Cable (5Mbps) |
| 默认 CPU | 4x slowdown | 1x |
| LCP 阈值 | 2500ms | 1200ms |
| FCP 阈值 | 1800ms | 800ms |

**建议**：CI 跑 mobile（更严格），桌面端单独 nightly 跑。

## 渐进式收紧

不要一步到位设最严。从现状 + 10% 起步：

```bash
# 1. 跑现状基线
npx lighthouse https://my-app.com --output=json

# 2. 设阈值 = 现状 * 1.1
# 3. 跑几周，逐步收紧到目标值
```

## 与业务指标挂钩

- LCP 每降 100ms → 电商转化率 +1-2%
- CLS > 0.1 → 用户跳出率 +5%
- INP > 200ms → 工具类用户留存 -3%

数据来源：Google Web.dev 案例研究。

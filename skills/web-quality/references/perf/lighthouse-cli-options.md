# Lighthouse CLI 参数

## 基础

```bash
npx lighthouse <url> \
  --output=json \
  --output-path=./report.json \
  --preset=desktop
```

## 常用参数

| 参数 | 用途 | 默认 |
|---|---|---|
| `--output` | json / html / csv | json |
| `--output-path` | 输出文件 | stdout |
| `--preset` | desktop / mobile | mobile (perf) / desktop (其他) |
| `--throttling-method` | simulate / devtools / provided | simulate |
| `--chrome-flags` | 额外 Chrome 参数 | — |
| `--only-categories` | performance / a11y / seo / best-practices | all |
| `--skip-audits` | 跳过某些审计 | — |

## 模拟移动端

```bash
npx lighthouse https://my-app.com \
  --form-factor=mobile \
  --screenEmulation.mobile=true \
  --throttling.cpuSlowdownMultiplier=4
```

## 桌面端

```bash
npx lighthouse https://my-app.com --preset=desktop
```

## 跳过登录（如果需要）

```bash
npx lighthouse https://my-app.com \
  --extra-headers="{\"Cookie\":\"session=xxx\"}"
```

## 性能 only

```bash
npx lighthouse https://my-app.com \
  --only-categories=performance \
  --output=json
```

## 多页面批量

```bash
for url in / /about /pricing; do
  npx lighthouse "https://my-app.com$url" \
    --output=json \
    --output-path="./reports/${url//\//_}.json"
done
```

## Chrome flags 实用组合

```bash
--chrome-flags="--headless --no-sandbox --disable-gpu --disable-dev-shm-usage"
```

CI 环境必加 `--no-sandbox`。

## 输出格式对比

| 格式 | 适合 |
|---|---|
| `json` | CI 解析 |
| `html` | 人看 |
| `csv` | 批量对比 |

## 报告内容

Lighthouse JSON 关键字段：

```json
{
  "audits": {
    "largest-contentful-paint": { "numericValue": 1234 },
    "cumulative-layout-shift": { "numericValue": 0.05 },
    "total-blocking-time": { "numericValue": 100 }
  },
  "categories": {
    "performance": { "score": 0.95 }
  }
}
```

详见 `perf-regression-investigation.md` § 字段定位。

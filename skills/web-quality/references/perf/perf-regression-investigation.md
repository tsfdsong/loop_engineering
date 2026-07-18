# 性能回归定位

## 现象分类

| 现象 | 常见根因 | 定位工具 |
|---|---|---|
| LCP 飙高 | 大图未压缩 / 字体加载阻塞 / 关键 CSS 缺失 | Lighthouse "Largest Contentful Paint element" |
| CLS 飙高 | 异步图片无宽高 / 动态注入内容 / 字体 FOIT | Lighthouse "Layout shift elements" |
| INP 飙高 | 长任务（>50ms）阻塞主线程 | Performance tab "Long Tasks" |
| FCP 飙高 | 关键资源加载慢 / render-blocking JS | Network tab waterfall |
| TTI 飙高 | 第三方脚本大 / hydration 慢 | Coverage tab |

## 定位流程

### 1. 复现

```bash
# 跑两次确认稳定
npx lighthouse https://my-app.com --output=json --output-path=baseline.json
npx lighthouse https://my-app.com --output=json --output-path=baseline2.json
# diff baseline.json baseline2.json
```

### 2. 对比基线

```bash
# 找出与上次 release 的 diff
git log --oneline --since="1 week ago" -- frontend/
git diff <last-release>..HEAD -- frontend/ | head -200
```

### 3. Lighthouse 报告深读

打开 HTML 报告，看 **Diagnostics** 和 **Opportunities**：

| Section | 看什么 |
|---|---|
| **Diagnostics** | 哪些资源加载慢、是否有长任务 |
| **Opportunities** | 可优化点（按预估节省时间排序）|
| **Largest Contentful Paint Element** | LCP 元素是哪个、为什么慢 |

### 4. 关键问题清单

#### LCP 飙高

- [ ] LCP 元素是图片？是否用 `next/image` 或 `<img loading="lazy">` 反模式？
- [ ] 字体加载完成时间？是否 `font-display: swap`？
- [ ] 关键 CSS 是否 inline？

#### CLS 飙高

- [ ] 所有 `<img>` 有 `width` / `height` 属性？
- [ ] 动态注入的 banner / cookie consent 是否预留空间？
- [ ] Web fonts 加载时是否用 `size-adjust` 调整行高？

#### INP 飙高

- [ ] 点击 handler 是否超过 50ms？
- [ ] 大列表是否虚拟滚动？
- [ ] 是否有同步 localStorage / IndexedDB 阻塞主线程？

### 5. 工具组合

| 工具 | 用途 |
|---|---|
| Lighthouse | 整体评分 + 优化建议 |
| Chrome DevTools Performance | 帧级分析（具体到函数）|
| Chrome DevTools Coverage | 找出未使用的 JS / CSS |
| WebPageTest | 多地点多设备测试 |
| bundlephobia | 包体积影响分析 |
| `import-cost` (VSCode) | 实时看每个 import 体积 |

## 报告模板

发现性能回归时，issue 模板：

```markdown
## 性能回归报告

**版本**：v1.2.0 → v1.3.0
**指标**：LCP 1800ms → 3200ms (+78%)

### Root cause
PR #234 引入了 `moment` 依赖（+200KB），阻塞关键路径

### Fix
替换为 `date-fns` (-180KB)，LCP 恢复 1900ms

### Prevention
- 在 CI 增加 bundle size 阈值（>50KB 警告，>100KB 阻塞）
- 引入 `import-cost` 检查依赖大小
```

## 持续监控

- 每次 release 跑 perf audit
- 在 dashboard 跟踪趋势（Datadog / Grafana + lighthouse-ci）
- 季度复盘 Web Vitals 趋势

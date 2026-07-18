# shared-setup — Playwright 安装与配置（web-quality 共享前置）

> 4 子能力（a11y / perf / regression-e2e / visual-diff）共用同一套 Playwright 基础设施
> 由 web-regression-e2e 子能力负责 scaffold，其他 3 个复用

## 1. 基础依赖

| 依赖 | 版本 | 说明 |
|---|---|---|
| Node.js | ≥ 18 | Playwright 运行时 |
| `@playwright/test` | ^1.50.0 | 4 子能力的共同引擎 |

## 2. 项目首次安装（无 `e2e/` 目录）

```bash
# 1) 创建 e2e 目录（scaffold 细节见 regression-e2e/scaffold-templates.md）
mkdir -p e2e && cd e2e

# 2) 装 Playwright
npm i -D @playwright/test

# 3) 装浏览器二进制
npx playwright install chromium              # macOS / 基础用法
# 或：
npx playwright install --with-deps chromium  # Linux 装系统依赖
# 或（省 ~300MB，复用系统 Chrome）：
PLAYWRIGHT_BROWSERS_PATH=0 npx playwright install chromium

# 4) 跨浏览器矩阵（如需 Firefox / WebKit）
npx playwright install firefox webkit
```

## 3. 项目已存在 `e2e/`

直接复用：

```bash
cd e2e && npm install
npx playwright install chromium
```

## 4. 各子能力的额外依赖

| 子能力 | 额外依赖 | 安装命令 |
|---|---|---|
| regression-e2e | — | 无 |
| visual-diff | — | 无（Playwright `toHaveScreenshot` 内置像素对比） |
| a11y | `@axe-core/playwright` ^4.10.0 | `npm i -D @axe-core/playwright` |
| perf | `lighthouse` ^12.0.0 + `playwright-lighthouse` ^4.0.0 | `npm i -D lighthouse playwright-lighthouse` |

## 5. config 所有权

`web-quality` 是 `e2e/playwright.config.ts` 的**唯一 owner**（由 regression-e2e 子能力 scaffold）。

- 其他子能力（a11y / perf / visual-diff）**追加字段**到同一 config（如 `expect.toMatchSnapshot`、`projects`）
- 不要新建第二个 config
- 子目录约定：`tests/a11y/` / `tests/perf/` / `tests/visual/` / `tests/p0/` / `tests/ux/`

## 6. 一次性审计（CLI，不写测试）

若用户只想跑一次性审计（不集成到测试套件），可用 CLI：

```bash
# a11y
npx @axe-core/cli https://my-app.com --tags wcag2a,wcag2aa --save a11y-report.html --exit

# perf
npx lighthouse https://my-app.com --output=json --output-path=./perf.json
```

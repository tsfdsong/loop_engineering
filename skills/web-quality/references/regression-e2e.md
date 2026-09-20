# regression-e2e 子能力 — Playwright E2E 回归

> 本文件由 web-regression-e2e@1.0.0 迁移而来
> 入口：用户触发"E2E 回归 / Playwright / 端到端测试 / 跨浏览器"等关键词
> 本能力是 web-quality 套件的"基础设施层"——另外 3 个子能力（a11y/perf/visual-diff）都依赖它建立的 `e2e/` 目录与 config
> 共享前置见 `shared-setup.md`
> 通用 E2E 方法论（POM / fixtures / test pyramid）见 `testing` skill

## `playwright.config.ts` 所有权

`web-quality` 是 `e2e/playwright.config.ts` 的**唯一 owner**（由 regression-e2e 子能力负责 scaffold）。
其他子能力（visual-diff / a11y / perf）若需调整 config（如 `expect.toMatchSnapshot`、`projects`），
**追加字段**到同一 config，不要新建第二个 config。冲突协商见各子能力的 "config 协作" 段。

## 何时使用

- 项目无 `e2e/` 目录 → scaffold 全套
- 项目有 `e2e/` 但无 CI → 加 workflow
- 两者都有 → 运行 + 报告
- 项目是带路由的单页应用（React/Vue/Angular）
- 项目用 Antd 5.x / Material UI 5.x / Tailwind（Antd 见 `regression-e2e/antd-wait-patterns.md`）

## 何时不用

- 一次性探索性 bug 猎捕 → `agent-browser/dogfood`
- 纯 API 测试 → 项目级 pytest/jest
- 视觉回归 → `references/visual-diff.md`
- 无障碍审计 → `references/a11y.md`
- 性能预算 → `references/perf.md`

## 快速开始（5 步）

1. **探测项目状态**
   ```bash
   test -d e2e && echo "HAS_E2E" || echo "NEEDS_SCAFFOLD"
   test -f playwright.config.ts && echo "HAS_CONFIG"
   test -d .github/workflows && echo "HAS_CI"
   ```

2. **若 `NEEDS_SCAFFOLD`**：问用户项目类型（Antd / MUI / Tailwind / 其他）与目标 URL
3. **若 `HAS_E2E`**：跳到第 5 步（运行）
4. **Scaffold**：从 `regression-e2e/scaffold-templates.md` 复制模板到项目 `e2e/` 目录（覆盖 §1-§10：package.json / playwright.config.ts / fixtures / utils / 示例测试）
5. **运行**：
   ```bash
   cd <project> && npx playwright test --reporter=html,list
   ```

## 工作流

### Phase 1: 项目自检（go 侧，调用本技能前）

经 `/go` 调用时（family `web_qa` / regression），go 先跑这些检查：
- `package.json` 依赖 → 探测 Antd/MUI/Tailwind
- 路由表（React Router/Vue Router）→ 列出待测页面
- 既有 `e2e/` 目录 → 存在则跳过 scaffold
- `ALLOW_DEV_LOGIN` / 认证模式 → 准备 auth fixtures

### Phase 2: Scaffold（仅 `NEEDS_SCAFFOLD` 时）

创建：
```
e2e/
├── package.json
├── playwright.config.ts
├── tsconfig.json
├── .env.example
├── fixtures/
│   ├── auth.ts            # login/logout/session expiry
│   └── test-users.ts      # dev/admin credentials
├── utils/
│   ├── api-helpers.ts
│   ├── selectors.ts       # data-testid registry
│   └── wait-helpers.ts    # Antd-specific waits
└── tests/
    ├── p0/                # critical paths
    └── ux/                # form validation, loading states, error pages
```

### Phase 3: data-testid 钩子（协作）

技能指引用户给组件加 `data-testid="..."`：
- 命名见 `regression-e2e/data-testid-conventions.md`
- Antd 组件见 `regression-e2e/antd-wait-patterns.md`

### Phase 4: 测试执行

```bash
cd e2e && npx playwright test
```

默认 reporter：HTML + list。失败时留 trace 与截图。

### Phase 5: CI 集成

三选一：
- GitHub Actions（推荐，见 `regression-e2e/ci-integration-templates.md` § 1）
- GitLab CI（见 § 2）
- Jenkins（见 § 3）

## 输入（来自 go 或用户）

| 输入 | 必需 | 默认 |
|---|---|---|
| 项目路径 | 是 | cwd |
| 目标 URL（dev/staging） | 是 | — |
| 项目类型（Antd/MUI/Tailwind/其他） | 否 | 自动探测 |
| CI 平台 | 否 | GitHub Actions |
| 浏览器矩阵 | 否 | 仅 Chromium |

## 输出

| 输出 | 路径 |
|---|---|
| `e2e/` scaffold | `<project>/e2e/` |
| HTML 报告 | `<project>/e2e/playwright-report/` |
| Trace 文件（失败时） | `<project>/e2e/test-results/` |
| CI workflow | `<project>/.github/workflows/e2e.yml` |

## references/regression-e2e/（详细参考）

- `regression-e2e/scaffold-templates.md` — e2e/ 目录脚手架源（§1-§10：package.json / playwright.config.ts / fixtures / utils / 示例测试）
- `regression-e2e/data-testid-conventions.md` — 怎么给组件加测试钩子（命名 + 层级）
- `regression-e2e/antd-wait-patterns.md` — Antd Modal/Drawer/Tabs/Form 的等待模式
- `regression-e2e/auth-bypass-patterns.md` — dev login / cookie 注入 / mock JWT
- `regression-e2e/ci-integration-templates.md` — 3 种 CI 平台的 workflow 模板

## 失败模式与恢复

| 症状 | 原因 | 修复 |
|---|---|---|
| 测试等选择器超时 | Antd 动画未完成 | 用 `wait-helpers.ts` 的 `waitForModalOpen()` 替代通用等待 |
| 测试中 401 | auth fixture 未生效 | 验证 `user.extend({ userPage })` 在导航前跑了 `devLogin()` |
| Trace 显示点错元素 | 缺 data-testid | 给组件加 `data-testid`，注册进 `selectors.ts` |
| 本地过 CI 挂 | 环境变量不同 | 同步 `.env` 到 GitHub Secrets（见 `ci-integration-templates.md`） |

---
name: web-regression-e2e
description: Use when generating, scaffolding, or running Playwright E2E regression tests for a web application. Triggers on "regression E2E", "Playwright", "e2e 测试", "回归测试", "scaffold e2e", "CI 集成测试". Works for any web project (Antd, MUI, Tailwind, native HTML). Focus is project-level scaffolding (e2e/ directory, auth fixtures, CI workflows); for general E2E methodology/patterns (POM, fixtures, selectors, test pyramid) use the testing skill. Not for exploratory bug hunting (use agent-browser/dogfood) or unit tests (already covered by project's vitest/jest).
metadata:
  version: "1.0.0"
  engine: "@playwright/test ^1.50.0"
  scope: regression only (not exploratory)
  complements: agent-browser/dogfood
---

# web-regression-e2e

Generate, run, and integrate Playwright regression E2E tests for any web project.

## Prerequisites（首次使用前必装）

| 依赖 | 安装命令 | 说明 |
|---|---|---|
| Node.js ≥ 18 | — | Playwright 运行时 |
| Playwright + 浏览器 | `cd e2e && npm install && npx playwright install --with-deps chromium` | 首次跑必装；`--with-deps` 装系统依赖（Linux）|
| 复用系统 Chrome（可选） | `PLAYWRIGHT_BROWSERS_PATH=0 npx playwright install chromium` | 省 ~300MB 下载 |

> 若项目首次跑：先按 `references/scaffold-templates.md` 生成 `e2e/` 目录，再装依赖。

## `playwright.config.ts` 所有权（A4 约定）

`web-regression-e2e` 是 `e2e/playwright.config.ts` 的**唯一 owner**。
其他 web-* skill（visual-diff / a11y / perf）若需调整 config（如 `expect.toMatchSnapshot`、`projects`），
**追加字段**到同一 config，不要新建第二个 config。冲突协商见各 skill 的 "config 协作" 段。

## When to use

- Project has no `e2e/` directory → scaffold full suite
- Project has `e2e/` but no CI → add workflow
- Project has both → run + report
- Project is single-page app (React/Vue/Angular) with routing
- Project uses Antd 5.x / Material UI 5.x / Tailwind (see `references/antd-wait-patterns.md` for Antd)

## When NOT to use

- One-off exploratory bug hunt → `agent-browser/dogfood`
- API-only testing → project-level pytest/jest
- Visual regression → `web-visual-diff`
- Accessibility audit → `web-audit-a11y`
- Performance budget → `web-perf-budget`

## Quick start (5 steps)

1. **Detect project state**
   ```bash
   test -d e2e && echo "HAS_E2E" || echo "NEEDS_SCAFFOLD"
   test -f playwright.config.ts && echo "HAS_CONFIG"
   test -d .github/workflows && echo "HAS_CI"
   ```

2. **If `NEEDS_SCAFFOLD`**: ask user for project type (Antd / MUI / Tailwind / other) and target URL
3. **If `HAS_E2E`**: skip to step 5 (run)
4. **Scaffold**: copy templates from `references/scaffold-templates.md` to project `e2e/` directory (covers §1-§10: package.json / playwright.config.ts / fixtures / utils / sample tests)
5. **Run**:
   ```bash
   cd <project> && npx playwright test --reporter=html,list
   ```

## Workflow

### Phase 1: Project self-check (orch-side, before invoking this skill)

When invoked via `/orch 6`, orch first runs these checks:
- `package.json` dependencies → detect Antd/MUI/Tailwind
- Routes table (React Router/Vue Router) → list pages to test
- Existing `e2e/` directory → skip scaffold if present
- `ALLOW_DEV_LOGIN` / auth mode → prepare auth fixtures

### Phase 2: Scaffolding (only if `NEEDS_SCAFFOLD`)

Create:
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

### Phase 3: Data-testid hooks (collaborative)

Skill guides user to add `data-testid="..."` to components:
- See `references/data-testid-conventions.md` for naming
- See `references/antd-wait-patterns.md` for Antd components

### Phase 4: Test execution

```bash
cd e2e && npx playwright test
```

Default reporters: HTML + list. Trace and screenshot on failure.

### Phase 5: CI integration

Choose one:
- GitHub Actions (recommended, see `references/ci-integration-templates.md` § 1)
- GitLab CI (see § 2)
- Jenkins (see § 3)

## Inputs (from orch or user)

| Input | Required | Default |
|---|---|---|
| Project path | yes | cwd |
| Target URL (dev/staging) | yes | — |
| Project type (Antd/MUI/Tailwind/other) | no | auto-detect |
| CI platform | no | GitHub Actions |
| Browser matrix | no | Chromium only |

## Outputs

| Output | Path |
|---|---|
| `e2e/` scaffold | `<project>/e2e/` |
| HTML report | `<project>/e2e/playwright-report/` |
| Trace files (on failure) | `<project>/e2e/test-results/` |
| CI workflow | `<project>/.github/workflows/e2e.yml` |

## references/

- `references/scaffold-templates.md` — e2e/ 目录脚手架源（§1-§10：package.json / playwright.config.ts / fixtures / utils / sample tests）
- `references/data-testid-conventions.md` — 怎么给组件加测试钩子（命名 + 层级）
- `references/antd-wait-patterns.md` — Antd Modal/Drawer/Tabs/Form 的等待模式
- `references/auth-bypass-patterns.md` — dev login / cookie 注入 / mock JWT
- `references/ci-integration-templates.md` — 3 种 CI 平台的 workflow 模板

## Failure modes & recovery

| Symptom | Cause | Fix |
|---|---|---|
| Test times out waiting for selector | Antd animation not finished | Use `wait-helpers.ts` `waitForModalOpen()` instead of generic wait |
| 401 errors in tests | Auth fixture not applied | Verify `user.extend({ userPage })` runs `devLogin()` before navigation |
| Trace shows click on wrong element | No data-testid | Add `data-testid` to component, register in `selectors.ts` |
| CI passes locally but fails in CI | Different env vars | Sync `.env` to GitHub Secrets (see `ci-integration-templates.md`) |

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

## When to use

- Project has no `e2e/` directory → scaffold full suite
- Project has `e2e/` but no CI → add workflow
- Project has both → run + report
- Project is single-page app (React/Vue/Angular) with routing
- Project uses Antd 5.x / Material UI 5.x / Tailwind (see `regression-e2e/antd-wait-patterns.md` for Antd)

## When NOT to use

- One-off exploratory bug hunt → `agent-browser/dogfood`
- API-only testing → project-level pytest/jest
- Visual regression → `references/visual-diff.md`
- Accessibility audit → `references/a11y.md`
- Performance budget → `references/perf.md`

## Quick start (5 steps)

1. **Detect project state**
   ```bash
   test -d e2e && echo "HAS_E2E" || echo "NEEDS_SCAFFOLD"
   test -f playwright.config.ts && echo "HAS_CONFIG"
   test -d .github/workflows && echo "HAS_CI"
   ```

2. **If `NEEDS_SCAFFOLD`**: ask user for project type (Antd / MUI / Tailwind / other) and target URL
3. **If `HAS_E2E`**: skip to step 5 (run)
4. **Scaffold**: copy templates from `regression-e2e/scaffold-templates.md` to project `e2e/` directory (covers §1-§10: package.json / playwright.config.ts / fixtures / utils / sample tests)
5. **Run**:
   ```bash
   cd <project> && npx playwright test --reporter=html,list
   ```

## Workflow

### Phase 1: Project self-check (go-side, before invoking this skill)

When invoked via `/go` (family `web_qa` / regression), go first runs these checks:
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
- See `regression-e2e/data-testid-conventions.md` for naming
- See `regression-e2e/antd-wait-patterns.md` for Antd components

### Phase 4: Test execution

```bash
cd e2e && npx playwright test
```

Default reporters: HTML + list. Trace and screenshot on failure.

### Phase 5: CI integration

Choose one:
- GitHub Actions (recommended, see `regression-e2e/ci-integration-templates.md` § 1)
- GitLab CI (see § 2)
- Jenkins (see § 3)

## Inputs (from go or user)

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

## references/regression-e2e/（详细参考）

- `regression-e2e/scaffold-templates.md` — e2e/ 目录脚手架源（§1-§10：package.json / playwright.config.ts / fixtures / utils / sample tests）
- `regression-e2e/data-testid-conventions.md` — 怎么给组件加测试钩子（命名 + 层级）
- `regression-e2e/antd-wait-patterns.md` — Antd Modal/Drawer/Tabs/Form 的等待模式
- `regression-e2e/auth-bypass-patterns.md` — dev login / cookie 注入 / mock JWT
- `regression-e2e/ci-integration-templates.md` — 3 种 CI 平台的 workflow 模板

## Failure modes & recovery

| Symptom | Cause | Fix |
|---|---|---|
| Test times out waiting for selector | Antd animation not finished | Use `wait-helpers.ts` `waitForModalOpen()` instead of generic wait |
| 401 errors in tests | Auth fixture not applied | Verify `user.extend({ userPage })` runs `devLogin()` before navigation |
| Trace shows click on wrong element | No data-testid | Add `data-testid` to component, register in `selectors.ts` |
| CI passes locally but fails in CI | Different env vars | Sync `.env` to GitHub Secrets (see `ci-integration-templates.md`) |

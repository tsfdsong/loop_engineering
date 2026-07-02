# CI 集成模板

## § 1. GitHub Actions (推荐)

`.github/workflows/e2e.yml`:

```yaml
name: E2E Tests

on:
  push:
    branches: [main, test]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Playwright
        run: |
          cd e2e
          npm ci
          npx playwright install --with-deps chromium

      - name: Run E2E
        env:
          BASE_URL: ${{ secrets.STAGING_URL }}
          ADMIN_USER: admin
          ADMIN_PASS: ${{ secrets.ADMIN_PASS }}
        run: cd e2e && npx playwright test --reporter=html,list,github

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: e2e/playwright-report/
          retention-days: 14

      - name: Upload traces (on failure)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: traces
          path: e2e/test-results/
          retention-days: 7
```

## § 2. GitLab CI

`.gitlab-ci.yml`:

```yaml
e2e:
  image: mcr.microsoft.com/playwright:v1.50.0-jammy
  stage: test
  script:
    - cd e2e
    - npm ci
    - npx playwright test --reporter=html,list,junit
  artifacts:
    when: always
    paths:
      - e2e/playwright-report/
      - e2e/test-results/
    reports:
      junit: e2e/test-results/junit.xml
  only:
    - main
    - merge_requests
```

## § 3. Jenkins (declarative)

```groovy
pipeline {
  agent { docker { image 'mcr.microsoft.com/playwright:v1.50.0-jammy' } }
  stages {
    stage('E2E') {
      steps {
        dir('e2e') {
          sh 'npm ci'
          sh 'npx playwright test --reporter=html,list,junit'
        }
      }
    }
  }
  post {
    always {
      publishHTML(target: [reportDir: 'e2e/playwright-report', reportFiles: 'index.html', keepAll: true])
      junit 'e2e/test-results/junit.xml'
    }
  }
}
```

## § 4. 通用建议

- **超时**：CI 单次跑设 30 分钟（本地 10 分钟）
- **重试**：CI 跑 2 次（`retries: 2`），本地 0 次（避免掩盖真问题）
- **并发**：CI 设 1 worker（避免端口冲突），本地不限制
- **缓存**：用 `actions/cache` 缓存 `~/.cache/ms-playwright/`（省 200MB 下载）
- **Secret 管理**：`ADMIN_PASS` 等通过 CI Secret 注入，不入仓

---
name: github-actions-templates
description: |
  TRIGGER: 设置 CI/CD pipeline / GitHub Actions workflow / 自动化测试构建部署 / 'CI/CD' / '部署' / '流水线' / 'GitHub Actions' / 'workflow'（不用于：纯部署策略用 production-readiness，非 CI 自动化）
  RULE: no specific rule（方法论 skill · CI/CD 模板库）
  DETAIL: 本 SKILL.md（GitHub Actions 模板）
---

# GitHub Actions Templates

## 用途

为测试、构建、部署应用创建高效、安全的 GitHub Actions workflow，覆盖多种技术栈。

## 何时使用

- 自动化测试与部署
- 构建 Docker 镜像并推送 registry
- 部署到 Kubernetes 集群
- 跑安全扫描
- 为多环境实现 matrix 构建

## 常用 Workflow 模式

### Pattern 1: 测试 Workflow

```yaml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [18.x, 20.x]

    steps:
    - uses: actions/checkout@v4

    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run linter
      run: npm run lint

    - name: Run tests
      run: npm test

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage/lcov.info
```

**参考：** 见 `assets/test-workflow.yml`

### Pattern 2: 构建并推送 Docker 镜像

```yaml
name: Build and Push

on:
  push:
    branches: [ main ]
  tags: [ 'v*' ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

**参考：** 见 `assets/deploy-workflow.yml`

### Pattern 3: 部署到 Kubernetes

```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2

    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name production-cluster --region us-west-2

    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
        kubectl rollout status deployment/my-app -n production
        kubectl get services -n production

    - name: Verify deployment
      run: |
        kubectl get pods -n production
        kubectl describe deployment my-app -n production
```

### Pattern 4: Matrix 构建

```yaml
name: Matrix Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}

    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: pytest
```

**参考：** 见 `assets/matrix-build.yml`

## Workflow 最佳实践

1. **用确定的 action 版本**（@v4，不用 @latest）
2. **缓存依赖**加速构建
3. 敏感数据**用 secrets**
4. PR 上**实现 status checks**
5. 多版本测试**用 matrix 构建**
6. **设置恰当的 permissions**
7. 常见模式**用 reusable workflows**
8. 生产环境**实现审批门**
9. 失败时**加通知步骤**
10. 敏感工作负载**用 self-hosted runners**

## Reusable Workflows

```yaml
# .github/workflows/reusable-test.yml
name: Reusable Test Workflow

on:
  workflow_call:
    inputs:
      node-version:
        required: true
        type: string
    secrets:
      NPM_TOKEN:
        required: true

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
    - run: npm ci
    - run: npm test
```

**调用 reusable workflow：**
```yaml
jobs:
  call-test:
    uses: ./.github/workflows/reusable-test.yml
    with:
      node-version: '20.x'
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## 安全扫描

```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

    - name: Run Snyk Security Scan
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

## 带审批的部署

```yaml
name: Deploy to Production

on:
  push:
    tags: [ 'v*' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com

    steps:
    - uses: actions/checkout@v4

    - name: Deploy application
      run: |
        echo "Deploying to production..."
        # Deployment commands here

    - name: Notify Slack
      if: success()
      uses: slackapi/slack-github-action@v1
      with:
        webhook-url: ${{ secrets.SLACK_WEBHOOK }}
        payload: |
          {
            "text": "Deployment to production completed successfully!"
          }
```

## 参考文件

- `assets/test-workflow.yml` —— 测试 workflow 模板
- `assets/deploy-workflow.yml` —— 部署 workflow 模板
- `assets/matrix-build.yml` —— matrix 构建模板
- `references/common-workflows.md` —— 常用 workflow 模式

## 相关技能

- `gitlab-ci-patterns` —— GitLab CI workflow
- `deployment-pipeline-design` —— 流水线架构
- `secrets-management` —— secrets 管理

## 边界

- 仅当任务明确匹配上述范围时使用本技能。
- 不要把输出当作环境特定验证、测试或专家评审的替代品。
- 缺少必需输入、权限、安全边界或成功标准时，停下来问清楚。

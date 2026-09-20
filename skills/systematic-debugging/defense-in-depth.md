# Defense-in-Depth Validation（纵深防御校验）

## Overview（概述）

修完一个坏数据引起的 bug 后，在一处加校验感觉够了。但单一检查会被不同代码路径、重构或 mock 绕过。

**核心原则：** 数据经过的**每一层**都校验。让 bug 在结构上不可能。

## 为什么要多层

单一校验："我们修好了这个 bug"
多层校验："我们让这个 bug 不可能发生"

不同层抓不同情况：
- 入口校验抓大多数 bug
- 业务逻辑抓边界情况
- 环境守卫防上下文特定的危险
- 调试日志在其他层失效时兜底

## 四层防御

### 层 1：入口点校验
**目的：** 在 API 边界拒绝明显非法输入

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  if (!statSync(workingDirectory).isDirectory()) {
    throw new Error(`workingDirectory is not a directory: ${workingDirectory}`);
  }
  // ... proceed
}
```

### 层 2：业务逻辑校验
**目的：** 确保数据对该操作有意义

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

### 层 3：环境守卫
**目的：** 阻止特定上下文中的危险操作

```typescript
async function gitInit(directory: string) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // ... proceed
}
```

### 层 4：调试埋点
**目的：** 为取证捕获上下文

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', {
    directory,
    cwd: process.cwd(),
    stack,
  });
  // ... proceed
}
```

## 应用此模式

发现 bug 时：

1. **追数据流** —— 坏值从哪来？在哪被用？
2. **映射全部检查点** —— 列出数据经过的每一处
3. **每层加校验** —— 入口、业务、环境、调试
4. **逐层测试** —— 试着绕过层 1，验证层 2 能抓住

## 会话实例

bug：空 `projectDir` 导致 `git init` 跑进源代码

**数据流：**
1. 测试 setup → 空字符串
2. `Project.create(name, '')`
3. `WorkspaceManager.createWorkspace('')`
4. `git init` 跑在 `process.cwd()`

**加了四层：**
- 层 1：`Project.create()` 校验非空/存在/可写
- 层 2：`WorkspaceManager` 校验 projectDir 非空
- 层 3：`WorktreeManager` 测试中拒绝 tmpdir 外 git init
- 层 4：git init 前 stack trace 日志

**结果：** 1847 个测试全过，bug 无法复现

## 关键洞见

四层都必要。测试期间，每层都抓到过其他层漏掉的 bug：
- 不同代码路径绕过了入口校验
- mock 绕过了业务逻辑检查
- 不同平台的边界情况需要环境守卫
- 调试日志识别出结构性误用

**不要停在一个校验点。** 每层都加检查。

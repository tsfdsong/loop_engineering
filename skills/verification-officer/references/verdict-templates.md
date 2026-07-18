# verdict.json 模板库

验证官（verification-officer）按 task_type 选择对应模板写入 `.verify-state/<SID>/verdict.json`。

## 通用 schema

```json
{
  "task": "string         — 任务简述",
  "task_type": "frontend|api|backend|script|config",
  "status": "VERIFIED|FAILED|BLOCKED|NEEDS_CONTEXT",
  "timestamp": "ISO8601 UTC",
  "verifier": "subagent:verification-officer | self",
  "reason": "string        — FAILED/BLOCKED 时必填，VERIFIED 时可省略",
  "evidence": { ... },      — 验证证据（命令输出/断言结果）
  "failures": [ ... ],      — FAILED 时必填，逐条列失败项
  "root_cause_classification": "A|B|C|🎨"
}
```

## frontend — 完整 F1-F5

### VERIFIED

```json
{
  "task": "用户登录页面",
  "task_type": "frontend",
  "status": "VERIFIED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "evidence": {
    "browser_errors": 0,
    "network_status_codes": ["200", "200", "201"],
    "network_failures": [],
    "snapshot_hits": {
      "login_form": true,
      "submit_button": true,
      "error_message_element": true
    },
    "interaction_steps_verified": 4
  }
}
```

### FAILED（根因 A：代码 bug）

```json
{
  "task": "用户登录页面",
  "task_type": "frontend",
  "status": "FAILED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "reason": "F1 有 1 个 JS error + F3 登录按钮渲染缺失",
  "evidence": {
    "browser_errors": 1,
    "network_failures": []
  },
  "failures": [
    {
      "gate": "F1",
      "detail": "TypeError: Cannot read property 'onSubmit' of undefined @ LoginForm.tsx:28",
      "root_cause": "A — 组件 props 未传递 onSubmit handler"
    },
    {
      "gate": "F3",
      "detail": "snapshot 中未找到 submit 按钮（@ref 查找失败）",
      "root_cause": "A — 因 F1 error 导致按钮未渲染"
    }
  ],
  "root_cause_classification": "A"
}
```

### BLOCKED（根因 C：环境）

```json
{
  "task": "用户登录页面",
  "task_type": "frontend",
  "status": "BLOCKED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "reason": "G0 失败：后端 API 服务未启动，POST /api/login 连接被拒",
  "blocker": "environment",
  "suggested_fix": "docker-compose up -d api && 等待端口 8000 就绪"
}
```

## api — HTTP 端点

### VERIFIED

```json
{
  "task": "用户注册 API",
  "task_type": "api",
  "status": "VERIFIED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "evidence": {
    "endpoints_tested": [
      {
        "method": "POST",
        "url": "/api/v1/users/register",
        "status": 201,
        "response_has_fields": ["id", "email", "created_at"]
      }
    ]
  }
}
```

### FAILED

```json
{
  "task": "用户注册 API",
  "task_type": "api",
  "status": "FAILED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "reason": "POST /api/v1/users/register 返回 500",
  "evidence": {
    "endpoints_tested": [
      {
        "method": "POST",
        "url": "/api/v1/users/register",
        "status": 500,
        "response_body_snippet": "{\"error\": \"IntegrityError: duplicate email\"}"
      }
    ]
  },
  "failures": [
    {
      "gate": "status_code",
      "detail": "期望 201，实际 500",
      "root_cause": "A — 缺少 email 唯一性校验"
    }
  ],
  "root_cause_classification": "A"
}
```

## backend — 测试 + 红绿循环

### VERIFIED（含红绿循环）

```json
{
  "task": "修复 #42 分页 off-by-one bug",
  "task_type": "backend",
  "status": "VERIFIED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "evidence": {
    "test_command": "pytest tests/test_pagination.py -v",
    "test_exit_code": 0,
    "tests_passed": 8,
    "tests_failed": 0,
    "red_green_verified": true,
    "red_green_detail": "revert fix → test_page_boundary FAILS → restore → test PASSES"
  }
}
```

### FAILED

```json
{
  "task": "修复 #42 分页 off-by-one bug",
  "task_type": "backend",
  "status": "FAILED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "reason": "2 个测试失败 + 红绿循环未通过（revert 后测试仍 PASS = 测试无效）",
  "evidence": {
    "test_exit_code": 1,
    "tests_passed": 6,
    "tests_failed": 2,
    "red_green_verified": false,
    "red_green_detail": "revert fix 后 test_page_boundary 仍然 PASS → 测试未覆盖该 bug"
  },
  "failures": [
    {
      "gate": "test_pass",
      "detail": "test_page_offset[limit=10] FAILED: assert 9 == 10"
    },
    {
      "gate": "red_green",
      "detail": "revert 后测试仍 PASS，说明回归测试无效"
    }
  ],
  "root_cause_classification": "B — 验证脚本（测试）本身未正确覆盖 bug"
}
```

## script — 黄金路径裸命令

### VERIFIED

```json
{
  "task": "install.sh 一键安装",
  "task_type": "script",
  "status": "VERIFIED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "evidence": {
    "command_run": "curl -fsSL https://example.com/install.sh | bash",
    "exit_code": 0,
    "duration_seconds": 12,
    "clean_env_tested": true,
    "zero_flags": true,
    "output_contains_expected": "✅ 安装完成"
  }
}
```

### FAILED（hang 场景 · 来自 L#002 教训）

```json
{
  "task": "install.sh 一键安装",
  "task_type": "script",
  "status": "FAILED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "reason": "命令 hang（永不退出），非 fail。git pull 指向不存在 URL 时反复重试 TCP",
  "evidence": {
    "command_run": "timeout 30 bash install.sh",
    "exit_code": 124,
    "timeout_seconds": 30,
    "hang_detected": true,
    "process_tree": "1 bash → 7 git subprocess (永不退出)"
  },
  "failures": [
    {
      "gate": "golden_path",
      "detail": "timeout 30s 后仍未退出（hang 非 fail）",
      "root_cause": "A — git pull 无 timeout 降级路径"
    }
  ],
  "root_cause_classification": "A"
}
```

## config — 语法 + 引用

### VERIFIED

```json
{
  "task": "新增 .env.example 配置",
  "task_type": "config",
  "status": "VERIFIED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "evidence": {
    "syntax_valid": true,
    "paths_referenced_exist": ["./logs/", "./data/"],
    "env_vars_documented": ["DATABASE_URL", "REDIS_URL", "JWT_SECRET"]
  }
}
```

### FAILED

```json
{
  "task": "新增 .env.example 配置",
  "task_type": "config",
  "status": "FAILED",
  "timestamp": "2026-07-15T13:00:00Z",
  "verifier": "subagent:verification-officer",
  "reason": "引用了不存在的路径 ./logs/prod/",
  "evidence": {
    "syntax_valid": true,
    "paths_referenced_exist": [],
    "paths_missing": ["./logs/prod/"],
    "env_vars_undocumented": ["SECRET_KEY"]
  },
  "failures": [
    {
      "gate": "reference_integrity",
      "detail": "路径 ./logs/prod/ 不存在",
      "root_cause": "A — 需创建目录或修正路径"
    }
  ],
  "root_cause_classification": "A"
}
```

## 根因分类速查（复用 self-healing.md）

| 类型 | 判定特征 | 验证官处置 |
|------|---------|-----------|
| **A. 代码 bug** | 堆栈指向业务代码 / 渲染不符 / 逻辑错 | 写 FAILED，建议 implementer 修代码 |
| **B. 验证脚本错** | ref 失效 / 选择器定位失败 / 测试逻辑错 | 写 FAILED，建议修测试而非代码 |
| **C. 环境问题** | 服务没起 / 端口不通 / 登录态过期 | 写 BLOCKED（非代码问题） |
| **🎨 主观项** | 配色 / 间距 / 风格 | 写 VERIFIED + 标注"🎨 设计待确认" |

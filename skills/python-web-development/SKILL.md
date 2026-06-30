---
name: python-web-development
description: "Use when designing REST/GraphQL APIs, implementing API security (rate limit, JWT, OAuth2), or building async Python web apps (asyncio/aiohttp/FastAPI). Triggers on API 设计, REST, GraphQL, JWT, OAuth, asyncio, FastAPI, aiohttp. Do NOT use for: frontend code, or non-Python web frameworks."
metadata:
  version: "1.0"
  type: skill
  sources:
    - community (api-design-principles)
    - community (api-security-best-practices)
    - community (auth-implementation-patterns)
    - community (async-python-patterns)
  merged_from:
    - api-development
    - code-engineering (Python 异步部分)
  merge_date: "2026-06-30"
  merge_reason: "v6.4 合并 — API 开发与 Python 异步 Web 同属后端开发领域，合并为完整工作流"
  audience: Python 后端开发工程师
  not_invoked_by: loop / go（被动技能，由用户/任务触发）
---

# Python Web Development 超级技能

Python 后端开发的完整工作流：从 API 设计 → 安全加固 → 认证授权 → 异步决策 → 异步实现 → 测试上线。

## 何时使用

- 设计新的 REST/GraphQL API（资源建模、错误处理、版本化）
- 给现有 API 加固安全（限流、输入验证、注入防护）
- 实现用户认证（session / JWT / OAuth2 / OIDC / RBAC）
- 决定同步 vs 异步（I/O 密集 vs CPU 密集）
- 构建异步 Web 服务（FastAPI / aiohttp / Sanic）
- 实现异步 I/O 操作（数据库、爬虫、WebSocket、后台任务）
- 调试异步代码（取消、超时、异常传播）

## 何时不用

- 纯前端 UI 工作
- 纯基础设施（无 API 契约）
- 任务只在桌面/CLI 脚本中
- CPU 密集型计算（异步无收益）

---

## 第一阶段 · API 设计（资源建模 + 契约）

### 资源建模

- **资源是名词而非动词**：`/users` 而非 `/getUsers`
- **集合用复数**：单数 `user` / 复数 `users`
- **命名跨端点一致**：核心实体（如 `User`）在所有引用点统一
- **层级不超过 2 层**：`/users/{id}/orders` 而非 `/users/{id}/orders/{oid}/items/{iid}/...`
- **HTTP 方法映射 CRUD**：

| 操作 | HTTP | 幂等 | 状态码 |
|------|------|:---:|--------|
| 列出/读取 | GET | ✅ | 200 |
| 创建 | POST | ❌ | 201 |
| 全量替换 | PUT | ✅ | 200/204 |
| 部分更新 | PATCH | ❌ | 200 |
| 删除 | DELETE | ✅ | 200/204 |

### 错误响应统一

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "email 格式不合法",
    "field": "email",
    "timestamp": "2026-06-30T10:00:00Z"
  }
}
```

### 分页与限流

- **分页**：cursor-based（推荐）或 offset-based，每页默认 20 / 上限 100
- **过滤**：query params（`?status=active&sort=-created_at`）
- **稀疏字段集**：`?fields=id,name`（减少响应体）
- **限流头**：`X-RateLimit-Limit` / `X-RateLimit-Remaining` / `Retry-After`

### 详细模式（按需查阅）

- **REST 详细模式**（408 行）：[references/rest-best-practices.md](references/rest-best-practices.md)
- **GraphQL Schema 设计**（583 行）：[references/graphql-schema-design.md](references/graphql-schema-design.md)
- **API 设计检查清单**（155 行）：[assets/api-design-checklist.md](assets/api-design-checklist.md)
- **REST 模板代码**：[assets/rest-api-template.py](assets/rest-api-template.py)

---

## 第二阶段 · API 安全（10 大要点）

> 完整 915 行内容：[references/api-security-full.md](references/api-security-full.md)

| # | 防护 | 关键措施 |
|---|------|---------|
| 1 | **认证 / 授权** | 详见第三阶段（JWT / OAuth2 / RBAC） |
| 2 | **输入验证** | 白名单 + 长度限制 + 字段类型严格校验 |
| 3 | **限流节流** | 每用户/IP 限流，超限返回 429 + `Retry-After` |
| 4 | **CORS** | 白名单 origin，禁止 `Access-Control-Allow-Origin: *` |
| 5 | **CSRF** | CSRF token + SameSite cookie + Origin/Referer 校验 |
| 6 | **注入防护** | 参数化查询（防 SQLi）/ ORM / 转义输出（防 XSS） |
| 7 | **敏感数据** | 加密存储 + 脱敏输出 + 不在 URL 放密钥 |
| 8 | **错误处理** | 不泄露栈信息，外部错误通用化（`{"error": "internal"}`） |
| 9 | **审计日志** | 关键操作（登录/支付/删除）不可篡改 + 用户/IP/时间戳 |
| 10 | **依赖安全** | 定期 `pip-audit` / `npm audit` 扫描 + 漏洞订阅 |

### 关键防护的 FastAPI 实现

```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI()

# 4. CORS 白名单
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # 白名单，不要用 *
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
)

# 3. 限流
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/users/{user_id}")
@limiter.limit("100/minute")  # 每 IP 100 次/分钟
async def get_user(request: Request, user_id: int):
    # 2. 输入验证（FastAPI 自动从 path 校验类型）
    if user_id <= 0:
        # 8. 不泄露内部信息
        raise HTTPException(status_code=400, detail="Invalid user id")
    # 9. 审计日志
    logger.info("user.access", extra={"user_id": user_id, "ip": request.client.host})
    return {"id": user_id, "name": "..."}
```

---

## 第三阶段 · 认证授权（AuthN / AuthZ）

### 选型决策

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 传统 Web 应用（服务端渲染） | **Session + Cookie** | 简单、可控、易撤销 |
| SPA / 移动端 API | **JWT（短期 + Refresh）** | 无状态、跨域友好 |
| 第三方登录 / 联邦身份 | **OAuth2 / OIDC** | 标准化、不存密码 |
| 微服务间调用 | **JWT + mTLS** | 双向认证、零信任 |
| 内部系统 | **mTLS / Service Account** | 高安全、低运维 |

### JWT 实现要点

```python
from datetime import datetime, timedelta, timezone
import jwt

# 签发
def issue_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),  # 短期
        "iss": "api.example.com",
        "aud": "web.example.com",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# 校验（带完整异常处理）
def verify_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, SECRET_KEY,
            algorithms=["HS256"],  # 白名单算法
            audience="web.example.com",
            issuer="api.example.com",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### RBAC（基于角色的访问控制）

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

PERMISSIONS = {
    Role.ADMIN: {"read", "write", "delete"},
    Role.EDITOR: {"read", "write"},
    Role.VIEWER: {"read"},
}

def require_permission(action: str):
    def checker(user: User = Depends(get_current_user)):
        if action not in PERMISSIONS.get(user.role, set()):
            raise HTTPException(403, f"Role {user.role} cannot {action}")
        return user
    return checker

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, _: User = Depends(require_permission("delete"))):
    ...
```

### Safety（红线 · 不可违反）

- ❌ **绝不**记录密钥、token、凭证到日志
- ❌ **绝不**把密钥提交到 git（用 `python-dotenv` + `.env` + `.gitignore`）
- ✅ 强制最小权限（每个 token 只授予必需的 scope）
- ✅ 密钥定期轮换（建议 90 天）
- ✅ Refresh token 存 HttpOnly + Secure + SameSite=Strict cookie
- ✅ Access token 短期（≤ 15 分钟）

---

## 第四阶段 · 异步决策（同步 vs 异步）

### 何时用异步

| 场景 | 同步 | 异步 | 原因 |
|------|:---:|:---:|------|
| **I/O 密集**（DB/网络/文件） | ⚠️ | ✅ | 异步不阻塞，能并发处理多请求 |
| **CPU 密集**（计算/压缩/加密） | ✅ | ❌ | GIL 限制，异步无收益 |
| **WebSocket / 长连接** | ❌ | ✅ | 异步是天然契合 |
| **高并发 HTTP API** | ⚠️ | ✅ | 单进程并发数从 ~50 提升到 ~10000 |
| **简单脚本** | ✅ | ❌ | 异步增加复杂度，无收益 |

### 异步不是银弹 · 性能权衡

- 异步代码**不一定更快**——CPU 密集任务无收益（GIL 限制）
- 异步增加心智负担：取消、异常传播、上下文传递都更复杂
- 异步生态不如同步成熟（很多库不支持 async）
- 异步调试更困难（stack trace 跨 event loop）

### 决策树

```
任务主要是 I/O？
├─ 是 → 高并发（>100 QPS）？ → ✅ 异步
│       └─ 否 → 同步即可
└─ 否（CPU 密集） → 多进程 / C 扩展，不要用异步
```

---

## 第五阶段 · 异步实现

### asyncio 核心 API

| API | 用途 | 示例 |
|-----|------|------|
| `async def` | 定义协程 | `async def fetch(url): ...` |
| `await` | 等待可等待对象 | `result = await fetch(url)` |
| `asyncio.gather` | 并发执行多个协程 | `await asyncio.gather(*tasks)` |
| `asyncio.create_task` | 后台执行 | `task = asyncio.create_task(coro())` |
| `asyncio.Queue` | 异步队列 | `await queue.put(item)` |
| `asyncio.Semaphore` | 并发限制 | `async with sem: ...` |
| `asyncio.wait_for` | 超时控制 | `await asyncio.wait_for(coro(), timeout=5)` |
| `asyncio.run` | 入口启动 | `asyncio.run(main())` |

### 异步 Web 框架对比

| 框架 | 性能 | 生态 | 适用 |
|------|:---:|:---:|------|
| **FastAPI** | 高 | 🟢 丰富 | 通用 API + 自动 OpenAPI |
| **aiohttp** | 高 | 🟡 中等 | 高性能 client + 简单 server |
| **Sanic** | 极高 | 🟡 中等 | 超高性能 API |
| **Starlette** | 极高 | 🟡 偏底层 | 需要定制时 |

### 异步 I/O 客户端

- **HTTP 客户端**：`aiohttp.ClientSession`（替代 `requests`）
- **PostgreSQL**：`asyncpg`（替代 `psycopg2`）
- **Redis**：`aiomcache` / `redis.asyncio`
- **MySQL**：`aiomysql`
- **MongoDB**：`motor`

### 标准模式：并发 + 超时 + 限流

```python
import asyncio
import aiohttp

async def fetch(session, url, sem):
    async with sem:  # 限流：最多 10 并发
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return await resp.json()
        except asyncio.TimeoutError:
            return {"error": "timeout", "url": url}

async def fetch_all(urls):
    sem = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url, sem) for url in urls]
        # gather 全部完成，return_exceptions 让单个失败不影响其他
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### 异步代码红线

- ❌ **不要在 async 中阻塞**：禁用 `time.sleep` / `requests` / 同步 I/O
- ❌ **不要忘了 await**：没 await 的协程不会执行，silently 失败
- ❌ **不要在 event loop 中跑 CPU 密集**：用 `loop.run_in_executor` 扔到线程池
- ✅ 资源用 `async with` 管理（连接、锁、文件）
- ✅ 异常用结构化处理（gather + return_exceptions）
- ✅ 取消要传播（asyncio.CancelledError 重新抛）

### 详细示例（按需查阅）

- **异步实现手册**（678 行）：[resources/async-playbook.md](resources/async-playbook.md)
- **API 实施手册**（513 行）：[resources/implementation-playbook.md](resources/implementation-playbook.md)
- **API 安全完整 915 行**：[references/api-security-full.md](references/api-security-full.md)
- **REST 实现模式 408 行**：[references/rest-best-practices.md](references/rest-best-practices.md)
- **GraphQL Schema 583 行**：[references/graphql-schema-design.md](references/graphql-schema-design.md)

---

## 整合使用流程

### 场景 1 · 新建 Python Web API

```
Step 1 (设计): 资源建模 + HTTP 方法映射 + 错误响应统一
  ↓ 输出: API 契约文档
Step 2 (安全): 10 大要点逐条对照（限流/CORS/输入验证/CSRF/注入...）
  ↓ 输出: 安全检查清单
Step 3 (认证): 选 session/JWT/OAuth2 + RBAC 策略
  ↓ 输出: 认证流程图 + token 设计
Step 4 (异步决策): I/O 密集? 高并发? → 决定同步 vs 异步
  ↓ 输出: 架构决策记录（ADR）
Step 5 (实现): FastAPI / aiohttp + 异步客户端 + 资源管理
  ↓ 输出: 可运行代码
Step 6 (测试): 单元 + 集成 + 异步代码路径覆盖（详见 testing 技能）
```

### 场景 2 · 加固现有 API

```
Step 1: 完整阅读 references/api-security-full.md
Step 2: 修复 Critical 风险（注入/认证缺失/密钥泄露）
Step 3: 修复 Important 风险（限流/CORS/CSRF）
Step 4: 添加审计日志 + 监控告警
Step 5: 压测验证（限流生效、并发不崩）
```

### 场景 3 · 同步转异步

```
Step 1: 评估是否值得转（I/O 密集？高并发？性能瓶颈？）
Step 2: 从最热的端点开始（不要全面铺开）
Step 3: 同步库换异步库（requests → aiohttp，psycopg2 → asyncpg）
Step 4: 异步路由 + 异步依赖注入
Step 5: 异步测试覆盖（pytest-asyncio）
Step 6: 监控 + 对比（QPS / p99 延迟 / 资源占用）
```

### 场景 4 · 异步代码 Bug 排查

```
Step 1: 是取消（CancelledError）？还是超时？还是异常吞噬？
Step 2: 堆栈是否在 event loop 边界断开？
Step 3: 是否有阻塞调用污染了 event loop？（asyncio 检测：loop.slow_callback_duration）
Step 4: 资源是否泄漏？（未关闭的 session / connection）
Step 5: 加入结构化日志（contextvars 传递 request_id）
```

---

## 与其他技能配合

| 场景 | 配合技能 |
|------|---------|
| 设计阶段需求探索 | `brainstorming` / `product-manager` |
| 架构决策 ADR | `software-architecture`（DDIA 分布式系统） |
| 写自动化测试 | `testing`（TDD + 异步测试） |
| 代码审查 | `code-reviewer`（API 安全检查清单） |
| 上线前审计 | `production-readiness`（限流/熔断/容量） |
| 调试异步 Bug | `systematic-debugging` |

---

## 限制

- **不替代环境特定验证** — 不同框架（FastAPI / Django / Flask）有各自最佳实践
- **不替代实际测试** — 安全要点必须配渗透测试
- **不替代人工审查** — 复杂业务规则需架构师判断
- **不适用 Python 2 / 同步阻塞库** — 本技能假设 Python 3.10+ asyncio
- **不覆盖前端** — 跨域 / CORS 仅给后端配置

---

## 迁移说明

- v6.4 合并前：api-development（API 设计/安全/认证） + code-engineering（Python 异步部分） 两个独立技能
- v6.4 合并后：python-web-development 一个超级技能
- 完整内容保留在 references/ 和 resources/
- orch 调度表已同步：api-development / code-engineering 行已移除
- 计数：v6.3 (36) - 1 = v6.4 (35)

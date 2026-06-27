---
id: VER-001
domain: verification
severity: high
applies_when:
  - task_type: backend
  - task_type: fullstack
  - has_database: true
source: loop/mcp-plaza-0626
created: 2026-06-26
---

## 远程 DB 连不上时禁止用单测替代集成验证

**问题**: loop/mcp-plaza-0626 任务中，后端因远程数据库拒绝连接，直接降级为"只跑不依赖 DB 的单元测试（101 passed）"，然后声称"验证通过"。实际所有 API 端点都返回 500，功能完全不可用。

**根因**: 把"单元测试通过"等同于"集成验证通过"。单元测试用 mock/内存 DB，绕过了真实依赖，无法发现 DB 连接、ORM 映射、迁移遗漏等问题。环境不通时选择"放过自己"而非"修通环境"。

**规则**:
- 门禁矩阵 **G1（依赖可达）是所有非纯文档任务的强制前置**——DB/Redis/外部 API 任一不可达，禁止进入后续维度
- G1 不通时，**优先用 docker-compose 起本地依赖**（见 ENV-001），修通后再继续
- **绝对禁止**用单元测试通过来替代集成验证（G5）
- 环境确实无法修通时，进入**阻塞保护**如实汇报，**禁止声称验证通过**

**关联门禁**: G1, G5

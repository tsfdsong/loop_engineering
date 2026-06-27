---
id: BE-001
domain: backend
severity: medium
applies_when:
  - task_type: backend
  - task_type: fullstack
  - tech_stack: sqlalchemy
  - tech_stack: pydantic
source: loop/mcp-plaza-0626
created: 2026-06-26
---

## ORM JSONB 字段返回 API 时需手动转 Pydantic 模型

**问题**: loop/mcp-plaza-0626 中新增 `GET /mcp/publish/tools/{tool_id}/adapters/{version_id}` 端点时，直接把 ORM 对象的 JSONB 字段（如 `auth_config`、`request_mapping`）返回给 FastAPI 的 `response_model`。Pydantic 的 `model_validate` / `from_attributes` **不会自动**把 JSONB 存储的 `dict` 解包成嵌套的 Pydantic 模型（如 `AuthConfig`），导致类型校验失败或字段丢失。

**根因**: PostgreSQL JSONB 列在 ORM 中是 `dict`/`list`，Pydantic v2 的 `from_attributes=True` 只做顶层属性映射，不递归把 `dict` 转成嵌套 `BaseModel`。需要手动 `AuthConfig(**adapter.auth_config)` 构造。

**规则**:
- 当 ORM 模型有 JSONB 字段且该字段对应一个 Pydantic 嵌套模型时，API 端点**不能直接返回 ORM 对象**
- 必须手动构造：`嵌套模型(**orm_obj.jsonb_field)` 或在 `to_response` helper 中转换
- 写完此类端点后，**G5（集成冒烟）必须真实请求该端点**验证返回结构（mock 测不出这个问题）
- 如果 JSONB 字段可能为 None，转换时提供默认值：`AuthConfig(**(obj.field or {}))`

**关联门禁**: G5, G6

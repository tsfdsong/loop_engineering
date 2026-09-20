---
name: database-design
description: |
  TRIGGER: 设计数据库 schema / 索引 / 迁移 / 选 SQL/NoSQL/ORM/serverless / '数据库' / 'SQL' / '表设计' / '索引' / 'schema' / 'migration'（不用于：应用代码用 python-web-development，纯架构用 software-architecture）
  RULE: no specific rule（方法论 skill · 数据库设计方法论）
  DETAIL: 本 SKILL.md（schema/索引/迁移/选型）
---

# Database Design

> **Learn to THINK, not copy SQL patterns.**

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

| File | Description | When to Read |
|------|-------------|--------------|
| `references/database-selection.md` | PostgreSQL vs Neon vs Turso vs SQLite | Choosing database |
| `references/orm-selection.md` | Drizzle vs Prisma vs Kysely | Choosing ORM |
| `references/schema-design.md` | Normalization, PKs, relationships | Designing schema |
| `references/indexing.md` | Index types, composite indexes | Performance tuning |
| `references/optimization.md` | N+1, EXPLAIN ANALYZE | Query optimization |
| `references/migrations.md` | Safe migrations, serverless DBs | Schema changes |

## 决策示例

需求：电商订单，查询模式 = 按用户列订单 + 按状态统计未完成单。

**反选项**（红线 R1.1）：
- 单表全字段（含商品快照 50 列）→ 否决：商品信息冗余膨胀、更新异常
- 订单 + 订单项 1:N（order_items 存商品快照）→ ✅ 采用

**关键决策**：
- PK 用 `BIGINT GENERATED ALWAYS AS IDENTITY` 而非 UUIDv4（B-tree 索引膨胀 2-3x）
- `(user_id, created_at DESC)` 复合索引覆盖"按用户列订单"；状态统计走部分索引 `(status, created_at) WHERE status != 'COMPLETED'`

→ PK 取舍见 `references/schema-design.md`，索引设计见 `references/indexing.md`。

---

## ⚠️ Core Principle

- ASK user for database preferences when unclear
- Choose database/ORM based on CONTEXT
- Don't default to PostgreSQL for everything

---

## Decision Checklist

Before designing schema:

- [ ] Asked user about database preference?
- [ ] Chosen database for THIS context?
- [ ] Considered deployment environment?
- [ ] Planned index strategy?
- [ ] Defined relationship types?

---

## Anti-Patterns

❌ Default to PostgreSQL for simple apps (SQLite may suffice)
❌ Skip indexing
❌ Use SELECT * in production
❌ Store JSON when structured data is better
❌ Ignore N+1 queries

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.

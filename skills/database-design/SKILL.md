---
name: database-design
description: |
  TRIGGER: 设计数据库 schema / 索引 / 迁移 / 选 SQL/NoSQL/ORM/serverless / '数据库' / 'SQL' / '表设计' / '索引' / 'schema' / 'migration'（不用于：应用代码用 python-web-development，纯架构用 software-architecture）
  RULE: no specific rule（方法论 skill · 数据库设计方法论）
  DETAIL: 本 SKILL.md（schema/索引/迁移/选型）
---

# Database Design

> **学的是思考，不是抄 SQL 模式。**

## 🎯 选择性阅读规则

**只读与请求相关的文件！** 查内容地图，找到需要的再读。

| 文件 | 内容 | 何时读 |
|------|------|--------|
| `references/database-selection.md` | PostgreSQL vs Neon vs Turso vs SQLite | 选数据库 |
| `references/orm-selection.md` | Drizzle vs Prisma vs Kysely | 选 ORM |
| `references/schema-design.md` | Normalization、PK、关系 | 设计 schema |
| `references/indexing.md` | 索引类型、复合索引 | 性能调优 |
| `references/optimization.md` | N+1、EXPLAIN ANALYZE | 查询优化 |
| `references/migrations.md` | 安全迁移、serverless DB | schema 变更 |

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

## ⚠️ 核心原则

- 数据库偏好不明时**问用户**
- 基于上下文选数据库/ORM
- 不要什么都默认 PostgreSQL

---

## 决策清单

设计 schema 之前：

- [ ] 问过用户数据库偏好吗？
- [ ] 为**此**上下文选定数据库了吗？
- [ ] 考虑过部署环境吗？
- [ ] 规划过索引策略吗？
- [ ] 定义过关系类型吗？

---

## 反模式

❌ 简单应用默认上 PostgreSQL（SQLite 可能就够）
❌ 跳过索引
❌ 生产环境用 SELECT *
❌ 结构化数据更适合时却存 JSON
❌ 无视 N+1 查询

## 何时使用
本技能适用于执行上述范围的工作流或操作。

## 边界
- 仅当任务明确匹配上述范围时使用本技能。

# ORM Selection (2025)

> 基于部署与 DX 需求选 ORM。

## 决策树

```
What's the context?
│
├── Edge deployment / Bundle size matters
│   └── Drizzle (smallest, SQL-like)
│
├── Best DX / Schema-first
│   └── Prisma (migrations, studio)
│
├── Maximum control
│   └── Raw SQL with query builder
│
└── Python ecosystem
    └── SQLAlchemy 2.0 (async support)
```

（边缘部署/包体积敏感→Drizzle（最小、类 SQL）；最佳 DX/schema 优先→Prisma（migration、studio）；最大控制→原生 SQL + query builder；Python 生态→SQLAlchemy 2.0（async 支持）。）

## 对比

| ORM | 最适合 | 代价 |
|-----|----------|------------|
| **Drizzle** | 边缘、TypeScript | 较新、示例少 |
| **Prisma** | DX、schema 管理 | 更重、不适边缘 |
| **Kysely** | 类型安全 SQL 构建器 | 手动 migration |
| **Raw SQL** | 复杂查询、控制 | 手动类型安全 |

# Database Selection (2025)

> 基于上下文选数据库，不按默认。

## 决策树

```
What are your requirements?
│
├── Full relational features needed
│   ├── Self-hosted → PostgreSQL
│   └── Serverless → Neon, Supabase
│
├── Edge deployment / Ultra-low latency
│   └── Turso (edge SQLite)
│
├── AI / Vector search
│   └── PostgreSQL + pgvector
│
├── Simple / Embedded / Local
│   └── SQLite
│
└── Global distribution
    └── PlanetScale, CockroachDB, Turso
```

（需完整关系型特性：自托管→PostgreSQL，serverless→Neon/Supabase；边缘部署/超低延迟→Turso；AI/向量检索→PostgreSQL + pgvector；简单/嵌入/本地→SQLite；全球分布→PlanetScale/CockroachDB/Turso。）

## 对比

| 数据库 | 最适合 | 代价 |
|----------|----------|------------|
| **PostgreSQL** | 全功能、复杂查询 | 需要托管 |
| **Neon** | Serverless PG、branching | PG 的复杂度 |
| **Turso** | 边缘、低延迟 | SQLite 的限制 |
| **SQLite** | 简单、嵌入、本地 | 单写者 |
| **PlanetScale** | MySQL、全球规模 | 无外键 |

## 先问这几个问题

1. 部署环境是什么？
2. 查询多复杂？
3. 边缘/serverless 重要吗？
4. 需要向量检索吗？
5. 需要全球分布吗？

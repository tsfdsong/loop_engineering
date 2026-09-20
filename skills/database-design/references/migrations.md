# Migration Principles（迁移原则）

> 零停机变更的安全迁移策略。

## 安全迁移策略

```
For zero-downtime changes:
│
├── Adding column
│   └── Add as nullable → backfill → add NOT NULL
│
├── Removing column
│   └── Stop using → deploy → remove column
│
├── Adding index
│   └── CREATE INDEX CONCURRENTLY (non-blocking)
│
└── Renaming column
    └── Add new → migrate data → deploy → drop old
```

（加列：先 nullable → 回填 → 加 NOT NULL。删列：停用 → 部署 → 删列。加索引：CREATE INDEX CONCURRENTLY（不阻塞）。改名列：加新列 → 迁数据 → 部署 → 删旧列。）

## 迁移哲学

- 永远不一步做破坏性变更
- 先在数据副本上测迁移
- 有回滚预案
- 可能的话在事务中跑

## Serverless 数据库

### Neon（Serverless PostgreSQL）

| 特性 | 收益 |
|---------|---------|
| Scale to zero | 省成本 |
| Instant branching | 开发/预览 |
| 完整 PostgreSQL | 兼容性 |
| 自动扩缩 | 扛流量 |

### Turso（边缘 SQLite）

| 特性 | 收益 |
|---------|---------|
| 边缘节点 | 超低延迟 |
| SQLite 兼容 | 简单 |
| 慷慨免费额度 | 成本 |
| 全球分布 | 性能 |

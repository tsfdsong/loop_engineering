# Query Optimization（查询优化）

> N+1 问题、EXPLAIN ANALYZE、优化优先级。

## N+1 问题

```
What is N+1?
├── 1 query to get parent records
├── N queries to get related records
└── Very slow!

Solutions:
├── JOIN → Single query with all data
├── Eager loading → ORM handles JOIN
├── DataLoader → Batch and cache (GraphQL)
└── Subquery → Fetch related in one query
```

（N+1 = 1 条查父记录 + N 条查关联记录，非常慢。解法：JOIN 单查询全量 / ORM 预加载 / DataLoader 批量缓存（GraphQL）/ 子查询一次取关联。）

## 查询分析心智

```
Before optimizing:
├── EXPLAIN ANALYZE the query
├── Look for Seq Scan (full table scan)
├── Check actual vs estimated rows
└── Identify missing indexes
```

（优化前：EXPLAIN ANALYZE / 找 Seq Scan（全表扫）/ 对比实际与预估行数 / 识别缺失索引。）

## 优化优先级

1. **补缺失索引**（最常见问题）
2. **只选需要的列**（不要 SELECT *）
3. **用恰当的 JOIN**（尽量避免子查询）
4. **尽早 limit**（数据库层分页）
5. **缓存**（适当时）

# Indexing Principles（索引原则）

> 何时建索引、怎么建有效。

## 何时建索引

```
Index these:
├── Columns in WHERE clauses
├── Columns in JOIN conditions
├── Columns in ORDER BY
├── Foreign key columns
└── Unique constraints

Don't over-index:
├── Write-heavy tables (slower inserts)
├── Low-cardinality columns
├── Columns rarely queried
```

（该索引：WHERE 列 / JOIN 列 / ORDER BY 列 / 外键列 / 唯一约束。别过度索引：写密集表（拖慢插入）/ 低基数列 / 极少查询的列。）

## 索引类型选择

| 类型 | 用途 |
|------|---------|
| **B-tree** | 通用，等值与范围 |
| **Hash** | 仅等值，更快 |
| **GIN** | JSONB、数组、全文 |
| **GiST** | 几何、范围类型 |
| **HNSW/IVFFlat** | 向量相似度（pgvector） |

## 复合索引原则

```
Order matters for composite indexes:
├── Equality columns first
├── Range columns last
├── Most selective first
└── Match query pattern
```

（顺序很重要：等值列在前、范围列在后、高选择性优先、匹配查询模式。）

# Schema Design Principles（schema 设计原则）

> 范式化、主键、时间戳、关系。

## 范式化决策

```
When to normalize (separate tables):
├── Data is repeated across rows
├── Updates would need multiple changes
├── Relationships are clear
└── Query patterns benefit

When to denormalize (embed/duplicate):
├── Read performance critical
├── Data rarely changes
├── Always fetched together
└── Simpler queries needed
```

（范式化（拆表）：数据跨行重复 / 更新需多处改 / 关系清晰 / 查询模式受益。反范式化（嵌入/冗余）：读性能关键 / 数据极少变 / 总是一起取 / 需要更简单的查询。）

## 主键选择

| 类型 | 何时用 |
|------|----------|
| **UUID** | 分布式系统、安全 |
| **ULID** | UUID + 按时间可排序 |
| **Auto-increment** | 简单应用、单数据库 |
| **自然键** | 极少（带业务含义） |

## 时间戳策略

```
For every table:
├── created_at → When created
├── updated_at → Last modified
└── deleted_at → Soft delete (if needed)

Use TIMESTAMPTZ (with timezone) not TIMESTAMP
```

（每张表：created_at 创建时间 / updated_at 最后修改 / deleted_at 软删（如需）。用 TIMESTAMPTZ（带时区）不用 TIMESTAMP。）

## 关系类型

| 类型 | 何时 | 实现 |
|------|------|----------------|
| **一对一** | 扩展数据 | 独立表 + FK |
| **一对多** | 父子 | 子表放 FK |
| **多对多** | 双方都有多 | 联结表 |

## 外键 ON DELETE

```
├── CASCADE → Delete children with parent
├── SET NULL → Children become orphans
├── RESTRICT → Prevent delete if children exist
└── SET DEFAULT → Children get default value
```

（CASCADE 级联删子；SET NULL 子成孤儿；RESTRICT 有子禁删；SET DEFAULT 子取默认值。）

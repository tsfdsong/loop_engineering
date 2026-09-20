# CONTEXT.md 格式

## 结构

```md
# {Context Name}

{一两句话描述这个上下文是什么、为什么存在。}

## Language

**Order**:
{一两句话描述该术语}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## 规则

- **要有主见。** 同一概念存在多个词时，选最好的那个，其余列入 `_Avoid_`。
- **定义要紧凑。** 最多一两句。定义它**是**什么，不是它做什么。
- **只收本上下文特有的术语。** 通用编程概念（超时、错误类型、工具模式）不算，哪怕项目大量使用。加词前自问：这是本上下文独有的概念，还是通用编程概念？只有前者该进。
- **自然聚类出现时按子标题分组。** 若所有词属单一内聚领域，平铺即可。

## 单上下文 vs 多上下文仓库

**单上下文（多数仓库）：** repo 根放一个 `CONTEXT.md`。

**多上下文：** repo 根放 `CONTEXT-MAP.md`，列出各上下文、位置、相互关系：

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md): receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md): generates invoices and processes payments
- [Fulfillment](./src/fulfillment/CONTEXT.md): manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing**: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing**: Shared types for `CustomerId` and `Money`
```

技能自动推断适用哪种结构：

- 存在 `CONTEXT-MAP.md` → 读它找各上下文
- 只有根 `CONTEXT.md` → 单上下文
- 都不存在 → 首个术语被解析时惰性创建根 `CONTEXT.md`

多上下文存在时，推断当前话题关联哪个。不清楚就问。

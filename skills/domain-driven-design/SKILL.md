---
name: domain-driven-design
description: DDD 规则集 —— 领域驱动设计。处理复杂业务领域建模、限界上下文、聚合、实体、值对象等。源自 Eric Evans《Domain-Driven Design》。
metadata:
  source: ciembor/agent-rules-books
  book: Domain-Driven Design by Eric Evans
---

# Domain-Driven Design 规则集

当需要对复杂业务领域进行建模、定义限界上下文、设计聚合和实体时使用此技能。

## 使用方式

加载此技能后，**必须**读取并严格遵循以下规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\domain-driven-design\domain-driven-design.mini.md
```

## 规则概览

- 通用语言（Ubiquitous Language）贯穿对话、模型和代码
- 限界上下文（Bounded Context）明确定义模型边界
- 实体由标识定义，值对象由属性定义
- 聚合是一致性边界，通过聚合根访问
- 领域服务处理无自然归属的领域逻辑
- 资源库（Repository）封装持久化，模拟内存集合
- 工厂封装复杂创建逻辑
- 分层架构：接口层、应用层、领域层、基础设施层
- 战略设计指导大尺度结构

**_规则文件是此技能的核心。务必在设计前读取它。_**

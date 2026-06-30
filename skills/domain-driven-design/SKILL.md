---
name: domain-driven-design
description: "Use when modeling complex business domains, designing bounded contexts, aggregates, or applying tactical/strategic DDD patterns. Triggers on DDD, 领域, 限界上下文, 聚合根, domain model. Do NOT use for: pure architecture (use software-architecture), or simple CRUD (no skill needed)."
metadata:
  version: "2.0"
  type: skill
  sources:
    - ciembor/agent-rules-books (3 books)
    - self (1 tactical patterns)
  books:
    - Domain-Driven Design Distilled by Vaughn Vernon
    - Domain-Driven Design by Eric Evans
    - Implementing Domain-Driven Design by Vaughn Vernon
  merged_from:
    - ddd-distilled
    - domain-driven-design
    - implementing-ddd
    - ddd-tactical-patterns
  merge_date: "2026-06-29"
  merge_reason: "4 件套内容高度重叠（4 本 DDD 书），合并减少调度冲突"
---

# Domain-Driven Design 超级技能

当需要 DDD 入门、复杂业务领域建模、限界上下文设计、战术编码（实体/值对象/聚合/资源库/领域事件）、DDD 落地实战时使用此技能。

## 使用方式

加载此技能后，**必须**根据需要读取对应规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\domain-driven-design-distilled\domain-driven-design-distilled.mini.md    # Vernon 入门
C:\Users\admin\.agents\skills\agent-rules-books\domain-driven-design\domain-driven-design.mini.md                       # Evans 原书
C:\Users\admin\.agents\skills\agent-rules-books\implementing-domain-driven-design\implementing-domain-driven-design.mini.md  # Vernon 落地
```

ddd-tactical-patterns（self 源）的内容已直接写入本 SKILL.md（见下方"战术编码规则"章节）。

## 来源与定位

| 部分 | 来源 | 用途 |
|------|------|------|
| **ddd-distilled**（Vernon 入门） | Vernon《DDD Distilled》 | DDD 快速入门、事件风暴、聚合设计原则 |
| **domain-driven-design**（Evans 原书） | Eric Evans《DDD》 | 复杂业务领域建模、限界上下文、聚合、实体、值对象 |
| **ddd-tactical-patterns**（self 战术） | self | 战术编码模式（实体/值对象/聚合/资源库/领域事件） |
| **implementing-ddd**（Vernon 落地） | Vernon《Implementing DDD》 | DDD 落地实战、事件溯源、CQRS、Saga |

## 触发关键词（合并后）

DDD、领域驱动、限界上下文、聚合、实体、值对象、聚合根、通用语言、领域服务、资源库、领域事件、事件风暴、事件溯源、CQRS、Saga、战术模式、入门、原书、落地

## 规则概览

### 来自 ddd-distilled（Vernon 入门）

- DDD 核心概念精要
- 限界上下文与子域
- 事件风暴（Event Storming）
- 聚合设计原则
- 领域事件

### 来自 domain-driven-design（Evans 原书）

- 通用语言（Ubiquitous Language）贯穿对话、模型和代码
- 限界上下文（Bounded Context）明确定义模型边界
- 实体由标识定义，值对象由属性定义
- 聚合是一致性边界，通过聚合根访问
- 领域服务处理无自然归属的领域逻辑
- 资源库（Repository）封装持久化，模拟内存集合
- 工厂封装复杂创建逻辑
- 分层架构：接口层、应用层、领域层、基础设施层
- 战略设计指导大尺度结构

### 来自 ddd-tactical-patterns（self 战术 · 已内联）

**适用场景**：
- 将领域规则转化为代码结构
- 设计聚合边界与不变式
- 把贫血模型重构为富含行为的领域对象
- 定义资源库契约与领域事件边界

**不适用场景**：
- 仍在定义战略边界
- 任务仅为 API 文档或 UI 布局
- 不需要 DDD 全复杂度

**Instructions（步骤式指令）**：
1. 先识别不变式，再围绕不变式设计聚合
2. 为已校验概念建模为不可变值对象
3. 领域行为保留在领域对象内，不放在控制器
4. 为有意义的状态转换发布领域事件
5. 资源库保持在聚合根边界

**示例**：
```typescript
class Order {
  private status: "draft" | "submitted" = "draft";

  submit(itemsCount: number): void {
    if (itemsCount === 0) throw new Error("Order cannot be submitted empty");
    if (this.status !== "draft") throw new Error("Order already submitted");
    this.status = "submitted";
  }
}
```

**局限性**：
- 不定义部署架构
- 不选择数据库或传输协议
- 应与 testing-patterns 配合以覆盖不变式

### 来自 implementing-ddd（Vernon 落地）

- 领域模型实现模式
- 聚合与并发
- 领域事件实现
- 事件溯源与 CQRS
- Saga 与流程管理
- 资源库实现
- 集成限界上下文

## 选择哪个源？

> **使用顺序建议**：首次接触 DDD → 入门（ddd-distilled）→ 战略/建模（Evans）→ 战术编码（self）→ 落地实战（Vernon）。
> ⚠️ **不要一上来就读"落地实战"**——会被劝退。落地实战假设你已经掌握前 3 个源的基础。

| 场景 | 推荐源 |
|------|--------|
| **首次接触 DDD / 概念入门** | ddd-distilled（Vernon 入门） |
| **复杂业务建模 / 战略设计** | domain-driven-design（Evans 原书） |
| **代码层战术编码** | ddd-tactical-patterns（self） |
| **DDD 落地 / 实战 / 高级模式** | implementing-ddd（Vernon 落地） |

---

## 迁移说明

- v6.1.1 合并前：ddd-distilled + domain-driven-design + ddd-tactical-patterns + implementing-ddd 四个独立技能
- v6.1.1 合并后：domain-driven-design 一个超级技能（含 3 个 ciembor 规则文件引用 + self 战术内容内联）
- orch 调度表已同步：ddd-distilled / ddd-tactical-patterns / implementing-ddd 行已移除
- 黄金轨迹：v54-baseline 中"ddd-distilled"等关键词已映射到 domain-driven-design
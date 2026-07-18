---
name: software-architecture
description: "Use when designing system architecture, choosing patterns (MVC, microservices, event-driven), or making distributed systems decisions (replication, partitioning, consistency). Triggers on 架构, 分层, 企业模式, 分布式, 微服务, architecture, distributed. Do NOT use for: DDD modeling (use domain-driven-design), or code quality (use clean-code)."
metadata:
  version: "2.1"
  type: skill
  sources:
    - ciembor/agent-rules-books (clean-architecture)
    - ciembor/agent-rules-books (poeaa)
    - ciembor/agent-rules-books (designing-data-intensive-apps)
  merged_from:
    - clean-architecture
    - poeaa
    - designing-data-intensive-apps
  merge_date: "2026-06-29"
  merge_date_v2_1: "2026-06-30"  # v6.4 重组为递进结构
  merge_reason: |
    v6.2 合并 → 三本各讲不同范畴的书被简单堆叠；v6.4 重组为"从单进程到分布式"的递进结构，
    明确每本书在架构演进路径中的位置。
  architecture_progression:
    - 单进程分层 (Clean Architecture)
    - 企业应用模式 (POEAA)
    - 分布式系统 (DDIA)
---

# Software Architecture 超级技能

## 核心定位：三层递进路径

软件架构不是"选一本书"，而是随系统规模演进的**三层递进**：

```
┌─────────────────────────────────────────────────────┐
│ Layer 3 · 分布式系统（DDIA · Kleppmann）            │
│   多服务 / 跨机房 / 数据复制 / 一致性 / 共识          │
│   ↑ 业务增长倒逼扩展时进入本层                        │
├─────────────────────────────────────────────────────┤
│ Layer 2 · 企业应用模式（POEAA · Fowler）             │
│   业务逻辑组织 / 数据源 / ORM / Web 表示              │
│   ↑ 单体应用规模扩大时进入本层                        │
├─────────────────────────────────────────────────────┤
│ Layer 1 · 单进程分层（Clean Arch · Martin）          │
│   业务边界 / 依赖方向 / 可测试性                      │
│   ↑ 新项目起点                                        │
└─────────────────────────────────────────────────────┘
```

**何时进入下一层**：
- Layer 1 → Layer 2：业务代码 > 5K 行 / 多人协作 / 多种数据源
- Layer 2 → Layer 3：单机容量成为瓶颈 / 跨地域需求 / SLA 要求 99.99%+

**何时不该跳过**：
- ❌ 新项目上来就 Layer 3（分布式）：增加 10 倍复杂度，性能更差
- ❌ 单体小项目套 Layer 2 全部模式：过度设计

---

## Layer 1 · 单进程分层（Clean Architecture · Robert C. Martin）

> **适用**：新项目起点 / 单体应用 / 团队 < 10 人 / 业务 < 50 个核心用例

### 核心原则

- **依赖方向**：外层依赖内层，反之不可
  - 内层 = 业务规则（不知道外层存在）
  - 外层 = 框架/数据库/UI/外部服务
- **边界**：业务规则与技术细节严格分离
- **稳定抽象**：抽象比实现稳定（业务接口定义后，框架可以换）

### 四层结构

```
┌─────────────────────────────────┐
│ Frameworks & Drivers（外）       │  ← Web / DB / UI / 外部 API
├─────────────────────────────────┤
│ Interface Adapters              │  ← Controller / Presenter / Gateway
├─────────────────────────────────┤
│ Use Cases（应用业务规则）        │  ← 应用服务 / 编排
├─────────────────────────────────┤
│ Entities（企业业务规则 · 最内）  │  ← 业务实体 / 领域规则
└─────────────────────────────────┘
```

### 关键模式

- **依赖倒置**（DIP）：高层不依赖低层，都依赖抽象（接口）
- **接口适配**：翻译层处理技术细节（DTO ↔ 实体）
- **框架独立**：业务不绑定具体框架（Spring / Django / FastAPI 都能用）
- **可测试**：业务规则不依赖数据库 / HTTP，能纯内存测试

### Layer 1 决策清单

- [ ] 业务规则是否与技术细节分离？
- [ ] 依赖方向是否单向（外 → 内）？
- [ ] 业务代码能否脱离框架单测？
- [ ] 是否有"上帝类"或"上帝模块"？

---

## Layer 2 · 企业应用模式（POEAA · Martin Fowler）

> **适用**：单体规模扩大（业务代码 > 5K 行）/ 多种数据源 / 复杂业务逻辑组织

### 分层架构（POEAA 视角）

```
表示层 → 业务层 → 数据层
  │        │        │
  │        │        └─ 事务脚本 / 领域模型 / 数据映射器
  │        └─ 服务层 / 领域模型
  └─ MVC / Page Controller / Front Controller
```

每层通过接口通信，业务逻辑封装在领域模型。

### 23 种核心模式（按类别）

#### 领域逻辑组织

| 模式 | 适用 | 不适用 |
|------|------|-------|
| **事务脚本** | 简单业务（CRUD） | 复杂业务规则 |
| **表数据入口** | 简单数据访问 | 复杂领域模型 |
| **领域模型** | 复杂业务 | 简单 CRUD |
| **服务层** | 跨聚合用例 | 单一实体操作 |

#### 数据源架构

| 模式 | 适用 |
|------|------|
| **表数据网关** | 单表访问 |
| **行数据网关** | 单行对象访问 |
| **Active Record** | 简单领域 + 单数据源（典型：Rails/Django ORM） |
| **数据映射器** | 复杂领域，独立于数据库（典型：Hibernate/SQLAlchemy） |

#### 对象-关系行为（ORM 行为）

- **工作单元（Unit of Work）**：跟踪变化，事务提交时统一写入
- **标识映射（Identity Map）**：保证同一对象在事务内只加载一次
- **延迟加载（Lazy Load）**：按需加载关联
- **查询对象（Query Object）**：封装 SQL 动态构建

#### 对象-关系结构

- **单表继承** / **类表继承** / **具体表继承**

#### Web 表示

- **MVC** / **Page Controller** / **Front Controller**
- **Template View** / **Transform View**

#### 离线并发

- **乐观锁**（版本号） / **悲观锁**（行锁）

### Layer 2 决策清单

- [ ] 领域逻辑用事务脚本还是领域模型？
- [ ] ORM 用 Active Record 还是数据映射器？
- [ ] 是否需要服务层？（业务用例 > 5 个聚合）
- [ ] 工作单元是否启用？（多对象写入）

---

## Layer 3 · 分布式系统（DDIA · Martin Kleppmann）

> **适用**：单机容量瓶颈 / 跨地域需求 / SLA 99.99%+ / 千万级用户

### 六大主题

| 主题 | 范围 | 关键问题 |
|------|------|---------|
| **第 1 章** | 可靠性 / 可扩展性 / 可维护性 | 系统目标如何定义？ |
| **第 2-3 章** | 数据模型与查询语言 | 关系 / 文档 / 图 如何选？ |
| **第 4-5 章** | 存储与检索 | LSM 树 / B 树 / 列式存储？ |
| **第 6 章** | 编码与演化 | 前向/后向兼容性？ |
| **第 7-9 章** | 分布式数据 | 复制 / 分区 / 事务 / 一致性 / 共识 |
| **第 10-12 章** | 派生数据 | 批处理 / 流处理 / 数据集成 |

### 关键概念

#### 复制

| 模式 | 写 | 读延迟 | 故障时 |
|------|-----|--------|--------|
| **单 leader** | 1 节点 | 异步副本可能落后 | 副本可服务读 |
| **多 leader** | 多节点 | 低 | 冲突需解决 |
| **无 leader**（dynamo） | 任意 | 最低 | 读修复 |

#### 分区

- **一致性哈希** / **范围分区**（key 顺序）
- **分区再平衡**：固定 / 一致性哈希 / 比例

#### 事务

- **ACID**：原子 / 一致 / 隔离 / 持久
- **BASE**：基本可用 / 软状态 / 最终一致
- **隔离级别**：读未提交 / 读已提交 / 可重复读 / 串行化

#### 一致性

- **线性一致性**：最强，所有操作全局有序
- **因果一致性**：保持因果，偏序
- **最终一致性**：仅保证收敛

#### 共识

- **Paxos** / **Raft** / **ZAB**（ZooKeeper）

### Layer 3 决策清单

- [ ] 数据需要分区吗？（数据 > 单机容量）
- [ ] 复制模式：单 leader / 多 leader / 无 leader？
- [ ] 一致性要求：强一致 / 最终一致？
- [ ] 共识算法选型？etcd / ZooKeeper？
- [ ] 故障切换策略：自动 / 手动？
- [ ] 跨机房延迟容忍度？

---

## 跨层组合（企业实战）

| 场景 | Layer 1 | Layer 2 | Layer 3 |
|------|:---:|:---:|:---:|
| **新项目起点** | ✅ | ❌ | ❌ |
| **单体应用** | ✅ | ✅ | ❌ |
| **微服务架构** | ✅（每服务） | ✅（每服务） | ✅（服务间） |
| **跨国 SaaS** | ✅ | ✅ | ✅ |

---

## 整合使用流程

### 场景 1 · 新系统设计

```
Step 1: 评估规模
  - 业务 < 50 用例 / < 5K 行 / 团队 < 10 人 → Layer 1
  - 业务 > 50 用例 / 多种数据源 / 跨团队 → Layer 1 + 2
  - 跨地域 / 高 SLA / 千万级用户 → Layer 1 + 2 + 3

Step 2: Layer 1 应用（Clean Arch）
  - 定义 Entities（业务实体 + 核心规则）
  - 定义 Use Cases（应用服务 / 编排）
  - 实现 Interface Adapters（Controller / Presenter / Gateway）
  - 选择 Frameworks（Web 框架 / DB / 外部服务）

Step 3: Layer 2 应用（POEAA · 仅规模需要时）
  - 选领域逻辑模式（事务脚本 vs 领域模型）
  - 选 ORM（Active Record vs Data Mapper）
  - 启用工作单元 + 标识映射
  - 服务层 / 仓储 / 工厂

Step 4: Layer 3 应用（DDIA · 仅分布式需要时）
  - 数据分区（按用户 / 按地域 / 按业务）
  - 复制策略（单 leader / 多 leader）
  - 一致性级别（业务驱动选择）
  - 共识与故障切换

Step 5: 验证可扩展性 / 可靠性
  - 压测（目标 QPS / p99 延迟）
  - 故障演练（单节点宕机 / 网络分区）
  - 容量规划（数据增长 / 流量增长）
```

### 场景 2 · 单体转微服务

```
Step 1: Layer 2 摸底
  - 识别聚合根（领域边界）
  - 识别跨聚合用例（决定服务边界）
Step 2: 服务拆分
  - 按业务能力拆（订单 / 用户 / 商品）
  - 按团队拆（康威定律）
Step 3: Layer 3 引入
  - 服务注册发现
  - API 网关
  - 分布式事务（Saga / 事件溯源）
  - 链路追踪
```

---

## 与其他技能配合

| 场景 | 配合技能 |
|------|---------|
| 业务领域建模 | `domain-driven-design`（Layer 1 的领域层深化） |
| 实施单体 API | `python-web-development`（Layer 1+2 的 API 落地） |
| 业务规则验证 | `testing`（业务不变式测试） |
| 架构决策记录 | `writing-plans` / `system-review`（ADR 模板） |
| 重构单体 | `refactoring`（Layer 1 → Layer 2 演进） |

---

## 限制

- **不替代实际测量** — 分布式是否必要由容量数据决定，不是理论推演
- **不替代业务判断** — 一致性级别由业务容忍度决定
- **不替代 DDD 深入** — 复杂业务需配合 domain-driven-design
- **完整内容在原书** — 本 SKILL.md 给出框架，详细模式查原书
- **架构决策应记录 ADR** — 重要选择（单 leader / 事务策略）必有 ADR

---

## 迁移说明

- v6.2 合并前：clean-architecture + poeaa + ddia 三个独立技能
- v6.2 合并后：software-architecture 一个超级技能（三本原文堆叠）
- **v6.4 重组**：从堆叠 → 三层递进结构（单进程 → 企业模式 → 分布式）
- 修死引用：v6.2 时该 references 文件已不存在（v6.2 仅删 SKILL.md 未删 references）→ v6.4 已改为内联要点
- 内联：poeaa + ddia 完整内容（30+30 行）已融入 Layer 2/3 章节
- orch 调度表已同步

---

## 论源（v1.0.4 工程实践红线对接）

本技能作为以下工程实践红线的**方法论支撑**（单点真源引用，AGENTS.md §9）：

- **R1.4 可回滚红线** — 提供"架构决策必须可回滚"的方法论（DDIA Chapter 4 编码 + 回滚 / POEAA 演进式设计）
- **R2.4 PoC / Spike 时间盒** — 提供"重大选型必须 spike 验证 + 时间盒"的具体技术（Clean Architecture 边界识别 + spike-and-stabilize 流程）
- **R6.2 ADR 红线** — 提供 ADR（Architecture Decision Record）的标准结构与编写流程（Michael Nygard ADR 模板 + 演进路径）

> **红线触发场景**：任何 AI 做技术选型 / 架构决策 / 不可逆设计时，必须遵循 R1.4 + R2.4 + R6.2；本技能提供方法论落地路径。
> **同步版本**：AGENTS.md v1.0.4（2026-07-03）

---

## §M. Domain-Driven Design 战术建模（吸收原 domain-driven-design · v2.0 合并 · D2.0）

> **来源**：`ciembor/agent-rules-books`（3 本 DDD 书）+ self（1 战术 patterns）· D2.0 合并于此。
> **合并自**：ddd-distilled / domain-driven-design / implementing-ddd / ddd-tactical-patterns（v6.1.1 已先行合并为单 skill，D2.0 再并入 software-architecture）。
> **使用场景**：复杂业务领域建模、限界上下文设计、战术编码（实体/值对象/聚合/资源库/领域事件）、DDD 落地实战。

### DDD 核心定位（在三层架构中的位置）

DDD 是 Layer 1（Clean Arch）领域层的深化方法。当业务规则复杂到事务脚本（POEAA）无法承载时，用 DDD 战术模式（实体/值对象/聚合/资源库/领域事件）组织领域层。简单 CRUD 不需要 DDD。

### 来源与定位

| 部分 | 来源 | 用途 |
|------|------|------|
| **ddd-distilled**（Vernon 入门） | Vernon《DDD Distilled》 | DDD 快速入门、事件风暴、聚合设计原则 |
| **domain-driven-design**（Evans 原书） | Eric Evans《DDD》 | 复杂业务领域建模、限界上下文、聚合、实体、值对象 |
| **ddd-tactical-patterns**（self 战术） | self | 战术编码模式（实体/值对象/聚合/资源库/领域事件） |
| **implementing-ddd**（Vernon 落地） | Vernon《Implementing DDD》 | DDD 落地实战、事件溯源、CQRS、Saga |

### 触发关键词

DDD、领域驱动、限界上下文、聚合、实体、值对象、聚合根、通用语言、领域服务、资源库、领域事件、事件风暴、事件溯源、CQRS、Saga、战术模式

### 规则概览

#### 来自 ddd-distilled（Vernon 入门）

- DDD 核心概念精要
- 限界上下文与子域
- 事件风暴（Event Storming）
- 聚合设计原则
- 领域事件

#### 来自 domain-driven-design（Evans 原书）

- **通用语言（Ubiquitous Language）** 贯穿对话、模型和代码
- **限界上下文（Bounded Context）** 明确定义模型边界
- 实体由标识定义，值对象由属性定义
- 聚合是一致性边界，通过聚合根访问
- 领域服务处理无自然归属的领域逻辑
- **资源库（Repository）** 封装持久化，模拟内存集合
- 工厂封装复杂创建逻辑
- 分层架构：接口层、应用层、领域层、基础设施层
- 战略设计指导大尺度结构

#### 来自 ddd-tactical-patterns（self 战术 · 已内联）

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
- 应与 testing 配合以覆盖不变式

#### 来自 implementing-ddd（Vernon 落地）

- 领域模型实现模式
- 聚合与并发
- 领域事件实现
- 事件溯源与 CQRS
- Saga 与流程管理
- 资源库实现
- 集成限界上下文

### 选择哪个源？

> **使用顺序建议**：首次接触 DDD → 入门（ddd-distilled）→ 战略/建模（Evans）→ 战术编码（self）→ 落地实战（Vernon）。
> ⚠️ **不要一上来就读"落地实战"** —— 会被劝退。落地实战假设你已经掌握前 3 个源的基础。

| 场景 | 推荐源 |
|------|--------|
| **首次接触 DDD / 概念入门** | ddd-distilled（Vernon 入门） |
| **复杂业务建模 / 战略设计** | domain-driven-design（Evans 原书） |
| **代码层战术编码** | ddd-tactical-patterns（self） |
| **DDD 落地 / 实战 / 高级模式** | implementing-ddd（Vernon 落地） |

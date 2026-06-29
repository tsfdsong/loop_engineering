---
name: software-architecture
description: "软件架构超级技能 —— Clean Architecture + 企业应用模式（POEAA）+ 数据密集系统设计（DDIA）三合一。涵盖分层架构、领域模式、分布式系统、数据一致性。"
metadata:
  version: "2.0"
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
  merge_reason: "3 个架构设计技能整合为单一入口"
---

# Software Architecture 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

整合 3 个架构设计技能：
- **clean-architecture**（ciembor）—— Clean Architecture 分层（Robert C. Martin）
- **poeaa**（ciembor）—— 企业应用模式（Fowler）
- **designing-data-intensive-apps**（ciembor）—— 数据密集系统（Kleppmann）

## 触发关键词（合并后）

分层、依赖方向、边界、组件划分、企业架构、ORM、MVC、数据源模式、分布式、复制、分区、一致性、流处理

## 使用方式

| 任务 | 读哪一章 |
|------|---------|
| 系统分层设计 | Clean Architecture |
| 企业应用模式 | POEAA 23 种模式 |
| 分布式系统设计 | DDIA |
| 数据一致性 | DDIA 第 5/7/9 章 |
| 微服务架构 | POEAA + DDIA |

## Clean Architecture（ciembor · 32 行）

### 核心原则

- **依赖方向**：外层依赖内层，反之不可
- **边界**：业务规则与技术细节分离
- **分层**：Entities → Use Cases → Interface Adapters → Frameworks
- **稳定抽象**：抽象比实现稳定

### 关键模式

- **依赖倒置**：高层不依赖低层，都依赖抽象
- **接口适配**：翻译层处理技术细节
- **框架独立**：业务不绑定具体框架

> 完整 32 行内容：[references/clean-architecture-full.md](references/clean-architecture-full.md)

## 企业应用模式 POEAA（Fowler · 32 行）

### 分层架构

- 表示层 → 业务层 → 数据层
- 每层通过接口通信
- 业务逻辑封装在领域模型

### 23 种模式分类

| 类别 | 模式 |
|------|------|
| **领域逻辑** | 事务脚本、表数据入口、领域模型、服务层 |
| **数据源** | 表数据网关、行数据网关、Active Record、数据映射器 |
| **对象-关系** | 标识映射、单元工作、延迟加载、查询对象 |
| **Web 表示** | MVC、Page Controller、Front Controller、Template View、Transform View |
| **分布** | 远程外观、数据传输对象 |

> 完整 32 行内容：[references/poeaa-full.md](references/poeaa-full.md)

## 数据密集系统 DDIA（Kleppmann · 33 行）

### 三大主题

1. **可靠性、可扩展性、可维护性**（第 1 章）
2. **数据模型与查询语言**（第 2-3 章）
3. **存储与检索**（第 4-5 章）
4. **编码与演化**（第 6 章）
5. **分布式数据**（第 7-9 章）
6. **派生数据**（第 10-12 章）

### 关键概念

- **复制**：单 leader、多 leader、无 leader
- **分区**：一致性哈希、范围分区
- **事务**：ACID、BASE、隔离级别
- **一致性**：线性一致性、因果一致性、最终一致性
- **共识**：Paxos、Raft、ZAB

> 完整 33 行内容：[references/ddia-full.md](references/ddia-full.md)

## 整合使用流程

```
新系统设计
├─ 步骤 1: Clean Architecture 分层（业务边界）
├─ 步骤 2: POEAA 业务逻辑模式（领域模型/服务层）
├─ 步骤 3: POEAA 数据源模式（ORM/数据映射）
├─ 步骤 4: DDIA 数据模型（关系/NoSQL/文档）
├─ 步骤 5: DDIA 分布式（复制/分区/一致性）
└─ 步骤 6: 验证可扩展性/可靠性
```

## Resources

- `references/clean-architecture-full.md`（来自 clean-architecture）—— 完整 32 行
- `references/poeaa-full.md`（来自 poeaa）—— 完整 32 行
- `references/ddia-full.md`（来自 designing-data-intensive-apps）—— 完整 33 行

## 限制

- 完整内容在 references/，按需查阅
- 架构决策应记录 ADR（架构决策记录）

---

## 迁移说明

- v6.2 合并前：clean-architecture + poeaa + designing-data-intensive-apps 三个独立技能
- v6.2 合并后：software-architecture 一个超级技能
---
name: production-readiness
description: "生产就绪超级技能 —— 生产级代码审计 + 发布稳定设计（Release It!）二合一。涵盖代码质量审计、生产稳定性模式、发布策略、容错设计。"
metadata:
  version: "2.0"
  type: skill
  sources:
    - community (production-code-audit)
    - ciembor/agent-rules-books (release-it)
  merged_from:
    - production-code-audit
    - release-it
  merge_date: "2026-06-29"
  merge_reason: "2 个生产就绪技能（审计 + 稳定设计）整合为单一入口"
---

# Production Readiness 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

整合 2 个生产就绪技能：
- **production-code-audit**（community）—— 全代码库生产级质量审计
- **release-it**（ciembor）—— 生产稳定性与发布设计（《Release It!》）

## 触发关键词（合并后）

上线前检查、生产审计、生产级、发布、上线、稳定性、故障、断路器、超时、重试、限流、降级、监控、SLA、容量

## 使用方式

| 任务 | 读哪一章 |
|------|---------|
| 上线前全面审计 | production-code-audit |
| 设计发布策略 | release-it 蓝绿/金丝雀 |
| 处理稳定性反模式 | release-it 集成点/连锁反应 |
| 评估 SLA 与监控 | release-it 运维透明性 |

## 生产级代码审计（production-code-audit · community · 548 行）

### 核心能力

- **深度扫描**：逐行理解代码库架构与模式
- **系统化转换**：转化为生产级、企业级专业质量
- **优化建议**：性能、可维护性、安全性

### 审计范围

| 维度 | 检查项 |
|------|--------|
| **代码质量** | 命名、注释、复杂度、重复 |
| **架构** | 分层、依赖、耦合度 |
| **性能** | 瓶颈、N+1、内存 |
| **安全** | 注入、密钥、权限 |
| **可观测性** | 日志、指标、追踪 |
| **可维护性** | 测试覆盖、文档 |

> 完整 548 行内容：[references/production-code-audit-full.md](references/production-code-audit-full.md)

## 生产稳定性（release-it · Michael Nygard · 30 行）

### 稳定性反模式（避免）

- **集成点**：跨网络/跨进程的脆弱边界
- **连锁反应**：一个故障扩散全系统
- **级联故障**：超时未设置 → 资源耗尽
- **慢响应**：拖死线程池

### 稳定性模式（采用）

- **超时**：所有外部调用必须设超时
- **断路器**：失败率超阈值时短路
- **隔舱**：限制故障爆炸半径
- **稳态处理**：避免资源累积
- **快速失败**：不要无限重试

### 发布模式

- **蓝绿部署**：新旧版本同时运行，瞬时切换
- **金丝雀发布**：小比例流量验证新版本
- **滚动发布**：分批替换实例

### 容量规划

- 容量测试：在生产规模下验证
- SLA 定义：99.9% / 99.99% 量化目标
- 监控告警：黄金指标（延迟/流量/错误/饱和）

> 完整 30 行内容：[references/release-it-full.md](references/release-it-full.md)

## 整合使用流程

```
上线前审计
├─ 步骤 1: production-code-audit 全代码库审计
├─ 步骤 2: 修复 Critical 问题
├─ 步骤 3: 修复 Important 问题
├─ 步骤 4: 应用 release-it 稳定性模式
├─ 步骤 5: 容量测试 + SLA 验证
└─ 步骤 6: 蓝绿/金丝雀发布

故障处理
├─ 步骤 1: 识别连锁反应源
├─ 步骤 2: 添加超时
├─ 步骤 3: 部署断路器
├─ 步骤 4: 设置隔舱
└─ 步骤 5: 监控 + 告警
```

## Resources

- `references/production-code-audit-full.md`（来自 production-code-audit）—— 完整 548 行
- `references/release-it-full.md`（来自 release-it）—— 完整 30 行

## 限制

- 完整审计需大量上下文，建议分模块进行
- 容量测试需生产规模环境
- 完整内容在 references/，按需查阅

---

## 迁移说明

- v6.2 合并前：production-code-audit + release-it 两个独立技能
- v6.2 合并后：production-readiness 一个超级技能
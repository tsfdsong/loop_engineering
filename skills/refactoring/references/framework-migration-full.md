# Legacy Code Modernization Workflow（遗留代码现代化工作流）

用绞杀者模式（strangler fig pattern）编排全面的遗留系统现代化，在维持业务连续运行的前提下，通过专家 agent 协调逐步替换过时组件。

[扩展思考：绞杀者模式得名于逐渐包裹并取代宿主的热带榕树，是风险受控的遗留现代化黄金标准。本工作流实现系统化路径——新功能逐步替换遗留组件，两套系统在过渡期共存。通过编排评估、测试、安全、实施等专职 agent，确保每个迁移阶段先验证再推进，在最大化现代化速度的同时最小化扰动。]

## 何时使用

- 处理遗留代码现代化工作流任务
- 需要遗留现代化的指引、最佳实践或检查清单

## Phase 1: 遗留评估与风险分析

### 1. 全面遗留系统分析
- 用 Task tool，subagent_type="legacy-modernizer"
- Prompt："分析 $ARGUMENTS 处的遗留代码库。产出技术债清单：过时依赖、废弃 API、安全漏洞、性能瓶颈、架构反模式。生成现代化就绪报告，含组件复杂度评分（1-10）、依赖映射、数据库耦合分析。区分快赢目标与复杂重构目标。"
- 预期产出：含风险矩阵与现代化优先级的详细评估报告

### 2. 依赖与集成映射
- 用 Task tool，subagent_type="architect-review"
- Prompt："基于遗留评估报告，建全面依赖图：内部模块依赖、外部服务集成、共享数据库 schema、跨系统数据流。识别迁移中需要 facade 模式或适配层的集成点。标出需解决的循环依赖与紧耦合。"
- 上文上下文：遗留评估报告、组件复杂度评分
- 预期产出：可视化依赖图 + 集成点目录

### 3. 业务影响与风险评估
- 用 Task tool，subagent_type="business-analytics::business-analyst"
- Prompt："评估现代化各已识别组件的业务影响。建风险评估矩阵，考量：业务关键度（营收影响）、用户流量模式、数据敏感度、合规要求、回退复杂度。用加权评分排序：(业务价值 × 0.4) + (技术风险 × 0.3) + (快赢潜力 × 0.3)。为每个组件定义回滚策略。"
- 上文上下文：组件清单、依赖映射
- 预期产出：带风险缓解策略的优先级迁移路线图

## Phase 2: 测试覆盖建立

### 1. 遗留代码测试覆盖分析
- 用 Task tool，subagent_type="unit-testing::test-automator"
- Prompt："分析 $ARGUMENTS 遗留组件的既有测试覆盖。用覆盖率工具找出未测代码路径、缺失的集成测试、缺席的端到端场景。对覆盖 <40% 的组件生成特征测试（characterization tests），记录当前行为而不改功能。为安全重构建测试 harness。"
- 预期产出：覆盖率报告 + 特征测试套件

### 2. 契约测试实施
- 用 Task tool，subagent_type="unit-testing::test-automator"
- Prompt："为依赖映射中识别的全部集成点实现契约测试。为 API、消息队列交互、数据库 schema 建消费者驱动契约。在 CI/CD 流水线中设置契约校验。生成响应时间与吞吐的性能基线，用于验证现代化组件守住 SLA。"
- 上文上下文：集成点目录、既有测试覆盖
- 预期产出：契约测试套件 + 性能基线

### 3. 测试数据管理策略
- 用 Task tool，subagent_type="data-engineering::data-engineer"
- Prompt："为双系统并行运行设计测试数据管理策略。建边界情况数据生成脚本、敏感信息脱敏、测试库刷新流程。为迁移期间新旧组件间的数据一致性设置监控。"
- 上文上下文：数据库 schema、测试需求
- 预期产出：测试数据管道 + 一致性监控

## Phase 3: 增量迁移实施

### 1. 绞杀者基础设施搭建
- 用 Task tool，subagent_type="backend-development::backend-architect"
- Prompt："实现带 API 网关流量路由的绞杀者基础设施。配置 feature flag 做渐进放量（环境变量或 feature 管理服务）。搭代理层，按 URL 模式 / header / 用户分段的规则路由请求。实现熔断与回退机制保证韧性。建双系统可观测性仪表盘。"
- 预期产出：API 网关配置、feature flag 系统、监控仪表盘

### 2. 组件现代化 —— 第一波
- 用 Task tool，subagent_type="python-development::python-pro" 或 "golang-pro"（按目标栈）
- Prompt："现代化第一波组件（评估中识别的快赢项）。每个组件：从遗留代码剥离业务逻辑，用现代模式实现（依赖注入、SOLID），经适配器模式保向后兼容，用事件溯源或双写保数据一致。遵循 12-factor 原则。待现代化组件：[来自优先级路线图]"
- 上文上下文：特征测试、契约测试、基础设施
- 预期产出：带适配器的现代化组件

### 3. 安全加固
- 用 Task tool，subagent_type="security-scanning::security-auditor"
- Prompt："审计现代化组件的安全漏洞。实施安全改进：OAuth 2.0/JWT 认证、RBAC、输入校验与净化、SQL 注入防护、XSS 防护、secrets 管理。验证 OWASP top 10 合规。配置安全 header 与限流。"
- 上文上下文：现代化组件代码
- 预期产出：安全审计报告 + 加固后组件

## Phase 4: 性能验证与优化

### 1. 性能测试与优化
- 用 Task tool，subagent_type="application-performance::performance-engineer"
- Prompt："对比测试遗留 vs 现代化组件性能。按生产流量模式做负载测试，测响应时间、吞吐、资源占用。识别性能回归并优化：索引数据库查询、缓存策略（Redis/Memcached）、连接池、适用的异步处理。对照 SLA 验证。"
- 上文上下文：性能基线、现代化组件
- 预期产出：性能测试结果 + 优化建议

### 2. 渐进放量与监控
- 用 Task tool，subagent_type="deployment-strategies::deployment-engineer"
- Prompt："用 feature flag 实现渐进放量。先 5% 流量到现代化组件，监控错误率、延迟、业务指标。定义自动回滚触发：错误率 >1%、延迟 >2x 基线、业务指标劣化。建切流 runbook：5% → 25% → 50% → 100%，每档观察 24 小时。"
- 上文上下文：feature flag 配置、监控仪表盘
- 预期产出：带自动保险的放量计划

## Phase 5: 迁移收尾与文档

### 1. 遗留组件退役
- 用 Task tool，subagent_type="legacy-modernizer"
- Prompt："规划被替换遗留组件的安全退役。经流量分析确认无剩余依赖（0% 流量持续至少 30 天）。归档遗留代码并记录原始功能。更新 CI/CD 流水线移除遗留构建。清理无用数据库表、移除废弃 API 端点。为保留的遗留组件记录 sunset 时间表。"
- 上文上下文：流量路由数据、现代化状态
- 预期产出：退役清单与时间表

### 2. 文档与知识转移
- 用 Task tool，subagent_type="documentation-generation::docs-architect"
- Prompt："编写全面的现代化文档：架构图（前后对照）、带迁移指引的 API 文档、双系统运行 runbook、常见问题排障指南、经验教训报告。为现代化系统生成开发者 onboarding 指南。记录迁移中的技术决策与 trade-off。"
- 上文上下文：全部迁移工件与决策
- 预期产出：完整现代化文档包

## 配置选项

- **--parallel-systems**：双系统长期并行（渐进迁移）
- **--big-bang**：验证后整体切换（风险高、完成快）
- **--by-feature**：按完整功能而非技术组件迁移
- **--database-first**：数据库先于应用层现代化
- **--api-first**：先现代化 API 层、保留遗留后端

## 成功标准

- 全部高优先级组件现代化，测试覆盖 >80%
- 迁移期间零计划外停机
- 性能指标持平或改善（P95 延迟在基线 110% 以内）
- 安全漏洞减少 >90%
- 技术债评分改善 >60%
- 迁移后连续运行 30 天无回滚
- 文档完整，新开发者 onboarding <1 周

Target: $ARGUMENTS

## 边界

- 仅当任务明确匹配上述范围时使用本技能。
- 不要把输出当作环境特定验证、测试或专家评审的替代品。
- 缺少必需输入、权限、安全边界或成功标准时，停下来问清楚。

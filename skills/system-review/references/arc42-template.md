# ARC42 架构模板（参考）

> 来源: [arc42.org](https://arc42.org/overview)
> 用途: 标准化架构文档与审查框架

---

## 12 章模板

| # | 章节 | 审查什么 |
|---|------|---------|
| 1 | **Introduction & Goals** | 系统的核心质量目标是否明确？干系人期望是否对齐？ |
| 2 | **Constraints** | 技术/组织/法规约束是否被识别和遵守？ |
| 3 | **Context & Scope** | 系统边界是否清晰？外部接口是否完整定义？ |
| 4 | **Solution Strategy** | 核心技术决策是否有记录？决策理由是否充分？ |
| 5 | **Building Block View** | 分层/分模块是否合理？黑盒/白盒关系是否清晰？ |
| 6 | **Runtime View** | 关键场景的运行时交互是否正确？异常路径是否覆盖？ |
| 7 | **Deployment View** | 部署拓扑是否合理？基础设施映射是否正确？ |
| 8 | **Crosscutting Concepts** | 横切关注点（日志/安全/错误处理）是否一致？ |
| 9 | **Architectural Decisions** | 关键决策是否有记录（ADR）？理由是否可追溯？ |
| 10 | **Quality Requirements** | 质量场景是否具体可测？是否覆盖性能/安全/可用性？ |
| 11 | **Risks & Technical Debt** | 已知风险和技术债是否被追踪？是否有缓解计划？ |
| 12 | **Glossary** | 领域术语是否统一定义？是否消除歧义？ |

---

## 与 system-review 三条方法论的映射

| ARC42 章节 | 对应方法论 |
|-----------|-----------|
| 第3章 Context & Scope | → 方法论1: 横向自洽性（边界一致性） |
| 第8章 Crosscutting Concepts | → 方法论1: 横向自洽性（横切一致性） |
| 第1章 Goals + 第5章 Building Block | → 方法论2: 纵向深度（分层合理性） |
| 第9章 Decisions + 第11章 Risks | → 方法论3: 持续改进（决策追溯、风险追踪） |

---

## 使用建议

- **轻量审查**: 只用 system-review 的三条方法论
- **完整审查**: 按 ARC42 的 12 章逐章审查，每条方法论作为对应章节的判据
- **架构文档化**: 用 ARC42 模板为新系统编写架构文档

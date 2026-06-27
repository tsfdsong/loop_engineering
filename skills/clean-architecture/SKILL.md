---
name: clean-architecture
description: Clean Architecture 规则集 —— 架构设计、模块划分、依赖管理时使用。关注分层、边界、依赖规则。源自 Robert C. Martin《Clean Architecture》。
metadata:
  source: ciembor/agent-rules-books
  book: Clean Architecture by Robert C. Martin
---

# Clean Architecture 规则集

当进行架构设计、模块划分、依赖方向管理、边界定义或需要确保系统结构清晰时使用此技能。

## 使用方式

加载此技能后，**必须**读取并严格遵循以下规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\clean-architecture\clean-architecture.mini.md
```

## 规则概览

- 遵守依赖规则：依赖只能指向内层
- 实体封装企业级业务规则
- 用例封装应用特定业务规则
- 接口适配层将外部形式转换为内部用例格式
- 框架和驱动层只放外部工具
- 边界接口由内层定义，外层实现
- 不要在组件边界上共享数据结构
- 架构应该脱离框架交付而可测试

**_规则文件是此技能的核心。务必在设计前读取它。_**

---
name: clean-code
description: Clean Code 规则集 —— 日常编码与代码审查时使用。关注可读性、局部推理、可维护代码形态。源自 Robert C. Martin《Clean Code》。
metadata:
  source: ciembor/agent-rules-books
  book: Clean Code by Robert C. Martin
---

# Clean Code 规则集

当进行日常编码实现、代码审查、重构或需要提升代码可读性和可维护性时使用此技能。

## 使用方式

加载此技能后，**必须**读取并严格遵循以下规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\clean-code\clean-code.mini.md
```

## 规则概览

- 将整洁视为交付的一部分
- 为局部推理而写代码
- 使用精确命名，一个概念一个词
- 函数保持短小、专注、单一抽象层级
- 参数少而有意义；避免布尔标志和输出参数
- 命令与查询分离，消除隐藏副作用
- 清晰路径可读；隔离错误处理
- 暴露行为而非原始表示
- 将构造、框架、持久化等细节排除在业务行为之外
- 公共 API 小而显式，难以误用
- 注释仅用于理由、约束、警告或外部契约
- 测试作为生产代码对待

**_规则文件是此技能的核心。务必在编码前读取它。_**

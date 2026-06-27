---
name: refactoring
description: Refactoring 规则集 —— 重构代码时使用。涵盖代码坏味道识别与消除方法。源自 Martin Fowler《Refactoring》。
metadata:
  source: ciembor/agent-rules-books
  book: Refactoring by Martin Fowler
---

# Refactoring 规则集

当需要重构现有代码、识别和消除代码坏味道、改善代码结构时不改变外部行为时使用此技能。

## 使用方式

加载此技能后，**必须**读取并严格遵循以下规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\refactoring\refactoring.mini.md
```

## 规则概览

- 重构不改变可观察行为
- 小步前进，频繁测试
- 先让代码能工作，再让它变好
- 识别坏味道：长函数、大类、长参数列表、发散式变化、霰弹式修改、依恋情结等
- 使用重构手法：提取函数、内联、移动、封装、引入参数对象等
- 测试是重构的安全网

**_规则文件是此技能的核心。务必在重构前读取它。_**

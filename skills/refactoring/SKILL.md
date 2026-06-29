---
name: refactoring
description: "Refactoring 超级技能 —— 标准重构操作 + Fowler 原书 + refactoring.guru 速查三合一。涵盖代码坏味道识别、重构手法、改善结构、设计模式应用场景。源自 Martin Fowler《Refactoring》+ refactoring.guru。"
metadata:
  version: "2.0"
  type: skill
  source: ciembor/agent-rules-books
  books:
    - Refactoring by Martin Fowler
    - Refactoring.Guru
  merged_from:
    - refactoring
    - refactoring-guru
  merge_date: "2026-06-29"
  merge_reason: "两源同打包工具 + 内容高度重叠（Fowler 原书 + refactoring.guru 速查），合并减少调度冲突"
---

# Refactoring 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

当需要重构现有代码、识别和消除代码坏味道、改善代码结构、改善可读性，或快速查阅重构手法与设计模式时使用此技能。

## 使用方式

加载此技能后，**必须**读取并严格遵循以下**两个**规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\refactoring\refactoring.mini.md
C:\Users\admin\.agents\skills\agent-rules-books\refactoring-guru\refactoring-guru.mini.md
```

## 来源与定位

| 部分 | 来源 | 用途 |
|------|------|------|
| **refactoring**（Fowler 原书） | Martin Fowler《Refactoring》 | 标准重构操作 + 重构原则（不改变可观察行为） |
| **refactoring-guru**（速查） | refactoring.guru 网站 | 重构手法与设计模式速查目录 |

## 触发关键词（合并后）

重构、坏味道、提取方法、改善结构、速查、模式参考、技巧目录

## 使用时机

| 场景 | 是否该用 refactoring |
|------|:---:|
| ✅ 代码能工作但结构差，需要改善 | ✅ 该用 |
| ✅ 有测试保护，可小步前进 | ✅ 该用 |
| ❌ 没有测试（应先加测试） | ❌ 用 legacy-code |
| ❌ 业务逻辑需要重写（不是重构） | ❌ 先 brainstorming |
| ❌ 全新功能开发 | ❌ 不在重构范畴 |

## 规则概览

### 来自 refactoring（Fowler 原书）

- 重构不改变可观察行为
- 小步前进，频繁测试
- 先让代码能工作，再让它变好
- 识别坏味道：长函数、大类、长参数列表、发散式变化、霰弹式修改、依恋情结等
- 使用重构手法：提取函数、内联、移动、封装、引入参数对象等
- 测试是重构的安全网

### 来自 refactoring-guru（速查）

- 代码坏味道完整分类
- 重构手法速查
- 设计模式应用场景
- 重构与模式的关系

**_两个规则文件都是此技能的核心。务必在重构前读取它们。_**

---

## 迁移说明

- v6.1.1 合并前：refactoring + refactoring-guru 两个独立技能
- v6.1.1 合并后：refactoring 一个超级技能（含两个规则文件引用）
- skill-hub 调度表已同步：refactoring-guru 行已移除
- 黄金轨迹：v54-baseline 中"refactoring-guru"关键词已映射到 refactoring
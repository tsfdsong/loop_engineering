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
    - legacy-code
    - framework-migration-legacy-modernize
  merge_date_v2: "2026-06-29"
  merge_date_v2_1: "2026-06-29"
  merge_reason: "v6.1.1 合并 refactoring-guru → refactoring；v6.2 扩展 legacy-code + framework-migration-legacy-modernize"
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

### 来自 legacy-code（v6.2 扩展）

遗留代码 = 没有测试保护的代码。改造原则：
- **识别接缝（Seam）**：可在不修改源码情况下改变行为的位置
- **破除依赖**：参数化、提取接口、子类化并重写
- **特征测试（Characterization Test）**：记录现有行为
- **小步改动 + 快速验证**
- **高风险改动优先用安全手段**

> 完整 31 行内容：[references/legacy-code-full.md](references/legacy-code-full.md)

### 来自 framework-migration-legacy-modernize（v6.2 扩展）

框架迁移的 strangler fig 模式：
- **渐进式替换**：新旧系统共存，逐步迁移
- **持续业务运行**：迁移期间不中断业务
- **风险管控**：每阶段验证后再继续
- **关键模式**：门面模式、抽象层、双写

> 完整 140 行内容：[references/framework-migration-full.md](references/framework-migration-full.md)

## 触发关键词（v6.2 扩展后）

重构、坏味道、提取方法、改善结构、速查、模式参考、遗留代码、没测试、老系统、安全改动、框架迁移、升级、现代化

## v6.2 扩展整合

```
refactoring 超级技能 = refactoring (Fowler) + refactoring-guru (速查) + legacy-code + framework-migration
├─ 何时用 refactoring 主技能：通用代码改善
├─ 何时用 legacy-code：没有测试保护的旧代码
└─ 何时用 framework-migration：升级框架版本
```

**_规则文件是此技能的核心。务必在重构前读取 references/。_**

---

## 迁移说明

- v6.1.1 合并前：refactoring + refactoring-guru 两个独立技能
- v6.1.1 合并后：refactoring 一个超级技能（含两个规则文件引用）
- skill-hub 调度表已同步：refactoring-guru 行已移除
- 黄金轨迹：v54-baseline 中"refactoring-guru"关键词已映射到 refactoring
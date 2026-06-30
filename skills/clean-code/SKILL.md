---
name: clean-code
description: "Use when applying code quality principles, naming conventions, commit standards, DRY/YAGNI, or general code craftsmanship questions. Triggers on '代码规范', '可读', '命名', 'commit 规范', 'DRY', 'YAGNI'. Do NOT use for: large refactors (use refactoring), or architecture (use software-architecture)."
metadata:
  version: "2.1"
  type: skill
  sources:
    - ciembor/agent-rules-books (2 books)
    - self (1 code-quality-principles)
    - ciembor/agent-rules-books (pragmatic-programmer)
  books:
    - Clean Code by Robert C. Martin
    - Code Complete by Steve McConnell
    - The Pragmatic Programmer by Hunt & Thomas
  merged_from:
    - clean-code
    - code-complete
    - code-quality-principles
    - pragmatic-programmer
  merge_date_v2: "2026-06-29"
  merge_date_v2_1: "2026-06-30"  # v6.4 强化风格融合 + 内联 pragmatic-programmer
  merge_reason: |
    v6.2 合并 → 4 源并排但风格不一致；v6.4 明确 4 源在 4 个不同维度（原则/要点/规范/决策），
    让用户按需选风格而非混用。
  style_dimensions:
    - principles (Martin · 为什么)
    - checklist (McConnell · 是什么)
    - standards (self · 做什么)
    - decisions (pragmatic · 怎么决策)
---

# Clean Code 超级技能

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

## 核心定位：4 种风格 × 4 个维度

不同问题需要不同风格的指导。4 源各占一个维度，互补不冲突：

| 维度 | 源 | 风格 | 何时用 |
|------|-----|------|-------|
| **为什么** | clean-code（Martin） | 原则式 | 设计哲学 / 微观代码形态 |
| **是什么** | code-complete（McConnell） | 要点式 | 全过程速查 / 教科书 |
| **做什么** | code-quality-principles（self） | 表格式 | 工程规范 / 检查清单 |
| **怎么决策** | pragmatic-programmer（Hunt & Thomas） | 决策式 | 工程决策 / 估算 / 权衡 |

**使用顺序建议**：
- **新项目** → Martin（原则）→ self（规范）→ pragmatic（决策）
- **代码审查** → self（清单）→ Martin（原则）→ McConnell（要点）
- **架构决策** → pragmatic（决策）→ self（清单）→ Martin（原则）
- **学习编码** → McConnell（教科书）→ Martin（原则）→ pragmatic（决策）

---

## 维度 1 · 原则（clean-code · Martin）—— 为什么

> 适用：设计哲学 / 微观代码形态 / 命名与抽象层级

### 核心原则

- **为局部推理而写代码** — 一次只需理解一小段
- **函数短小专注** — 单一抽象层级（SLAP）
- **命名精确** — 一个概念一个词，意图明确
- **参数少而有意义** — 避免布尔标志和输出参数
- **命令与查询分离**（CQS）— 函数要么改状态，要么返回值
- **消除隐藏副作用** — 调用前不修改全局状态
- **隔离错误处理** — try/catch 不污染主逻辑
- **暴露行为而非原始表示** — 封装内部数据结构
- **构造/框架/持久化等细节排除在业务行为之外** — 业务不依赖技术
- **公共 API 小而显式** — 难以误用
- **注释仅用于理由/约束/警告/外部契约** — 不解释 what
- **测试作为生产代码对待** — 不低于业务代码标准

### 命名规则

| 维度 | 规则 |
|------|------|
| **意图明确** | `d` → `elapsed_time_in_days` |
| **避免误导** | `account_list`（不是 list，是 dict）→ `accounts` |
| **有意义区分** | `get_active_account()` / `get_inactive_account()` |
| **可读** | `genymdhms`（生成日期）→ `generation_timestamp` |
| **可搜索** | 不写魔法数（`MAX_CLASSES_PER_STUDENT = 7`） |
| **一个概念一个词** | `fetch` / `retrieve` / `get` 统一用 `get` |

### 函数规则

- **短小**（≤ 20 行）
- **只做一件事**
- **单一抽象层级**（SLAP）
- **参数 ≤ 3 个**（多个用对象）
- **无副作用**（或显式命名表明副作用）

---

## 维度 2 · 要点（code-complete · McConnell）—— 是什么

> 适用：全过程速查 / 软件构造教科书 / 子程序设计

### 核心要点

- **为变化而设计，为理解而编码**
- **管理复杂度是软件开发的核心**
- **选用合适的数据结构和算法**（不是炫技）
- **高质量子程序**：
  - 内聚（功能单一）
  - 命名清晰
  - 参数合理
- **防御式编程**：检查输入 / 断言前置条件
- **变量命名反映用途和作用域**
- **控制流的结构和可读性**
- **代码调优要在测量后针对热点**（不要过早优化）

### 子程序设计清单

- [ ] 单一目的？
- [ ] 名字描述功能？
- [ ] 参数 ≤ 7 个？
- [ ] 参数是输入而非修改？
- [ ] 局部变量无重叠？
- [ ] 嵌套 ≤ 3 层？
- [ ] 代码长度合理（≤ 1-2 屏）？
- [ ] 引用全局变量已文档化？

### 防御式编程清单

- [ ] 关键假设有断言？
- [ ] 外部输入有校验？
- [ ] 错误处理路径覆盖？
- [ ] 资源使用有 try-with-resources / context manager？

### 调试策略

- [ ] 错误能稳定复现？
- [ ] 找到最小失败用例？
- [ ] 区分假设和观察？
- [ ] 使用二分查找定位？
- [ ] 修复后加回归测试？

---

## 维度 3 · 规范（code-quality-principles · self）—— 做什么

> 适用：工程规范 / 检查清单 / commit 规范 / 防御式编程

### 异常三分

| 类型 | 特征 | 处理 |
|------|------|------|
| **可恢复** | 重试可能成功（网络超时） | 重试+退避，warning |
| **不可恢复** | 重试无意义（参数错误） | 快速失败，error |
| **需人工** | 需运维介入（资源耗尽） | 报警+降级，critical |

### 契约测试

- API 响应字段白名单检查
- 函数签名兼容性检查
- DB schema diff 检查

### Commit 规范

- **原子**：一个 commit 只做一件事
- **语义化**：`feat:` / `fix:` / `refactor:` / `test:` / `docs:`
- **diff < 200 行**（强制小步）

### 防御式编程

- **输入在边界处校验**（不信任外部）
- **空/零/null/超大值** 四类边界必有测试
- **外部依赖不可用时优雅降级**（不崩）

### 测试金字塔

```
    ╱ E2E ╲      ~10%   (关键用户旅程)
   ╱  集成  ╲     ~20%   (跨模块路径)
  ╱   单测   ╲   ~70%    (业务逻辑 + 边界)
```

- **单测覆盖**：正常 + 边界 + 异常
- **集成测试**：真实依赖，不 mock DB
- **E2E**：只测核心流程

### 代码质量检查清单（上线前）

- [ ] 圈复杂度 ≤ 10 / 函数
- [ ] 行数 ≤ 200 / 文件
- [ ] 重复率 < 5%
- [ ] 注释率 > 15%（业务关键）
- [ ] 测试覆盖率 ≥ 80%

---

## 维度 4 · 决策（pragmatic-programmer · Hunt & Thomas）—— 怎么决策

> 适用：工程决策 / 估算 / 权衡 / 长期职业素养

### 核心原则

- **DRY（Don't Repeat Yourself）**：知识单一来源（不是代码单一来源！）
- **正交性**：组件之间互不依赖（改 A 不影响 B）
- **可逆性**：决策保留回退余地（不"破釜沉舟"）
- **曳光弹**：用最小可行产品快速验证（不"先做大而全"）
- **估算**：先做粗略估算（数量级），再细化
- **原型**：用原型学习风险，不靠猜测
- **领域语言**：用业务术语命名（不用技术黑话）

### DRY 的真正含义

> ❌ **常见误解**：DRY = 不要复制粘贴代码
> ✅ **正确理解**：DRY = 任何知识在系统中必须有单一、明确、权威的表示

**DRY 适用范围**：
- ✅ 业务规则（必须 DRY）
- ✅ 数据库 schema（必须 DRY）
- ✅ API 契约（必须 DRY）
- ⚠️ 代码（可以重复，但要明确意图不同）
- ❌ 文档（不同受众可以重复）

### 正交性检查

| 维度 | 正交 | 不正交 |
|------|------|--------|
| **修改 A 是否引发 B 改动** | 否 | 是 |
| **修改 A 是否引发 C 改动** | 否 | 是 |
| **组件能否独立测试** | 是 | 否 |
| **组件能否独立部署** | 是 | 否 |

### 估算方法

```
1. 给出"理想时间"（无干扰）
2. 加 25% 给"现实时间"（开会 / 邮件）
3. 加 50% 给"实际时间"（意外 / 等待）
4. 加上会议开销
5. 加 5-10% buffer

→ 估算 = 理想 × 1.75 + 会议 + buffer
```

**估算准确度目标**：
- 数量级（1天 vs 1周）：80% 准确
- 精确到小时：30% 准确
- **结论**：报数量级 + 风险，不报精确小时

### 曳光弹 vs 原型

| 模式 | 目的 | 输出 |
|------|------|------|
| **曳光弹** | 找未知 + 走通关键路径 | 可演进的最小系统 |
| **原型** | 学风险 + 验证假设 | 一次性探索代码（之后丢弃） |

### 决策检查清单

- [ ] **可逆吗？**（可逆就大胆试）
- [ ] **有原型数据吗？**（没数据先做原型）
- [ ] **正交性？**（改 A 是否影响 B）
- [ ] **DRY 边界？**（知识是否单源）
- [ ] **业务价值？**（不是技术炫技）
- [ ] **团队能力？**（是否能维护）
- [ ] **未来 6 个月会变化吗？**（保留可逆性）

---

## 4 维度交叉使用

### 场景 1 · 命名一个类

```
1. 原则（Martin）: 类名是名词，意图明确
2. 要点（McConnell）: 名字描述类的主要职责
3. 规范（self）: 不用缩写，不用技术黑话
4. 决策（pragmatic）: 用业务术语而非技术术语
```

### 场景 2 · 写一个函数

```
1. 原则（Martin）: 短小专注、单一抽象层级
2. 要点（McConnell）: 单一目的、参数 ≤ 3 个、命名清晰
3. 规范（self）: 加前置条件断言 + 异常三分
4. 决策（pragmatic）: 不过度抽象、不预先设计
```

### 场景 3 · 代码审查

```
1. 规范（self）: 检查清单（异常 / commit / 测试）
2. 原则（Martin）: 看命名 / 函数 / 抽象
3. 要点（McConnell）: 看子程序设计 / 防御式
4. 决策（pragmatic）: 看是否 DRY / 正交 / 可逆
```

---

## 触发关键词

干净代码、可读性、命名、函数拆分、代码规范、代码原则、异常处理、commit规范、防御式编程、软件构造、全套流程、代码审查、复杂度、深模块、抽象、信息隐藏、DRY、正交、可逆、曳光弹、原型、估算

---

## 与其他技能配合

| 场景 | 配合技能 |
|------|---------|
| 业务规则提取 | `domain-driven-design` |
| 重构实现 | `refactoring`（本技能原则 + refactoring 手法） |
| 架构级设计 | `software-architecture`（pragmatic 决策 → 架构选择） |
| 测试规范 | `testing`（self 规范 + TDD） |
| 上线前审计 | `production-readiness`（规范检查） |

---

## 限制

- **不替代语言特定最佳实践** — 不同语言有不同细节
- **不替代业务理解** — 命名需业务术语
- **不替代代码审查** — 自动工具无法判断意图
- **完整内容在原书** — 本 SKILL.md 给出框架，详细手法查原书

---

## 迁移说明

- v6.1.1 合并：clean-code + code-complete + code-quality-principles
- v6.2 扩展：+ pragmatic-programmer（合并到 references/）
- v6.2 状态：4 源并排 + "v6.2 扩展整合"树状图
- **v6.4 重组**：4 源 → 4 个明确维度（原则/要点/规范/决策），避免风格混用
- 内联：pragmatic-programmer 34 行要点已融入"维度 4：决策"章节
- 保留：clean-code + code-complete 通过 `~/.agents/skills/agent-rules-books/` 规则文件引用
- skill-hub 调度表已同步

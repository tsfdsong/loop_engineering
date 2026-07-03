---
name: refactoring
description: "Use when improving existing code structure, fixing code smells, reducing complexity, or applying design patterns. Triggers on '重构', '坏味道', '太长', '重复代码', 'refactor', 'legacy code'. Do NOT use for: new features (use brainstorming), or debugging (use systematic-debugging)."
metadata:
  version: "2.1"
  type: skill
  source: ciembor/agent-rules-books + community
  books:
    - Refactoring by Martin Fowler
    - Refactoring.Guru
    - Working Effectively with Legacy Code by Michael Feathers
  merged_from:
    - refactoring
    - refactoring-guru
    - legacy-code
    - framework-migration-legacy-modernize
  merge_date_v2: "2026-06-29"
  merge_date_v2_1: "2026-06-30"  # v6.4 强化全流程 + 内联 legacy-code
  merge_reason: |
    v6.2 合并 → 4 源并排堆叠；v6.4 重组为"重构全流程"（识别 → 计划 → 小步 → 验证），
    真正从"重构操作"角度融合而非简单堆叠。
  workflow:
    - identify (坏味道)
    - plan (接缝/边界)
    - step-by-step (小步前进)
    - verify (测试保护)
---

# Refactoring 超级技能

## 核心定位：4 阶段重构工作流

重构不是"随手改改"，而是受控的 4 阶段过程：

```
┌────────────────────────────────────────────────────────┐
│ Stage 1: 识别 (Identify) — 哪些代码需要重构？           │
│   坏味道识别 + 重构目标定义                              │
│   ↓ 锁定目标                                            │
│ Stage 2: 计划 (Plan) — 如何安全重构？                   │
│   接缝识别 + 测试覆盖 + 重构手法选择                     │
│   ↓ 计划就绪                                            │
│ Stage 3: 小步 (Step-by-Step) — 执行重构                │
│   一次改一处 + 频繁测试 + 提交原子化                     │
│   ↓ 目标坏味道消除                                      │
│ Stage 4: 验证 (Verify) — 重构成果                       │
│   行为不变 + 性能持平 + 可读性提升                       │
│   （下一轮 Stage 1）                                     │
└────────────────────────────────────────────────────────┘
```

**何时该用 refactoring**：
- ✅ 代码能工作但结构差
- ✅ 有测试保护
- ✅ 业务规则清晰

**何时不该用**（应换技能）：
- ❌ 没测试（应先 testing 加保护）
- ❌ 业务逻辑需要重写（应 brainstorming）
- ❌ 全新功能开发（不是重构）
- ❌ 框架升级（应用 framework-migration 模式）

---

## Stage 1 · 识别（坏味道 + 重构目标）

### 12 大坏味道速查

| 坏味道 | 信号 | 优先重构手法 |
|-------|------|-------------|
| **长函数** | > 30 行 / 多个抽象层级 | Extract Function（提取函数） |
| **大类** | > 300 行 / 多职责 | Extract Class（提取类） |
| **长参数列表** | > 3 个参数 | Introduce Parameter Object（参数对象） |
| **发散式变化** | 一个类因多个原因修改 | Extract Class / Single Responsibility |
| **霰弹式修改** | 一个改动需改多个类 | Move Method / Move Field |
| **依恋情结** | 函数更爱用其他类数据 | Move Method |
| **数据泥团** | 多个字段总一起出现 | Extract Class / Parameter Object |
| **基本类型偏执** | 用基本类型表示领域概念 | Replace Primitive with Object |
| **重复代码** | 相同结构在多处 | Extract Function / Class |
| **循环语句** | 显式循环难读 | Replace Loop with Pipeline |
| **夸夸其谈的通用性** | 预留的扩展点无人用 | Remove Dead Code |
| **临时字段** | 字段只在某些场景用 | Extract Class |

### 重构目标定义（SMART）

- [ ] **Specific**：消除哪个坏味道？
- [ ] **Measurable**：用什么指标衡量改善？（行数 / 圈复杂度 / 测试覆盖率）
- [ ] **Achievable**：能在单次 PR 中完成？
- [ ] **Relevant**：对业务价值有贡献？
- [ ] **Time-bound**：什么时间点必须完成？

> **示例**：`OrderService.process()` 圈复杂度从 18 降到 ≤ 8，提取 3 个领域方法

---

## Stage 2 · 计划（接缝 + 测试 + 手法选择）

### 2.1 识别接缝（Seam）

> **接缝 = 可在不修改源码情况下改变行为的位置**

| 接缝类型 | 示例 | 用途 |
|---------|------|------|
| **方法参数化** | 构造函数接受接口而非具体类 | 注入 mock / 替身 |
| **提取接口** | 抽象出 `PaymentGateway` 接口 | 替换实现 |
| **子类化 + 重写** | 继承并重写关键方法 | 测试用 |
| **静态方法抽离** | 提到可注入的 bean | 测试替换 |
| **时间接缝** | `Clock` 抽象 | 时间相关测试 |
| **文件系统接缝** | 抽到接口 | 文件 IO mock |

### 2.2 测试覆盖优先级

```
优先级 1（必须）: 目标坏味道所在方法的核心路径
优先级 2（应该）: 边界条件 / 异常路径
优先级 3（可以）: 调用方（保证重构不破坏下游）
```

**遗留代码特殊处理**（无测试时）：
1. **特征测试（Characterization Test）**：记录现有行为（即使是 bug）
2. **写完测试 → 跑通 → 才动代码**
3. **每次重构都重跑特征测试**

### 2.3 重构手法选择

| 场景 | 推荐手法 | 替代手法 |
|------|---------|---------|
| 函数太长 | Extract Function | Replace Method with Method Object |
| 类太大 | Extract Class | Replace Class with Delegate |
| 重复代码 | Extract Function / Class | Form Template Method |
| 条件复杂 | Replace Conditional with Polymorphism | Decompose Conditional |
| 循环复杂 | Replace Loop with Pipeline | — |
| 数据耦合 | Introduce Parameter Object | Preserve Whole Object |
| API 难用 | Rename / Move / Hide Delegate | — |

---

## Stage 3 · 小步前进（Step-by-Step）

> 核心原则：**一次一处，频繁测试，原子提交。**

### 3.1 执行节奏

```
TDD 红绿重构循环（每步都走完）:

1. 写/确认测试（红）
2. 改一处（提取函数 / 改类名 / 移字段）
3. 跑测试（绿）
4. 提交（原子 commit）
5. 继续下一处
```

### 3.2 关键纪律

- ❌ **不要**"改一堆然后一起测"（难定位问题）
- ❌ **不要**重构时改业务逻辑（范围控制）
- ❌ **不要**重构 + 添加新功能混在一个 commit
- ✅ **每次**重构后跑全部测试（防连锁影响）
- ✅ **每次**重构独立 commit（便于 review / revert）
- ✅ **测试**不通过 = 立即回滚（不要继续叠加）

### 3.3 提交模板

```bash
git commit -m "refactor(<scope>): <重构手法> <目标>

- 提取/移动/重命名: <具体内容>
- 行为不变: <验证方式>
- 测试: <新增/更新>

Refs: <原 issue / 设计文档>"
```

---

## Stage 4 · 验证（行为不变 + 可读性提升）

### 4.1 验证清单

| 维度 | 验证方式 | 通过标准 |
|------|---------|---------|
| **行为不变** | 跑全部测试 | 100% 通过 |
| **性能持平** | benchmark 对比 | ±5% 内 |
| **可读性** | code review 反馈 | 圈复杂度下降 |
| **可维护性** | 后续改动成本 | 改一处不引发连锁 |
| **测试覆盖** | coverage 报告 | 不下降 |

### 4.2 重构失败信号

- ⚠️ **测试频繁失败**：可能改大了，应该回滚拆分
- ⚠️ **新代码比旧代码更复杂**：方向错了
- ⚠️ **修改引发连锁改动**：抽象层级不对
- ⚠️ **性能下降**：可能引入额外开销

---

## 特殊场景：遗留代码改造（Feathers）

> **遗留代码 = 没有测试的代码。** 改造核心 = 在不破坏行为的前提下增加测试覆盖。

### 改造原则

1. **识别接缝**：找可在不修改源码情况下改变行为的位置
2. **破除依赖**：参数化 / 提取接口 / 子类化并重写
3. **特征测试**：记录现有行为（即使行为是 bug）
4. **小步改动 + 快速验证**
5. **高风险改动优先用安全手段**（参数化而非直接改类）

### 接缝识别清单

| 障碍 | 破除方法 |
|------|---------|
| `new` 关键字创建紧耦合对象 | 工厂方法 / DI 容器 |
| 静态方法调用 | 包装到可注入 bean |
| 不可见的方法调用 | 包装到虚方法 |
| 时间耦合（`datetime.now()`） | 注入 `Clock` 抽象 |
| 文件系统耦合 | 抽象 `FileSystem` 接口 |
| 网络耦合 | 抽象 `HttpClient` 接口 |
| 数据库耦合 | 抽到 Repository |

### 改造节奏

```
1. 找到目标代码（遗留方法）
2. 写特征测试（红）
3. 识别接缝（如何替换依赖）
4. 破除依赖（参数化 / 接口提取）
5. 测试通过（绿）
6. 提取函数 / 重命名
7. 提交
8. 下一个目标
```

---

## 特殊场景：框架迁移（strangler fig 模式）

> 框架升级 / 替换时使用 — 渐进式替换，新旧共存，避免"大爆炸"。

### 模式要点

- **渐进式替换**：新旧系统共存，逐步迁移
- **持续业务运行**：迁移期间不中断业务
- **风险管控**：每阶段验证后再继续
- **关键模式**：门面模式 / 抽象层 / 双写

### 迁移步骤

```
1. 引入门面（façade）：所有外部请求先打门面
2. 新实现一个功能（在新框架）
3. 门面路由切到新实现（按用户 / 按 URL / 按特性开关）
4. 验证新实现
5. 旧实现标记废弃
6. 全量切到新实现
7. 删除旧实现
8. 下一功能重复 2-7
```

### 双写策略

迁移数据库等持久层时：
- **双写**：写新 + 写旧，验证一致后再读新
- **回填**：一次性把旧数据同步到新
- **切换读**：先双写后切换读
- **下掉旧**：验证稳定后下掉

---

## 触发关键词（合并后）

重构、坏味道、提取方法、改善结构、速查、模式参考、遗留代码、没测试、老系统、安全改动、框架迁移、升级、现代化、strangler fig、双写

---

## 与其他技能配合

| 场景 | 配合技能 |
|------|---------|
| 业务规则提取 | `domain-driven-design`（聚合边界 + 领域服务） |
| 添加测试保护 | `testing`（TDD + 特征测试） |
| 业务逻辑改写 | `brainstorming`（先想清楚再重构） |
| 架构级重构 | `software-architecture`（Layer 1 → 2 → 3 演进） |
| 上线前审计 | `production-readiness`（重构后稳定性验证） |

---

## 限制

- **不改变可观察行为** — 重构前提是行为不变
- **不替代新功能开发** — 重构 ≠ 重写
- **不替代测试保护** — 没测试的代码先加测试
- **完整手法目录查原书** — Fowler / refactoring.guru 700+ 手法

---

## 迁移说明

- v6.1.1 合并：refactoring + refactoring-guru 两个独立技能 → refactoring
- v6.2 扩展：+ legacy-code + framework-migration-legacy-modernize
- v6.2 状态：4 源并排堆叠（"v6.2 扩展整合"只是树状图）
- **v6.4 重组**：4 源 → 重构全流程（识别 → 计划 → 小步 → 验证）
- 内联：legacy-code 31 行要点已融入"特殊场景：遗留代码改造"章节
- 保留：framework-migration-full.md（140 行，strangler fig 完整模式）
- orch 调度表已同步

---

## 论源（v1.0.4 工程实践红线对接）

本技能作为以下工程实践红线的**方法论支撑**（单点真源引用，AGENTS.md §9）：

- **R4.1 测试保护** — 直接对应本技能 workflow 的"verify（测试保护）"阶段；无测试覆盖代码禁止重构（Working Effectively with Legacy Code / Michael Feathers）
- **R4.4 机械重构优先** — 直接对应 Refactoring by Martin Fowler 的"机械重构 → 架构重构"递进原则；rename / extract / move 优先于架构重构

> **红线触发场景**：任何 AI 重构现有代码 / 处理 legacy code / 应用设计模式时，必须遵循 R4.1 + R4.4；本技能提供重构全流程方法论（识别 → 计划 → 小步 → 验证）。
> **同步版本**：AGENTS.md v1.0.4（2026-07-03）

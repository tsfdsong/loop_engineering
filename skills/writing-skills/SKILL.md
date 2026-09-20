---
name: writing-skills
description: |
  TRIGGER: 创建新 skill / 编辑现有 skill / 部署前验证 skill 可用性（不用于：用技能执行开发任务（本技能仅用于编写和维护技能本身））
  RULE: no specific rule（方法论 skill · skill 编写方法论）
  DETAIL: 本 SKILL.md（skill 结构 + 元数据 + 验证流程）+ references/skill-spec.md（详细规范）
---

# Writing Skills（编写技能）

## Overview（概述）

**Writing skills 就是把 TDD 应用于流程文档。**

你写测试用例（带 subagent 的压力场景），看它失败（基线行为），写技能（文档），看测试通过（agent 遵守），然后重构（堵漏洞）。

**核心原则：** 没看过 agent 在无技能时失败，你就不知道这个技能教的对不对。

**REQUIRED BACKGROUND：** 使用本技能前必须理解 superpowers:test-driven-development。那个技能定义了根本的 RED-GREEN-REFACTOR 循环，本技能把 TDD 适配到文档。

**官方指南：** Anthropic 官方 skill 编写最佳实践见 anthropic-best-practices.md。该文档提供补充本技能 TDD 视角的模式与指南。

## 什么是 Skill？

**Skill** 是已验证技术、模式或工具的参考指南。技能帮助未来的 Claude 实例找到并应用有效方法。

**Skills 是：** 可复用的技术、模式、工具、参考指南

**Skills 不是：** 关于你某次如何解决问题的叙事

## TDD 到 Skill 的映射

| TDD 概念 | Skill 创建 |
|-------------|----------------|
| **测试用例** | 带 subagent 的压力场景 |
| **生产代码** | 技能文档（SKILL.md） |
| **测试失败（RED）** | 无技能时 agent 违规（基线） |
| **测试通过（GREEN）** | 技能在场时 agent 遵守 |
| **重构** | 保持遵守的同时堵漏洞 |
| **先写测试** | 写技能**前**跑基线场景 |
| **看它失败** | 逐字记录 agent 用的合理化借口 |
| **最小代码** | 写针对那些具体违规的技能 |
| **看它通过** | 验证 agent 现在遵守 |
| **重构循环** | 发现新借口 → 堵 → 重验 |

整个技能创建过程遵循 RED-GREEN-REFACTOR。

## 何时创建 Skill

**创建，当：**
- 这个技术对你不是直觉显然的
- 你会跨项目再次引用它
- 模式适用面广（非项目特定）
- 其他人会受益

**不创建，当：**
- 一次性方案
- 别处已充分文档化的标准实践
- 项目特定约定（放 CLAUDE.md）
- 机械约束（能用 regex/校验强制就自动化——文档留给判断类问题）

## Skill 类型

### Technique（技术）
有步骤可循的具体方法（condition-based-waiting、root-cause-tracing）

### Pattern（模式）
思考问题的方式（flatten-with-flags、test-invariants）

### Reference（参考）
API 文档、语法指南、工具文档（office docs）

## 目录结构

```
skills/
  skill-name/
    SKILL.md              # 主参考（必需）
    supporting-file.*     # 仅在需要时
```

**扁平命名空间** —— 所有技能在一个可搜索命名空间

**拆分独立文件，当：**
1. **重参考**（100+ 行）—— API 文档、完整语法
2. **可复用工具** —— 脚本、实用程序、模板

**保持内联：**
- 原则与概念
- 代码模式（< 50 行）
- 其余一切

## SKILL.md Structure (核心要点)

**Frontmatter 必填两字段：** `name`（只用字母/数字/连字符）+ `description`（第三人称、以 "Use when..." 开头、只述何时用不述做什么、尽量 <500 字符、总 frontmatter ≤1024 字符）。

**主干段落骨架：** Overview（核心原则 1-2 句）→ When to Use（症状/用例 + 何时不用）→ Core Pattern（before/after）→ Quick Reference（表）→ Implementation（inline 或链接）→ Common Mistakes。

> 完整结构模板、字段细节、good/bad YAML 示例、token 效率技巧、交叉引用规范 → **见 `references/skill-spec.md` § SKILL.md 结构模板 + § Claude Search Optimization**。

## Claude Search Optimization（CSO）— 要点

**发现性关键：** 未来的 Claude 需要能**找到**你的 skill。

**铁律：Description = When to Use，NOT What the Skill Does。** description 概述工作流会形成 Claude 走的捷径，导致它跳过 skill 主体。测试已证实此退化模式。

**核心技巧：**
- 以 "Use when..." 开头，只给触发条件，绝不概述工作流
- 用具体触发器/症状/场景（技术无关，除非 skill 技术特定）
- Keyword coverage：覆盖错误消息、症状、同义词、工具名
- Descriptive naming：动词在前、主动语态（`creating-skills` > `skill-creation`）
- Token efficiency：getting-started <150 词、高频 <200 词、其他 <500 词
- **不用 `@` 链接**引用其他 skill（会强制加载烧 context）；用 `**REQUIRED BACKGROUND:** Use <skill-name>` 形式

> 完整 good/bad YAML 对比、token 压缩示例、命名规则、cross-reference 规范 → **见 `references/skill-spec.md` § Claude Search Optimization**。

## Flowchart Usage — 要点

**只在以下场景用 flowchart：** 不明显的决策点、可能提前停下的循环、"A vs B" 决策。

**绝不用于：** reference 材料（用表/列表）、代码示例（用 markdown 块）、线性指令（用编号列表）、无语义标签。

graphviz 样式见 @graphviz-conventions.dot；渲染 SVG 见本目录 `render-graphs.js`。

> 完整决策 flowchart + 何时用 markdown vs inline flowchart → **见 `references/skill-spec.md` § Flowchart Usage**。

## Code Examples — 要点

**一个优秀示例胜过一堆平庸示例。** 选最相关语言（测试→TS/JS、系统调试→Shell/Python、数据→Python）。好示例：完整可运行、注释解释 WHY、来自真实场景、可改造（非填空模板）。不要多语言实现、不要捏造示例。

> 完整 do/don't 列表 → **见 `references/skill-spec.md` § Code Examples**。

## File Organization — 要点

三种形态：**Self-Contained**（全 inline）、**Skill with Reusable Tool**（SKILL.md + example 代码）、**Skill with Heavy Reference**（SKILL.md + 600 行 API ref + scripts/）。

> 完整目录结构示例 → **见 `references/skill-spec.md` § File Organization**。

## The Iron Law (同 TDD)

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

适用于新技能**和**对既有技能的编辑。

先写技能再测试？删掉，重来。
编辑技能不测试？同样违规。

**无例外：**
- "简单加一点"不行
- "只加一节"不行
- "文档更新"不行
- 不许把未测试的改动留作"参考"
- 不许边跑测试边"顺手改"
- 删除就是删除

**REQUIRED BACKGROUND：** superpowers:test-driven-development 技能解释了这为什么重要。同样原则适用于文档。

## 受限环境的降级验证协议（2026-09-20 引入）

Iron Law 要求编辑技能前先看失败，但 subagent 压力测试环境可能不可用（认证/限额等，见 lessons L#006）。此时按本协议降级，**并在交付物中如实标注**：

1. **结构等价验证**（替代行为验证）：改动前后 `##`/`###` 标题数量对照（`git show HEAD:<file>` vs 当前）——翻译/重写类编辑的头号丢失模式就是丢节（2026-09-20 全库中文化中拦截 4 处）；列表条数增量必须可解释。
2. **audit 结构套件**：`pytest tests/test_audit_tools.py`（frontmatter/死链/占位符/行数/references 残留，25+ 项机械检查）。
3. **声明义务**：verdict / commit message 注明"未做 subagent 压力测试，验证为结构级"——环境恢复后补压测，不得宣称行为级结论。

**禁止**：以降级验证冒充压力测试宣称"技能有效"；以"环境不可用"为由跳过 1/2（机械检查永远可跑）。

## Testing All Skill Types — 要点

不同 skill 类型测不同维度：

| 类型 | 测什么 | 成功标准 |
|---|---|---|
| **Discipline-Enforcing**（规则） | 学术问题 + 压力场景 + 多重压力叠加 | 最大压力下仍守规则 |
| **Technique**（how-to） | 应用 + 变体 + 信息缺失 | 成功应用到新场景 |
| **Pattern**（心智模型） | 识别 + 应用 + 反例 | 正确识别何时/如何用 |
| **Reference**（文档/API） | 检索 + 应用 + 空白 | 找到并正确应用信息 |

> 每类的完整测试方法、场景示例 → **见 `references/skill-spec.md` § Testing All Skill Types**。

## Common Rationalizations for Skipping Testing

| 借口 | 现实 |
|--------|---------|
| "Skill 显然很清楚" | 对你清楚 ≠ 对其他 agent 清楚。测它。 |
| "只是个参考文档" | 参考也会有缺口、不清的小节。测检索。 |
| "测试杀鸡用牛刀" | 未测试的技能就是有问题。15 分钟测试省数小时。 |
| "出问题再测" | 出问题 = agent 用不了技能。部署**前**测。 |
| "测试太麻烦" | 比在生产环境调试坏技能省事。 |
| "我有信心它没问题" | 过度自信保证出问题。照样测。 |
| "学术评审够了" | 读过 ≠ 用过。测应用场景。 |
| "没时间测" | 部署未测试技能会花更多时间修。 |

**以上全部意味着：部署前测试。无例外。**

## Bulletproofing Skills Against Rationalization — 要点

执行纪律的 skill（如 TDD）必须抗合理化。核心 5 招：

1. **显式封堵每个漏洞** — 不只陈述规则，显式禁止具体规避（"delete means delete / 不留 reference / 不边测边改"）
2. **切断"精神 vs 字面"争论** — 早期立基础原则："违反字面即违反精神"
3. **建合理化表** — 从基线测试捕获每个借口入表（Excuse | Reality）
4. **建 Red Flags 列表** — 让 agent 自检（"this is different because..." = STOP）
5. **CSO 加违规症状** — description 里标"即将违规"的症状

**心理学基础：** 权威/承诺/稀缺/社会认同/归属感原则（研究基础见 persuasion-principles.md）。

> 完整 good/bad 对比、Red Flags 模板、CSO 违规症状示例 → **见 `references/skill-spec.md` § Bulletproofing Skills Against Rationalization**。

## 瘦身纪律与措辞微测 — 要点（2026-09-20 引入 · 源自 superpowers v6.0/v6.2）

**瘦身红线：反 rationalization 内容不是赘肉。** superpowers v6.2.0 A/B 实测：删掉 TDD "Why Order Matters" 论证段 → test-first 行为 8/10 退化到 5/10；以"借口表行内反驳"形式保留则不退化。渐进式披露瘦身时**禁止**把反借口内容当冗余删除 — 它们在 agent 合理化的瞬间被命中，是行为保持的载荷。

**形式匹配失败模式 + 措辞微测：**
- 指导形式按失败模式选：扁平禁令（防明知故犯）/ worked example（防不知何为合规）/ 借口表行内反驳（防压力下合理化）
- 措辞改动后微测：抽样 2-3 次压力场景 vs 无指导对照组，行为无退化才合入；重大改动用完整盲对比

> 完整纪律、实证数据、形式选择表 → **见 `references/skill-spec.md` § Slimming Discipline / § Match the Form to the Failure**。

## RED-GREEN-REFACTOR for Skills

遵循 TDD 循环：

### RED: 写失败测试（基线）

无技能跑压力场景。记录确切行为：
- 他们做了什么选择？
- 用了什么合理化借口（逐字）？
- 哪些压力触发了违规？

这就是"看测试失败"——写 skill 前必须先看 agent 自然会做什么。

### GREEN: 写最小技能

写针对那些具体合理化的 skill。不加针对假设情况的内容。

同一场景**有** skill 再跑。agent 现在应守规则。

### REFACTOR: 堵漏洞

agent 找到新合理化？加显式反制。重测直到无懈可击。

**测试方法：** 完整方法（压力场景写法、压力类型、系统性堵漏洞、元测试）见 @testing-skills-with-subagents.md。

## Anti-Patterns — 要点

四类禁止：**Narrative Example**（太具体不可复用）、**Multi-Language Dilution**（多语言平庸实现）、**Code in Flowcharts**（不能复制粘贴）、**Generic Labels**（无语义）。

> 完整反例 + why bad → **见 `references/skill-spec.md` § Anti-Patterns**。

## STOP: 进入下一个技能之前

**写完任何技能后，必须停下完成部署流程。**

**禁止：**
- 不逐个测试就批量创建多个技能
- 当前技能未验证就进入下一个
- 以"批量更高效"为由跳过测试

**下方部署清单对每个技能都是强制的。**

部署未测试的技能 = 部署未测试的代码。违反质量标准。

## Skill Creation Checklist (TDD 适配)

**重要：用 TodoWrite 为下方每一项创建 todo。**

**RED 阶段 - 写失败测试：**
- [ ] 创建压力场景（纪律类技能 3+ 重压叠加）
- [ ] 无技能跑场景——逐字记录基线行为
- [ ] 识别合理化/失败的模式

**GREEN 阶段 - 写最小技能：**
- [ ] Name 只用字母、数字、连字符（无括号/特殊字符）
- [ ] YAML frontmatter 含必填 `name` 与 `description`（≤1024 字符；见 [spec](https://agentskills.io/specification)）
- [ ] Description 以 "Use when..." 开头并含具体触发器/症状
- [ ] Description 第三人称
- [ ] 全文埋可搜索关键词（报错、症状、工具）
- [ ] 清晰的 Overview 含核心原则
- [ ] 针对 RED 阶段识别的具体基线失败
- [ ] 代码 inline 或链接独立文件
- [ ] 一个优秀示例（非多语言）
- [ ] 有技能跑场景——验证 agent 现在遵守

**REFACTOR 阶段 - 堵漏洞：**
- [ ] 从测试识别**新**合理化
- [ ] 加显式反制（纪律类技能）
- [ ] 从全部测试迭代构建合理化表
- [ ] 建 red flags 列表
- [ ] 重测直到无懈可击

**质量检查：**
- [ ] 仅在决策不显然时用小 flowchart
- [ ] Quick reference 表
- [ ] Common mistakes 节
- [ ] 无叙事故事
- [ ] 附属文件仅用于工具或重参考
- [ ] **主干 SKILL.md ≤ 500 行**（详细规范挪到 `references/` · v2.0 硬规则）

**部署：**
- [ ] 技能 commit 到 git 并 push 到你的 fork（若已配置）
- [ ] 考虑经 PR 回馈上游（若普遍有用）

## Discovery Workflow

未来的 Claude 如何找到你的技能：

1. **遇到问题**（"测试 flaky"）
3. **找到 SKILL**（description 匹配）
4. **扫 Overview**（相关吗？）
5. **读模式**（quick reference 表）
6. **加载示例**（实现时才看）

**为这个流程优化** —— 可搜索词尽早、尽多。

## references/

| 文档 | 内容 |
|------|------|
| **`references/skill-spec.md`** | 🆕 v2.0 拆分 · 详细规范（结构模板 / CSO / flowchart / code examples / file org / testing / rationalization / RED-GREEN-REFACTOR / anti-patterns） |
| `anthropic-best-practices.md` | Anthropic 官方 skill 编写最佳实践 |
| `testing-skills-with-subagents.md` | 完整 subagent 测试方法（压力场景 / 堵漏洞 / 元测试） |
| `persuasion-principles.md` | 说服原则研究基础（Cialdini 等） |
| `graphviz-conventions.dot` | graphviz 样式规则 |
| `render-graphs.js` | flowchart → SVG 渲染脚本 |

## The Bottom Line（底线）

**创建技能就是流程文档的 TDD。**

同一铁律：无失败测试，不写技能。
同一循环：RED（基线）→ GREEN（写技能）→ REFACTOR（堵漏洞）。
同一收益：更高质量、更少意外、无懈可击的结果。

代码用 TDD，技能也用 TDD。同一纪律，应用于文档。

> **详细规范（格式/长度/字数/具体写法/测试方法/反模式）一律 lazy load 自 `references/skill-spec.md`。本主干只保留入口 + 流程 + 关键检查清单。**

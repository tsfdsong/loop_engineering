---
name: agent-skill-architecture
description: |
  TRIGGER: 设计或评审 Agent skill / 创建/编辑 skill 架构 / '技能设计' / '技能架构' / 'SKILL.md 设计'（不用于：使用技能直接调 Skill tool，纯代码重构用 refactoring）
  RULE: no specific rule（方法论 skill · skill 设计元方法论）
  DETAIL: 本 SKILL.md + 与 writing-skills / context-driven-development 配合
metadata:
  version: "1.0"
  type: rule
  mode: design-review
---

# Agent 技能架构设计规范

设计或审查 Agent 技能时自动加载。强制执行以下规范。

## 架构硬规则

1. **分层单向**：路由→编排→执行，上层不碰下层细节
2. **职责不交叉**：删掉其他技能后仍能独立工作
3. **技能是插件**：不绑定到特定宿主
4. **最小信号**：编排层传指针不传内容（任务描述+验收条件+产物路径）

## 交互规则

确认点与选项设计遵循 AGENTS.md §C2（用户交互红线 · 单点真源）：决策必须用 `AskUserQuestion` 工具调用（推荐项标注 + 禁止自由文本输入）。细则以红线文档为准，此处不重复承载（2026-09-20 审查修复：原 4 条复述已删，防漂移）。

## 质量硬规则

1. 验收条件必须绑定到具体门禁维度（不能绑定 = 太模糊 = 必须澄清）
2. 失败按根因分类（A 代码bug / B 验证错 / C 环境 / 🎨 主观）
3. 必须有退出机制（stagnated / exhausted）
4. 决策写入 decision_log

## 文件组织

1. 技能文件 > 500 行 → 拆分为主文件 + references/
2. 主文件只做入口分发（≤ 200 行）
3. 共享组件提取为独立文件（一处修改、多模式受益）

## 自信度闸门

| 自信度 | 行为 |
|:---:|------|
| 🟢 高 | 审计闸门：自动通过 + 记录决策 |
| 🟡 中 | 软闸门：推荐方案 + 5s 倒计时 |
| 🔴 低 | 深度闸门：生成 BDD 示例 → 用户快速选 |

---

## 评审示例

**输入**：某技能 SKILL.md 400 行，内含 3 个完整 CI 配置模板 + 路由规则 + 评审清单。

**发现**（按分层单向规则排序）：
- ❌ 主文件超 200 行入口上限 → CI 模板移入 `references/ci-patterns.md`，原位换 3 行指针
- ❌ 路由层向执行层传全文内容 → 改传最小信号（任务描述 + 验收条件 + 产物路径）
- ✅ 职责独立：删掉编排技能后本技能仍可独立工作

**输出**：结构裁决表（规则编号 + 违规位置 + 修复动作），配合 `references/checklist.md` 逐项核对。

---

完整规范: 本技能自含（设计原则已并入上文各节）+ 审查清单见 `references/checklist.md`

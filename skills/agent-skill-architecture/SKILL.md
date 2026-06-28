---
name: agent-skill-architecture
description: Agent 技能架构设计规范 —— 设计或审查 Agent 技能时自动加载，强制执行分层、交互、质量、文件组织的硬规则。
metadata:
  version: "1.0"
  type: rule
  mode: design-review
---

# Agent 技能架构设计规范

> 🔴 **用户交互红线**：遵循 skill-hub 的 4 项硬要求——必须用 `AskUserQuestion` 列出选项（含推荐），推荐项标 `(推荐)` 并说明理由，不推荐项必须说明理由，禁止自由文本输入和开放式追问。

设计或审查 Agent 技能时自动加载。强制执行以下规范。

## 架构硬规则

1. **分层单向**：路由→编排→执行，上层不碰下层细节
2. **职责不交叉**：删掉其他技能后仍能独立工作
3. **技能是插件**：不绑定到特定宿主
4. **最小信号**：编排层传指针不传内容（任务描述+验收条件+产物路径）

## 交互硬规则 🔴

1. 确认点必须用 `AskUserQuestion` 选择框
2. 第一个选项必须是推荐项，标注 `(推荐)` + 推荐理由
3. 其他选项标注不推荐的理由
4. **禁止**要求用户输入文字、数字、"直接回车"

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

完整规范: [agent-skill-architecture-principles.md](../../../../tsfdsong/python-project/yimi-ai-hub/docs/superpowers/specs/agent-skill-architecture-principles.md)

审查清单: `references/checklist.md`

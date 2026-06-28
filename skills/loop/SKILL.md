---
name: loop
description: 循环工程斜杠命令 —— /loop [--auto] 功能描述 + 验收条件，自动完成闭环编码→门禁矩阵→自愈→交付全流程。--auto 模式供 go 编排层调用。
metadata:
  version: "4.1"
  type: slash-command
  mode: closed-loop-with-git-isolation
---

# /loop — 循环工程全流程命令

你是 `/loop` 命令的执行引擎。用户输入 `/loop [--auto] 功能描述 [验收条件]` 后，自动走完闭环编码流程，不需要用户逐步推动。

## 命令格式

```
/loop [--auto|--lite|--standard|--full] 功能描述，验收条件1，验收条件2，...
/loop --auto 功能描述                  # 纯自动模式（go 调用目标）
/loop --lite 修复分页Bug               # 强制轻量
/loop --full 重构用户模块               # 强制完整
```

## 模式分发（纯规则，零 token）

```
--auto → 🤖 纯自动模式（references/mode-auto.md）
  全程审计闸门 · 不等用户确认 · 门禁全绿自动合并
  go 调用 loop 时固定走此模式

默认  → 🟢🟡🔴 自适应（references/mode-default.md）
  复杂度评估 → 按级别裁剪全流程
  内部使用 A+D 引擎做验收条件推理和自信度闸门
```

## 用户交互硬规则 🔴

loop 在任何需要用户确认的地方，**必须且只能**使用以下交互方式：

1. **选择框交互**：使用 `AskUserQuestion` 工具，以选项列表呈现
2. **推荐项必标注**：第一个选项为推荐项，标注 `(推荐)`，描述中说明推荐理由
3. **其他选项必说明**：每个非推荐选项的描述中说明不推荐或需谨慎的理由
4. **禁止自由文本输入**：不允许要求用户"直接回车"、"输入数字"、"输入你的想法"等开放式交互
5. **禁止开放式追问**：不允许"你觉得呢？"、"还需要什么？"等需要用户组织语言回答的提问

违反以上任何一条 → 视为阻塞 Bug，必须自愈修复。

## 核心原则（两种模式通用）

1. **断点续跑**：状态文件持久化，中断后可恢复
2. **门禁矩阵不可跳过**：G1-G8+F1-F5，每个 ❌ 必须进自愈闭环
3. **不降级红线**：禁止静默删减功能、降低验收标准
4. **Git 隔离不妥协**：遵循 using-git-worktrees，保护主分支
5. **验证证据标准化**：可复现、有数据、有对比、可追溯
6. **每轮输出结构化门禁报告**：含每维度通过/失败状态和自愈处置
7. **新增文件自动 git add + commit，不 push**
8. **合并需用户确认**（--auto 模式除外）

## 流程详情

- **纯自动模式**: `references/mode-auto.md`
- **默认模式**: `references/mode-default.md`
- **A+D 引擎**: `references/acceptance-inference.md`

## 共享组件

| 组件 | 文件 | 内容 |
|------|------|------|
| 门禁矩阵 | `references/gate-matrix.md` | G0-G8+F1-F5 维度定义、启用规则、报告格式 |
| 自愈闭环 | `references/self-healing.md` | A/B/C/🎨 分级触发、阻塞保护、exhausted 终态 |
| 前端验证协议 | `references/frontend-verification.md` | 四阶段验证、@ref 规则、agent-browser MCP 工具表 |
| **环境配置** | `references/agent-browser-setup.md` | agent-browser 安装、MCP 配置、G0 预检、故障排查 |
| 经验库协议 | `references/experience-library.md` | 注入时机、匹配规则、沉淀时机、维护规则 |
| 状态管理 | `references/state-protocol.md` | .loop-state-*.json 格式、断点恢复、并发检测 |

## 环境前置（G0 门禁）

涉及前端验证（F1-F5）的任务，**必须**先确保 agent-browser 环境就绪：

```bash
bash skills/loop/scripts/check-agent-browser.sh
```

预检通过（exit 0）→ 继续；失败（exit 1）→ 阻塞，按提示修复后重跑。
详见 `references/agent-browser-setup.md`。

## 与其他命令的区别

| 命令 | 适用场景 |
|------|----------|
| `/loop 功能 条件` | 端到端新功能开发，有明确验收标准 |
| `/loop --auto 功能` | go 编排子任务，或确定需求的快速执行 |
| brainstorming | 纯需求探索，不写代码 |

# loop --auto 纯自动模式

loop --auto 供 go 编排层调用或用户明确选择时使用。全程审计闸门，不等用户确认。

## 触发条件
- `/loop --auto 功能描述，验收条件`
- go 编排层通过宿主 CLI 调用时注入 "加载 loop 技能（--auto 模式）"

## 执行流程

```
loop --auto 触发
    │
    ▼
Step ⓪ 断点续跑
  • 检查 .loop-state-<分支slug>.json
  • 存在且未完成 → 自动续跑
  • 不存在 → 进入 Step ①
    │
    ▼
Step ① 上下文注入（不重新扫描）
  • 如果被 go 调用,上下文已在 prompt 中:
    - 项目技术栈、已有模块、前置任务产物指针
    - 验收条件
  • 无需重复 6D 分析,直接使用已有上下文
    │
    ▼
Step ②-③ 复杂度评估 + 计划拆分
  • 如果被 go 调用,L2/L3 级别已确定
  • 否则自动评估: 需求清晰→🟡标准,复杂→🔴完整
  • 自动拆分(不需要用户确认轮次)
    │
    ▼
Step ④ Git 隔离（自动 · 上下文感知）
  • 检测: 当前分支是否以 "go-" 开头?
    ├─ 是 → 已处于 go 编排层的 worktree 中
    │       跳过创建,复用已有隔离环境
    │       (go 已保证主分支不受影响)
    └─ 否 → 独立执行,创建 loop/<功能slug>-<MMDD> 分支
            遵循 using-git-worktrees 技能
            主分支不受影响
    │
    ▼
Step ⑤ 闭环编码（纯自动）
  每 Round = Implement → GitCheck → 门禁矩阵 → 自愈 → Decide
  
  • Implement: clean-code + testing-patterns + 领域技能
  • GitCheck: 自动 git add + commit
  • 门禁矩阵: 全维度启用（见 references/gate-matrix.md）
  • 自愈闭环: 自动修复失败门禁（见 references/self-healing.md）
  
  Decide:
    ✅ 门禁全绿 → success，进入 Step ⑤.5 验证官
    🟡 连续2轮无进展 → stagnated，返回给 go（被调用时）或自动降级
    🔴 exhausted（默认4轮×1.5=6轮）→ 返回给 go 或自动终止
    │
    │
Step ⑤.5 验证官独立验证（🆕 v6.12 · 三层防御 B 层）
  门禁全绿后，派 verification-officer subagent 做独立验证：
  • 不复用 implementer 上下文，从零验证（解决利益冲突）
  • 按 task_type 路由：frontend→F1-F5 / api→curl / backend→测试+红绿 / script→裸命令
  • 验证官写 .verify-state/<SID>/verdict.json
  • 返回 4 状态：VERIFIED / FAILED / BLOCKED / NEEDS_CONTEXT

  判定:
    ✅ VERIFIED → 进入 Step ⑥ 交付
    ❌ FAILED → 回到 Step ⑤ 自愈（修代码后重派验证官）
    ⛔ BLOCKED → 返回给 go（环境问题，非代码）
    ❓ NEEDS_CONTEXT → AskUserQuestion 问用户验证方式
    │
    │
Step ⑥ 交付（📝审计闸门）
  • 门禁全绿 → 自动合并到 go 工作树（被调用时）
  • 独立执行 → 自动合并到主分支
  • 生成门禁报告摘要 → 回写 go 的 handoff.gate_result
  • 经验沉淀到 loop-library（自愈成功时）
  • 清理 .loop-state-*.json
    │
    ▼
✅ 完成 → 返回结果给 go 或用户
```

## Token 优化（编码前自动执行）

loop --auto 内建 Token 优化机制，按需使用：

| 时机 | 工具 | 用途 |
|------|------|------|
| 开始编码前 | Repomix(CLI) | 打包相关模块目录，获取代码结构 |
| 编码中取码 | jCodeMunch(MCP) | 按符号精准获取代码（不读全文件） |
| 工具输出 | Headroom | 压缩大段工具输出后喂 LLM |

**原则**: 按需拉取，不预打包全量。被 go 调用时优先用注入的上下文，减少重复扫描。

## 降级返回（供 go 判断）

loop --auto 被 go 调用时，异常状态返回给 go 做降级决策：

```json
// 成功
{"status": "ok", "commit_sha": "abc123", "gate_result": {"G4":"85%","G5":"2xx"} }

// 需要降级
{"status": "exhausted", "blockers": ["G5: 500 @POST /api/points"], "attempts": 6}

// 阻塞
{"status": "stagnated", "blockers": ["G1: DB不可达"], "attempts": 2}
```

go 收到 exhausted/stagnated → 降级到 Secondary Tier 直连或 Tertiary Tier。

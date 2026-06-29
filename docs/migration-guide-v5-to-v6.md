# Skill-Hub v5 → v6 迁移指南

> LoopEngine 1.0.2+ 启用 skill-hub v6.0 复合任务编排能力。
> **v5.4 单技能路由 100% 保留，零迁移成本。**

## 升级方式

### 一键升级（推荐）

```bash
cd "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"
git pull
bash scripts/zcode-mcp-ensure.sh
```

### 验证升级

```bash
# 1. 检查 skill-hub 版本
grep "version:" skills/skill-hub/SKILL.md | head -3
# Expected: version: "6.0"

# 2. 检查 references 是否齐全
ls skills/skill-hub/references/
# Expected: composite-task-types.md, complexity-evaluator.md, orchestrator-protocol.md, trace-format.md
```

## 新功能启用（opt-in）

v6.0 alpha 阶段默认关闭 Orchestrator，需显式启用：

```bash
# Linux/macOS
export LOOPENGINE_ORCHESTRATOR=alpha

# Windows PowerShell
$env:LOOPENGINE_ORCHESTRATOR = "alpha"
```

## 回滚方式

任何时候可回滚到 v5.4 行为：

```bash
# 关闭 Orchestrator
export LOOPENGINE_ORCHESTRATOR=off

# 或回滚到 v5.4 备份
cd skills/skill-hub
cp SKILL.md.v5.4.backup SKILL.md
```

## 向后兼容保证

| 现有 v5.4 行为 | v6.0 行为 | 兼容性 |
|--------------|---------|:---:|
| 单技能路由 | 同 v5.4 | 100% |
| 冲突裁决 | 同 v5.4 | 100% |
| 语义兜底 | 同 v5.4 | 100% |
| MCP 红线规则 | 同 v5.4 | 100% |
| 4 项用户交互红线 | 同 v5.4 | 100% |

## 已知限制（alpha 阶段）

- 复合任务识别仅支持 5 类预设（用户可显式 `/composite` 覆盖）
- Orchestrator 调度的 trace 暂仅记录到本地日志，不上传
- 5 类之外的复合任务需 Phase 2 扩展

## 反馈渠道

- 提交 issue：GitHub loop_engineering repo
- 启用 trace 后附上 trace_id（`/trace <id>` 查看）

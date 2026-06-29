# LoopEngine v6.0 → v6.1 迁移指南（2026-06-29）

> **本指南**：帮助用户从 v6.0 平滑升级到 v6.1。
> **核心变化**：skill-hub v6.1 三技能协同契约 + shared/ 抽取 + subagent-dd 桥接 opt-in。

---

## 1. 升级前检查

### 1.1 环境变量

```bash
# 检查当前 skill-hub 版本
cat ~/.agents/skills/skill-hub/SKILL.md | head -10 | grep version
# 期望输出: version: "6.0"
```

### 1.2 既有配置文件

| 文件 | 状态 | 升级动作 |
|------|------|---------|
| `~/.zcode/cli/config.json` | ✅ 不动 | 无需修改 |
| `~/.zcode/cli/plugins/marketplaces/*/marketplace.json` | ✅ 不动 | 无需修改 |
| `~/.zcode/cli/plugins/cache/.../loopengine/1.0.1/.zcode-plugin/plugin.json` | ✅ 不动 | 无需修改 |
| `tests/golden-traces/v54-baseline.json` | ✅ 不动 | 黄金轨迹 100% 保留 |
| 既有 `.orchestrate-state.json` | ✅ 不动 | 字段格式 100% 保留 |
| 既有 `.loop-state-*.json` | ✅ 不动 | 字段格式 100% 保留 |

---

## 2. 升级步骤

### 2.1 标准升级（推荐）

```bash
# 1. 拉取最新代码
cd /path/to/loop_engineering
git pull origin main

# 2. 同步到 ZCode CLI 缓存
bash scripts/zcode-mcp-ensure.sh

# 3. 验证版本
cat skills/skill-hub/SKILL.md | head -10 | grep version
# 期望输出: version: "6.1"

# 4. 运行回归测试（可选但推荐）
python tests/test-shared-modules.py
python tests/test-bridges.py
python tests/test-dispatch-regression.py

# 5. 完成
echo "✅ v6.1 升级完成"
```

### 2.2 离线升级

如无网络访问：

```bash
# 1. 从备份恢复
cp -r /backup/loop_engineering_v61/* /path/to/loop_engineering/

# 2. 同步插件
bash scripts/zcode-mcp-ensure.sh

# 3. 验证（同上）
```

### 2.3 容器/Docker 升级

```dockerfile
# Dockerfile 修改
FROM loopengine:v6.0
COPY --chown=loop:loop skills /opt/loopengine/skills
RUN bash /opt/loopengine/scripts/zcode-mcp-ensure.sh
# 验证
RUN python /opt/loopengine/tests/test-dispatch-regression.py
```

---

## 3. 行为变化

### 3.1 默认行为（100% 不变）

| 场景 | v6.0 行为 | v6.1 行为 | 变化 |
|------|----------|----------|:----:|
| `/loop 实现分页` | loop 单技能路由 | loop 单技能路由 | ❌ 无 |
| `/go 实现订单管理` | go 单技能路由 | go 单技能路由 | ❌ 无 |
| "审查系统" | system-review | system-review | ❌ 无 |
| "并行调研 A、B、C" | subagent-dd | subagent-dd | ❌ 无 |
| v5.4 黄金轨迹 27 条 | 100% 命中 | 100% 命中 | ❌ 无 |
| 既有 .orchestrate-state.json | 可正常加载 | 可正常加载 | ❌ 无 |
| 既有 .loop-state-*.json | 可正常加载 | 可正常加载 | ❌ 无 |

### 3.2 新增能力（opt-in）

| 能力 | 启用方式 | 默认状态 |
|------|---------|:-------:|
| 三技能协同契约（显式决策树） | skill-hub 自动 | ✅ 启用 |
| 6 组冲突裁决句式补全 | skill-hub 自动 | ✅ 启用 |
| shared/ 共享基础设施 | 自动加载 | ✅ 启用 |
| subagent-dd 桥接 G9/G10 | `LOOPENGINE_BRIDGES=alpha --reviewer=subagent-dd` | 🟡 需 opt-in |

### 3.3 新增失败模式

| 失败 | 行为 | 降级 |
|------|------|------|
| bridge 未启用（`disabled`） | 不加载 bridges/ | 走原 G9/G10 |
| `dispatch_*` 抛异常 | 记录 `bridge_error` | 降级到原 G9/G10 |
| `dispatch_implementer` BLOCKED | 记录 `degraded_reason` | 降级到原 G9/G10 |
| `dispatch_spec_reviewer` 持续 ❌ | 记录 `specs_stuck=true` | 降级到原 G9/G10 |
| `dispatch_code_quality_reviewer` Critical | 阻塞 + 自愈 | 不降级（自愈后继续） |

---

## 4. 新增 API（不破坏既有 API）

### 4.1 shared/ 共享 Python API

```python
# 原子写
from shared.scripts.atomic_write import atomic_write_json, atomic_read_json

# owner 字段（go + loop 共享）
owner = {
    "pid": os.getpid(),
    "session_id": "sess_xxx",
    "heartbeat": datetime.now().isoformat(),
    "started_at": datetime.now().isoformat(),
}
```

### 4.2 bridges/ 桥接 API（opt-in）

```python
# 默认禁用
from subagent_driven_development.bridges.contract import (
    is_bridge_enabled,  # 返回 False
    dispatch_implementer,  # 抛 NotImplementedError
)

# opt-in 启用
import os
os.environ["LOOPENGINE_BRIDGES"] = "alpha"
# 重新导入
import importlib
import subagent_driven_development.bridges.contract
importlib.reload(subagent_driven_development.bridges.contract)
from subagent_driven_development.bridges.contract import (
    is_bridge_enabled,  # 返回 True
    dispatch_implementer,  # 可调用（alpha 阶段抛 NotImplementedError，需生产实现）
)
```

---

## 5. 环境变量变化

| 变量 | v6.0 | v6.1 | 备注 |
|------|------|------|------|
| `LOOPENGINE_ORCHESTRATOR` | alpha / off | alpha / off | ❌ 无变化 |
| `LOOPENGINE_BRIDGES` | （无） | alpha / disabled | 🆕 新增，默认 disabled |

---

## 6. 配置文件变化

### 6.1 frontmatter 变化

| 文件 | v6.0 | v6.1 |
|------|------|------|
| `skills/skill-hub/SKILL.md` | `version: "6.0"` | `version: "6.1"` + `base_compat_v6: "6.0"` + `bridges_env` |
| `skills/subagent-driven-development/SKILL.md` | 无 metadata | +5 字段（`version`/`type`/`mode`/`bridgeable_contracts`/`bridge_env`） |

### 6.2 既有 .orchestrate-state.json 字段

**100% 保留**（无需迁移）：

```json
{
  "orchestrate_id": "go/xxx",
  "feature": "...",
  "tier": "L1",
  "status": "in_progress",
  "acceptance_criteria": [...],
  "tasks": [...],
  "feature_branch": "go/xxx",
  "base_branch": "main",
  "owner": {...},
  "decision_log": [...],
  "created_at": "...",
  "updated_at": "..."
}
```

### 6.3 既有 .loop-state-*.json 字段

**100% 保留**（无需迁移）：

```json
{
  "loop_id": "loop/xxx",
  "feature": "...",
  "mode": "🤖 auto",
  "auto_mode": true,
  "current_step": "...",
  "current_round": 1,
  "total_rounds": 3,
  "acceptance_criteria": [...],
  "task_list": [...],
  "blockers": [],
  "last_error": "",
  "verification_evidence": {},
  "last_commit_sha": "...",
  "owner": {...},
  "decision_log": []
}
```

---

## 7. 测试套件

### 7.1 新增测试

| 文件 | 测试数 | 覆盖 |
|------|:-----:|------|
| `tests/test-shared-modules.py` | 10 | atomic_write / owner / state-protocol / state_manager 集成 |
| `tests/test-bridges.py` | 18 | 6 桥接函数 + 3 dataclass + 灰度开关 |
| `tests/test-dispatch-regression.py` | 9 | v5.4 兼容 / v6.0 兼容 / 状态文件兼容 / 灰度开关 |
| **总计** | **37** | — |

### 7.2 黄金轨迹

| 文件 | 条数 | 用途 |
|------|:---:|------|
| `tests/golden-traces/v54-baseline.json` | 27 | v5.4 兼容基线（**不动**） |
| `tests/golden-traces/v61-go-loop-subagent.json` | 30 | v6.1 三技能协同新基线 |

---

## 8. 故障排查

### 8.1 v5.4 黄金轨迹失败

**症状**：`test_v54_baseline_27_traces_unchanged` 失败

**原因**：v5.4 单技能路由被破坏

**解决**：
1. 检查 `skills/skill-hub/SKILL.md` frontmatter `base_compat: "5.4"` 是否存在
2. 检查是否有未授权的 §三技能协同契约 修改（应只追加，不修改）
3. 回滚：`git checkout v6.0 -- skills/skill-hub/SKILL.md`

### 8.2 状态文件加载失败

**症状**：`read_state()` 报 `KeyError` 或 `JSONDecodeError`

**原因**：状态文件被破坏或字段不兼容

**解决**：
1. 检查 `owner` 字段是否含 `pid/session_id/heartbeat/started_at` 4 字段
2. 检查 `decision_log` 字段是否为 list
3. 用 `safe_load_state(path, default={})` 加载（v6.1 新增 API）

### 8.3 桥接不生效

**症状**：`LOOPENGINE_BRIDGES=alpha` 但 `is_bridge_enabled()` 返回 False

**原因**：环境变量未正确传递到 Python 进程

**解决**：
1. 确认 `export LOOPENGINE_BRIDGES=alpha`（不是 `set`）
2. 重启 ZCode 会话（环境变量只在会话启动时加载）
3. 在 Python 中验证：`os.environ.get("LOOPENGINE_BRIDGES")`

### 8.4 subagent-dd 桥接返回 NotImplementedError

**症状**：`dispatch_implementer` 抛 `NotImplementedError`

**原因**：alpha 阶段桥接组件未实现真实派遣逻辑

**解决**：
1. 确认是预期行为（alpha 阶段不阻塞）
2. 等待生产实现（参见 `bridges/dispatcher.md §3 契约`）
3. 或降级到原 G9/G10（`LOOPENGINE_BRIDGES=disabled`）

---

## 9. 回滚预案

### 9.1 关闭桥接

```bash
export LOOPENGINE_BRIDGES=disabled
# 行为回到 v6.0（loop/go 默认 G9/G10 不变）
```

### 9.2 关闭 Orchestrator

```bash
export LOOPENGINE_ORCHESTRATOR=off
# 行为回到 v5.4（单技能路由）
```

### 9.3 完整回滚到 v6.0

```bash
cd /path/to/loop_engineering
git checkout v6.0 -- skills/
bash scripts/zcode-mcp-ensure.sh
```

---

## 10. 升级后验证清单

- [ ] `cat skills/skill-hub/SKILL.md | grep version` → `version: "6.1"`
- [ ] `python tests/test-shared-modules.py` → 10/10 通过
- [ ] `python tests/test-bridges.py` → 18/18 通过
- [ ] `python tests/test-dispatch-regression.py` → 9/9 通过
- [ ] 既有 `/loop` 命令行为不变
- [ ] 既有 `/go` 命令行为不变
- [ ] 既有 .orchestrate-state.json 仍可加载
- [ ] 既有 .loop-state-*.json 仍可加载
- [ ] `LOOPENGINE_BRIDGES=disabled` 时 go/loop 行为 100% 不变
- [ ] `LOOPENGINE_BRIDGES=alpha` + `--reviewer=subagent-dd` 时 G9/G10 桥接生效

---

## 11. 升级后增强（opt-in）

### 11.1 启用 subagent-dd 桥接 G10

```bash
export LOOPENGINE_BRIDGES=alpha
/go --reviewer=subagent-dd 实现订单管理功能
# G10 = subagent-dd final reviewer（3 层问题分级）
```

### 11.2 启用 subagent-dd 桥接 G9

```bash
export LOOPENGINE_BRIDGES=alpha
/loop --reviewer=subagent-dd 实现分页功能
# G9 = subagent-dd 三阶段循环
# （implementer → spec → code quality）
```

### 11.3 关闭桥接

```bash
unset LOOPENGINE_BRIDGES
# 或
export LOOPENGINE_BRIDGES=disabled
```

---

## 12. 联系与反馈

- **设计文档**：`docs/2026-06-29-skill-hub-v6.1-design.md`
- **实施计划**：`docs/2026-06-29-skill-hub-v6.1-plan.md`
- **v6.0 设计**：`docs/2026-06-29-skill-hub-v6-design.md`（用于回溯对照）
- **v5 → v6 迁移**：`docs/migration-guide-v5-to-v6.md`（v6.1.1 已删除 — 历史归档，v5.4 → v6 行为由 v5.4 backup + golden-traces 持续保护）

---

## 13. 总结

v6.0 → v6.1 是**纯增量**升级：
- ✅ 17 个新文件，9 个修改文件
- ✅ 0 个被破坏的兼容接口
- ✅ 37/37 测试通过
- ✅ 30 条新黄金轨迹
- ✅ 默认行为 100% 不变
- ✅ 桥接 opt-in，零风险启用

升级过程仅需 `git pull` + `bash scripts/zcode-mcp-ensure.sh` + 跑 3 个测试套件，**总耗时 < 10 分钟**。

# 双轨制状态文件协议(机制④)

> 编排层用 `.orchestrate-state.json` 管**宏观调度**;每个子任务内部复用 loop 的 `.loop-state-*.json` 管**微观闭环**。两层职责清晰,互不污染。

---

## 设计原则

| 层级 | 文件 | 职责 | 谁读写 |
|------|------|------|--------|
| **宏观调度层** | `.orchestrate-state.json` | 哪些子任务/分给谁/依赖关系/断点/降级标记 | 编排层 |
| **微观闭环层** | `.loop-state-*.json`(复用loop) | 单子任务内部的门禁/迭代/经验 | loop 技能 |

编排层**只读写宏观状态**,不碰微观状态。子任务派发给 loop 时,loop 自行管理其 `.loop-state` 文件。

---

## 宏观状态文件: `.orchestrate-state.json`

- **存放位置**: 项目根目录(与 `.loop-state-*.json` 同级)
- **文件名**: 固定 `.orchestrate-state.json`(单编排任务,非按分支区分)
- **清理时机**: 编排任务完成(合并/丢弃)后自动删除

### JSON Schema

```json
{
  "orchestrate_id": "orch/points-0626",
  "feature": "用户积分系统",
  "tier": "L3",
  "status": "in_progress",
  "acceptance_criteria": [
    {"id": 1, "text": "覆盖率>=80%", "source": "auto", "passed": false},
    {"id": 2, "text": "积分累积正确", "source": "user", "passed": false}
  ],
  "tasks": [
    {
      "id": "T1",
      "name": "数据库表设计",
      "assigned_tool": "zcode",
      "depends_on": [],
      "status": "completed",
      "skill_injected": "database-design",
      "git_head_before": "abc1234",
      "git_commit_after": "def5678",
      "handoff": {
        "files_changed": ["app/models/points.py", "migrations/019_points.sql"],
        "new_interfaces": [
          {"type": "table", "name": "points", "columns": ["user_id", "amount", "reason"]}
        ],
        "artifacts": "数据库迁移已完成,points 表就绪",
        "git_commit": "def5678",
        "gate_result": {
          "G4": "✅ 85%覆盖率",
          "G5": "✅ 全部2xx",
          "F1": "✅ 0错误"
        },
        "next_task_hint": "T2 可基于 points 表开发累积/兑换API"
      },
      "degraded": false,
      "degraded_reason": null,
      "original_model": null,
      "actual_model": null
    },
    {
      "id": "T2",
      "name": "积分累积/兑换API",
      "assigned_tool": "zcode",
      "depends_on": ["T1"],
      "status": "pending",
      "skill_injected": "api-design-principles",
      "git_head_before": null,
      "git_commit_after": null,
      "handoff": null,
      "degraded": false,
      "degraded_reason": null,
      "original_model": null,
      "actual_model": null
    }
  ],
  "owner": {
    "pid": 0,
    "session_id": "",
    "started_at": "2026-06-26T12:00:00Z",
    "heartbeat": "2026-06-26T12:30:00Z"
  },
  "created_at": "2026-06-26T12:00:00Z",
  "updated_at": "2026-06-26T12:30:00Z",
  "decision_log": []
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `orchestrate_id` | string | 编排任务唯一ID,格式 `orch/<feature-slug>-<MMDD>` |
| `feature` | string | 功能描述 |
| `tier` | enum | `L1` / `L2` / `L3` 执行级别 |
| `status` | enum | `planning` / `in_progress` / `completed` / `failed` / `paused` |
| `acceptance_criteria[]` | array | 验收条件清单 |
| `acceptance_criteria[].source` | enum | `auto`(自动推理) / `user`(用户指定) |
| `acceptance_criteria[].passed` | boolean | 是否已通过 |
| `tasks[]` | array | 子任务列表(拓扑序) |
| `tasks[].assigned_tool` | enum | `zcode` / `cursor` / `trae` / `deepseek` |
| `tasks[].depends_on` | array | 依赖的子任务ID列表(空=无依赖,可并发) |
| `tasks[].status` | enum | `pending` / `in_progress` / `completed` / `failed` / `skipped` |
| `tasks[].skill_injected` | string | 注入的 skill-hub 技能名(机制②) |
| `tasks[].git_head_before` | string | 任务开始前的 git HEAD(**原子性回滚用**) |
| `tasks[].git_commit_after` | string | 任务完成后的 commit SHA |
| `tasks[].handoff` | object | 上下文交接摘要(机制⑥,详见 handoff-protocol.md); **新增 gate_result 字段**: loop --auto 完成后回写的门禁矩阵通过情况, 供 go 做降级决策和质量分层 |
| `tasks[].degraded` | boolean | 是否降级执行(**透明化标记**) |
| `tasks[].degraded_reason` | string\|null | 降级原因(如 `quota_exhausted`) |
| `tasks[].original_model` | string\|null | 原计划模型(如 `glm-5.2`) |
| `tasks[].actual_model` | string\|null | 实际使用模型(如 `deepseek-chat`) |
| `owner` | object | 并发占用(借鉴 loop 的 heartbeat 设计) |
| `decision_log[]` | array | 阻塞后的决策记录(可追溯) |

---

## 读写规范

### 写入(检查点机制)

**每次状态变更立即写盘**,防中断丢失。写入用**原子操作**:

```python
# 伪代码: 原子写入防损坏
import json, tempfile, os
def write_state(state, path):
    # 写临时文件
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    # 原子rename(Windows下用os.replace)
    os.replace(tmp, path)
```

### 读取(一致性校验)

断点恢复时读取状态文件,做三项校验(借鉴 loop Step⓪):

1. **git HEAD 对比**: `git_head_before` vs 当前 HEAD,不一致→提示"断点后有外部改动"
2. **验收条件文件变更**: 验收条件涉及的文件是否被外部修改
3. **搁置时长**: `updated_at` 距今 >24h → 提示"搁置较久,复盘验收条件是否仍有效"

### 并发检测

状态文件含 `owner`(pid/session_id/heartbeat)字段:
- 启动时检测已有状态文件,按 heartbeat 判定:
  - heartbeat 距今 <5min → "他会在跑",提示 [接管/另起/取消]
  - heartbeat ≥5min → "前会话僵死",自动接管

---

## 微观状态文件: `.loop-state-*.json`

完全复用 loop 技能的格式,**编排层不修改**。

- 每个子任务派发给 loop 执行时,loop 自己管理其 `.loop-state-<分支slug>.json`
- 编排层只读取宏观状态,不碰微观状态
- 子任务完成后,loop 的状态文件由 loop 自行清理

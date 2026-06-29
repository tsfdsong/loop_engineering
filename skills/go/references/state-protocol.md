# 状态文件协议 v3.1 — Worktree 单轨制

> 编排层用 `.orchestrate-state.json` 管**宏观调度**(子任务 DAG + worktree 分支)。
> loop 在 go 提供的 worktree 内执行,复用已有隔离,**不创建嵌套分支**。

---

## 设计原则

| 层级 | 文件 | 职责 | 谁读写 |
|------|------|------|--------|
| **编排层** | `.orchestrate-state.json` | 子任务 DAG/worktree 分支/断点/降级标记 | go 编排层 |
| **执行层** | `.loop-state-*.json`(复用 loop) | 单任务内部门禁/迭代/经验 | loop 技能 |

编排层只读写宏观状态。loop 在 worktree 目录内创建自己的 `.loop-state`，worktree 清理时自动消失。

---

## 宏观状态文件: `.orchestrate-state.json`

- **存放位置**: 项目根目录(feature 分支上)
- **文件名**: 固定 `.orchestrate-state.json`
- **清理时机**: 编排任务完成(合并/丢弃)后自动删除

### JSON Schema

```json
{
  "orchestrate_id": "go/points-0628",
  "feature": "用户积分系统",
  "tier": "L3",
  "status": "in_progress",
  "feature_branch": "go-points-0628",
  "base_branch": "main",
  "acceptance_criteria": [
    {"id": 1, "text": "覆盖率>=80%", "source": "auto", "passed": false}
  ],
  "tasks": [
    {
      "id": "T1",
      "name": "数据库表设计",
      "assigned_tool": "zcode",
      "depends_on": [],
      "status": "completed",
      "skills": ["database-design"],
      "files": ["app/models/points.py", "migrations/019_points.sql"],
      "git_head_before": "abc1234",
      "git_commit_after": "def5678",
      "commit_sha": "def5678",
      "handoff": {
        "files_changed": ["app/models/points.py"],
        "new_interfaces": [{"type": "table", "name": "points"}],
        "artifacts": "数据库迁移已完成",
        "next_task_hint": "T2 可基于 points 表开发 API"
      },
      "degraded": false,
      "degraded_reason": null,
      "actual_model": "deepseek-v4-pro"
    }
  ],
  "owner": {"pid": 0, "session_id": "", "started_at": "", "heartbeat": ""},
  "created_at": "2026-06-28T12:00:00Z",
  "updated_at": "2026-06-28T12:30:00Z",
  "decision_log": []
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `orchestrate_id` | string | 编排任务唯一ID,格式 `go/<feature-slug>-<MMDDHHMM>` |
| `feature_branch` | string | go 创建的 feature 分支名(断点恢复用) |
| `base_branch` | string | 从哪个分支切出(回滚用) |
| `tier` | enum | `L1` / `L2` / `L3` 执行级别 |
| `status` | enum | `planning` / `in_progress` / `completed` / `failed` / `paused` |
| `tasks[].assigned_tool` | enum | `zcode` / `deepseek` (已移除 cursor/trae) |
| `tasks[].depends_on` | array | 依赖的子任务ID列表(空=无依赖,可并发) |
| `tasks[].skills` | array | 子任务推荐的技能名列表 |
| `tasks[].files` | array | 子任务预期操作的文件列表(回归保护用) |
| `tasks[].status` | enum | `pending` / `in_progress` / `completed` / `failed` / `skipped` |
| `tasks[].git_head_before` | string | 任务开始前的 git HEAD(**原子性回滚用**) |
| `tasks[].git_commit_after` | string | 任务完成后的 commit SHA |
| `tasks[].commit_sha` | string | force_commit 返回的 SHA(强制提交保障) |
| `tasks[].handoff` | object | 上下文交接摘要(机制⑥) |
| `tasks[].degraded` | boolean | 是否降级执行(**透明化标记**) |
| `tasks[].degraded_reason` | string\|null | 降级原因(如 `quota_exhausted`) |
| `tasks[].actual_model` | string\|null | 实际使用模型 |
| `owner` | object | 并发占用(pid + session_id + heartbeat) |
| `decision_log[]` | array | 决策记录(可追溯) |

---

## 读写规范

### 写入(检查点机制)

**每次状态变更立即写盘**,防中断丢失。写入用**原子操作**:

```python
# 伪代码: 原子写入防损坏
import json, tempfile, os
def write_state(state, path):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
```

### 读取(一致性校验)

断点恢复时读取状态文件,做三项校验:

1. **git HEAD 对比**: `git_head_before` vs 当前 HEAD,不一致→提示"断点后有外部改动"
2. **feature_branch 存在性**: 分支不存在→提示"feature 分支已被删除"
3. **搁置时长**: `updated_at` 距今 >24h → 提示"搁置较久,复盘验收条件是否仍有效"

### 并发检测

状态文件含 `owner`(pid/session_id/heartbeat)字段:
- heartbeat 距今 <5min → "他会在跑",提示 [接管/另起/取消]
- heartbeat ≥5min → "前会话僵死",自动接管

---

## 微观状态文件: `.loop-state-*.json`

完全复用 loop 技能的格式,**编排层不修改**。

- loop 在 go 提供的 worktree 目录内创建 `.loop-state`
- worktree 清理时,`.loop-state` 自动随目录消失
- 编排层只读取宏观状态,不碰微观状态

---

## 🔗 v6.1 共享引用

> **v6.1 增强**：本文件中的 owner 字段定义、原子写算法、断点恢复协议已抽取到 `skills/shared/references/`，消除与 loop 技能的字段定义重复。

| 共享 spec | 替换原文件中的内容 | 详见 |
|----------|----------------|------|
| `shared/references/owner-field-spec.md` | 第 89 行（owner 字段描述）+ 第 120-122 行（并发检测规则） | owner 字段结构 `{pid, session_id, heartbeat, started_at}` + 5/30/24h 判定阈值 |
| `shared/references/atomic-write-spec.md` | 第 100-108 行（原子写伪代码） | tempfile + os.replace 算法 + 异常处理 |
| `shared/references/state-protocol-base.md` | 第 17-25 行（状态机定义）+ 第 32-35 行（通用字段） | 5 状态机（planning/in_progress/completed/failed/paused）+ 通用字段（id/feature/status/owner/decision_log） |
| `shared/references/breakpoint-recovery-base.md` | `breakpoint-recovery.md` 全文 | 三步骤协议（一致性校验 → 搁置时长 → 状态定位） |
| `shared/references/g9-g10-coordination.md` | SKILL.md 第 32 行（G9/G10 职责） | G9 = loop 单次提交审查 / G10 = go 累积分支审查 |

**Python 实现**：`scripts/state_manager.py` 已迁移到 `shared/scripts/atomic_write.py`（v6.1 改造完成，API 100% 兼容）。

**向后兼容**：本文件原有内容**全部保留**，共享 spec 是**增量引用**而非修改。

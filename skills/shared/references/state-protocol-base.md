# 状态文件通用规范（v6.1 共享 spec · 中优先级）

> **来源**：从 `skills/go/references/state-protocol.md`（131 行）+
> `skills/loop/references/state-protocol.md`（76 行）抽取通用字段。
> **抽取原因**：两份 state-protocol 字段集不重叠但 schema 哲学相同（状态机/owner/decision_log），
> 抽出通用规范供两边各自引用。

## 状态机定义

```
planning ──→ in_progress ──→ completed
                  │
                  ├──→ failed
                  │
                  ├──→ paused ──→ (resume) ──→ in_progress
                  │
                  └──→ (timeout) ──→ failed
```

| 状态 | 含义 | 终态？ |
|------|------|:------:|
| `planning` | 规划阶段，尚未开始执行 | ❌ |
| `in_progress` | 执行中 | ❌ |
| `completed` | 正常完成 | ✅ |
| `failed` | 失败终态 | ✅ |
| `paused` | 暂停（可 resume） | ❌ |

## 通用字段

| 字段 | 类型 | 必填 | 适用 |
|------|------|:----:|------|
| `id` | string | ✅ | go: `orchestrate_id` / loop: `loop_id` |
| `feature` | string | ✅ | 任务功能描述 |
| `status` | enum | ✅ | 见上表 |
| `decision_log[]` | array | ✅ | 决策记录（自动追加，永不删除） |
| `owner` | object | ✅ | 并发占用控制（详见 `owner-field-spec.md`） |
| `created_at` | string (ISO8601) | ✅ | 创建时间 |
| `updated_at` | string (ISO8601) | ✅ | 最后更新时间 |

## 双轨制字段（各自定义，不合并）

| 抽象层 | 状态文件 | 字段集 |
|--------|---------|--------|
| **宏观**（go） | `.orchestrate-state.json` | 通用字段 + tasks[] (含 git_head_before, commit_after, handoff, degraded) + feature_branch, base_branch, tier |
| **微观**（loop） | `.loop-state-<slug>.json` | 通用字段 + current_step, current_round, total_rounds + task_list[] (id/name/status) + auto_mode, blockers[], verification_evidence |

**铁律**：两份文件的**字段集不重叠**，仅共享通用字段（id/feature/status/decision_log/owner），
不合并为统一状态文件（合并会破坏分层设计）。

## decision_log 规范

```json
{
  "decision_log": [
    {
      "timestamp": "2026-06-29T12:34:56+08:00",
      "step": "go.Step①.5",
      "decision": "推荐方案 A",
      "rationale": "基于 6 维度分析，方案 A 复用现有 points 表",
      "alternatives_considered": ["方案 B：新建独立模块"]
    }
  ]
}
```

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `timestamp` | ✅ | 决策时间 |
| `step` | ✅ | 决策来源（go.Step①.5 / loop.mode-auto.Step② 等） |
| `decision` | ✅ | 决策内容 |
| `rationale` | ✅ | 决策理由 |
| `alternatives_considered` | 🟡 | 备选方案（不强制） |

## 写入规范

- 状态文件写入必须用 `atomic_write_json`（详见 `atomic-write-spec.md`）
- `updated_at` 每次写入自动更新
- `decision_log` 只追加，不修改/删除

## 兼容性

- ✅ 既有 .orchestrate-state.json / .loop-state-*.json 字段格式 100% 保留
- ✅ 加载逻辑不变（仅 spec 文档级共享，不改运行时行为）

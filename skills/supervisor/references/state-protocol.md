# State Protocol — `.supervisor-state.json` 完整 Schema

> supervisor 与 go 主流程通过状态文件通信（无 IPC · 无 socket · 纯文件）。

## 文件位置

- 路径：`<session_root>/.supervisor-state.json`
- session_root = go 启动 supervisor 时传入的 `--session-root`
- 通常 = 主 worktree 根目录

## 完整 Schema

```json
{
  "version": "1.0",
  "session_id": "<go-session-id>",
  "started_at": "2026-07-17T10:00:00Z",
  "last_update": "2026-07-17T10:15:30Z",
  "tasks": [
    {
      "id": "T1",
      "worktree": "../wt-T1",
      "status": "running",
      "last_update": "2026-07-17T10:15:00Z",
      "interventions": ["R1×1", "R1×2"],
      "degraded": false,
      "r1_count": 2,
      "r2_count": 0,
      "r3_count": 0,
      "r4_asked": false,
      "decision_log": []
    }
  ],
  "summary": {
    "total": 5,
    "done": 3,
    "running": 1,
    "stuck": 0,
    "exhausted": 0,
    "failed": 1,
    "r4_pending": false
  }
}
```

## 字段说明

### 顶层

| 字段 | 类型 | 说明 |
|---|---|---|
| version | string | schema 版本（当前 1.0） |
| session_id | string | go 会话 ID（关联 .go-session.json） |
| started_at | ISO 8601 | supervisor 启动时间 |
| last_update | ISO 8601 | 最后一次写入时间 |
| tasks | array | 各子任务状态 |
| summary | object | 汇总统计 |

### tasks[].status 状态机

```
        ┌──────────┐
        │ running  │◄──── 派发初始
        └────┬─────┘
             │
   ┌─────────┼─────────┐
   │         │         │
   ▼         ▼         ▼
┌──────┐ ┌────────┐ ┌──────┐
│stuck │ │exhausted│ │ done │
└──┬───┘ └────┬───┘ └──────┘
   │         │
   ▼         ▼
┌─────────────────┐
│ R1/R2/R3 干预    │
└────────┬────────┘
         │
   ┌─────┴─────┐
   ▼           ▼
┌──────┐   ┌──────┐
│ done │   │failed│ ──► R4 上报
└──────┘   └──────┘
```

状态定义：
- `running`：loop 正在执行
- `stuck`：检测到异常（门禁失败 · 等待干预）
- `exhausted`：loop 自愈预算耗尽
- `done`：子任务完成（通过所有门禁）
- `failed`：R1×2+R2×1 均失败（等待 R4）

### tasks[].interventions

数组 · 按时间顺序记录已执行的干预：
- `["R1×1"]` · `["R1×1", "R1×2"]` · `["R1×2", "R2×1"]` · `["R3"]`

### tasks[].decision_log

每次干预的详细记录（JSON 对象数组）· 见 intervention-strategies.md。

### summary

| 字段 | 说明 |
|---|---|
| total | 子任务总数 |
| done | 已完成 |
| running | 进行中 |
| stuck | 卡住 |
| exhausted | 自愈耗尽 |
| failed | 已失败（等 R4） |
| r4_pending | 是否有未应答的 R4 |

## 通信时序

```
go                    supervisor
 │                         │
 │── dispatch tasks ──────►│
 │                         │
 │   poll read state ◄─────│ write state
 │   poll read state ◄─────│ write state
 │                         │
 │   ◄── r4_pending=true ──│ （R4 触发）
 │                         │
 │── AskUserQuestion ─────►│ （用户回答后）
 │                         │
 │   poll read state ◄─────│ update task
 │                         │
 │   ◄── done==total ──────│
 │                         │
 │── merge ───────────────►│
```

## go 进入 merge 的条件

- `summary.done == summary.total`（全完成）
- 或 `summary.r4_pending == true` 且用户已应答所有 R4

## 写入原子性

- supervisor 写状态文件时**先写临时文件**（`.supervisor-state.json.tmp`）· 再 rename
- go 读时若遇到 `.tmp` · 忽略（只读正式文件）
- 避免读写竞争导致 JSON 解析失败

# Cursor Dispatch Bridge — go Worker Contract

> 当 `python orchestrator.py` 在 Cursor 环境子进程运行、无法直接调用 `Task` 工具时，
> `CursorSubagentAdapter` 通过文件队列桥接宿主 Cursor agent。

## 流程

```
orchestrator (subprocess)
    → CursorSubagentAdapter.execute(packet)
    → enqueue .go/dispatch/queue/<task_id>.*
    → stdout: GO_WORKER_DISPATCH_REQUEST {...}
    → poll .go/dispatch/results/<task_id>.result.json

hosting Cursor agent (同项目会话)
    → 读取 sentinel 或扫描 queue/*.request.json
    → Task(subagent) + prompt_path 内容
    → subagent 在 workspace.root 内执行
    → write_result → .go/dispatch/results/<task_id>.result.json

orchestrator
    → 收到 result → 继续 commit / merge
```

## 目录结构

```
.go/dispatch/
├── queue/
│   ├── T1.packet.json      # WorkerTaskPacket
│   └── T1.request.json     # 路径索引 + pending/completed
├── prompts/
│   └── T1.md               # Task subagent 提示词
└── results/
    └── T1.result.json      # WorkerResult（宿主 agent 写入）
```

## 宿主 Agent 操作清单

1. 发现 dispatch：stdout 含 `GO_WORKER_DISPATCH_REQUEST`，或扫描 `queue/*request.json` 中 `status=pending`
2. 读取 `prompt_path`，用 **Task** 工具派发 subagent（`generalPurpose` 或自定义 role）
3. 确保 subagent 仅在 `workspace_root` 内修改文件
4. 将 subagent 产出转为 `WorkerResult` JSON，写入 `result_path`

可用 CLI 辅助（项目根目录）：

```bash
python skills/go/scripts/cursor_dispatch_bridge.py write-result \
  --project . \
  --result-file path/to/result.json
```

## 环境变量

| 变量 | 值 | 行为 |
|------|-----|------|
| `LOOPENGINE_CURSOR_DISPATCH` | `auto`（默认） | Cursor 环境启用文件桥接 |
| | `file` | 强制启用 |
| | `off` | 禁用，返回 NEEDS_CONTEXT |
| `LOOPENGINE_GO_RUNTIME` | `cursor` | 使用 Cursor adapter |

## WorkerResult 最小示例

```json
{
  "contract_version": "1.0",
  "task_id": "T1",
  "status": "DONE",
  "handoff": {
    "files_changed": ["app/models/points.py"],
    "new_interfaces": [],
    "artifacts": "points model added",
    "next_task_hint": null
  },
  "runtime_meta": {
    "profile": "cursor",
    "execution_mode": "foreground_parallel",
    "degraded": false
  }
}
```

## 与 NEEDS_CONTEXT 的关系

- 桥接等待超时 → adapter 返回 `NEEDS_CONTEXT`，`error` 含 `packet_path` / `result_path`
- 宿主 agent 可异步补写 result 后，重跑该任务或调用 scheduler 续跑

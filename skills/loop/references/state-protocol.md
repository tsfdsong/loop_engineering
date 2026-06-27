# 状态文件协议（.loop-state-*.json）

loop 任务的状态持久化文件，支持断点续跑和并发保护。

## 文件命名

- 格式: `.loop-state-<分支slug>.json`
- slug = 分支名去掉 `loop/` 前缀，`/` → `-`
  - `loop/points-0624` → `.loop-state-points-0624.json`

## JSON Schema

```json
{
  "loop_id": "loop/points-0624",
  "feature": "用户积分系统",
  "mode": "🔴 完整",
  "auto_mode": false,
  "current_step": "⑥",
  "current_round": 2,
  "total_rounds": 4,
  "acceptance_criteria": [
    {"id": 1, "text": "覆盖率≥80%", "source": "自动推理", "status": "✅"},
    {"id": 2, "text": "积分累积正确", "source": "用户指定", "status": "❌"}
  ],
  "task_list": [
    {"id": 1, "name": "积分累积API", "status": "✅"},
    {"id": 2, "name": "积分兑换API", "status": "⏳"}
  ],
  "blockers": [],
  "last_error": "",
  "verification_evidence": {},
  "last_commit_sha": "",
  "owner": {
    "pid": 0,
    "session_id": "",
    "started_at": "",
    "heartbeat": ""
  },
  "decision_log": []
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `auto_mode` | boolean | 是否为 --auto 模式（决定是否跳过用户确认） |
| `current_round` | number | 当前轮次 |
| `total_rounds` | number | 总轮次（--auto 模式可能不存在） |
| `acceptance_criteria[].source` | enum | `自动推理` / `用户指定` |
| `acceptance_criteria[].status` | string | ✅/❌/⏳ |
| `owner` | object | 并发占用（pid + session_id + heartbeat） |

## 断点恢复（Step ⓪）

1. 读取状态文件，定位 current_step、last_commit_sha
2. **一致性校验**:
   a. git HEAD vs last_commit_sha → 不一致→"断点后有外部改动，重新确认范围"
   b. 验收条件文件是否被改 → 被改→重载，确认是否沿用旧判断
   c. 状态文件 mtime > 24h → "搁置较久，复盘验收条件是否仍有效"
3. 展示进度摘要 + 一致性校验结果
4. 校验通过→从断点继续；异常→先确认再继续
5. 恢复时不重新确认已通过闸门的内容

## 并发检测

- owner.heartbeat 距今 <5min → 判定他会在跑 → "任务可能正在另一会话运行 [1]强制接管 [2]另起 [3]取消"
- owner.heartbeat ≥5min → 判定僵死 → 自动接管

## 状态清理

- 任务完成后自动删除 `.loop-state-<分支slug>.json`
- 用户手动中断（Ctrl+C）时，状态文件保留
- `loop-screenshots/` 目录截图保留作为交付物

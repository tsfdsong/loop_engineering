# owner 字段规范（v6.1 共享 spec）

> **来源**：从 `skills/go/references/state-protocol.md` 第 89, 120-122 行 +
> `skills/loop/references/state-protocol.md` 第 34-39, 67-69 行抽取。
> **抽取原因**：两份文件 owner 字段**完全相同**，抽取后消除字段定义重复，确保未来不会漂移。

## 字段结构

```json
{
  "owner": {
    "pid": 12345,
    "session_id": "sess_abc123",
    "heartbeat": "2026-06-29T12:34:56+08:00",
    "started_at": "2026-06-29T12:30:00+08:00"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `pid` | int | ✅ | 当前进程 PID（POSIX 进程标识） |
| `session_id` | string | ✅ | 会话唯一 ID（用于跨进程追踪） |
| `heartbeat` | string (ISO8601) | ✅ | 最后心跳时间（用于判断是否存活） |
| `started_at` | string (ISO8601) | ✅ | owner 写入时间（用于计算搁置时长） |

## 心跳判定规则

| 当前时间 - heartbeat | 判定 | 处理 |
|---------------------|------|------|
| < 5 分钟 | 🟡 "他会在跑" | 警告，提示用户可能存在并发 |
| 5-30 分钟 | 🟠 "可能已死" | 自动接管（覆盖 owner） |
| > 30 分钟 | 🔴 "确认已死" | 自动接管 + 记录 takeover 事件到 decision_log |
| > 24 小时 | 🔴🔴 "搁置超 24h" | 触发搁置提示，询问用户是 resume 还是 reset |

## 双轨制应用

| 状态文件 | 抽象层 | owner 字段存放位置 |
|---------|--------|------------------|
| `.orchestrate-state.json`（go） | 宏观 | `owner` 顶级字段 |
| `.loop-state-<slug>.json`（loop） | 微观 | `owner` 顶级字段 |

两份文件 owner 字段**结构完全一致**，仅抽象层不同。

## 使用示例

详见 `examples/owner-usage.md`。

## 兼容性

- ✅ v5.4 owner 字段 100% 兼容
- ✅ v6.0 owner 字段 100% 兼容
- ✅ 既有 .orchestrate-state.json / .loop-state-*.json 加载逻辑不变

# Orchestrator Trace Format（v6.0 可观测性）

> 每次 Orchestrator 编排后输出 trace，用户可用 `/trace <id>` 回溯。

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["trace_id", "timestamp", "task_type", "skills_invoked", "stop_reason"],
  "properties": {
    "trace_id": {
      "type": "string",
      "format": "uuid",
      "description": "唯一 trace 标识"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "user_input_hash": {
      "type": "string",
      "description": "用户输入的 SHA256 哈希（不存原文，避免泄露）"
    },
    "detected_intents": {
      "type": "array",
      "items": {"type": "string"}
    },
    "task_type": {
      "type": "string",
      "enum": ["调研+决策", "分析+建议", "诊断+修复", "设计+实现", "规划+并行", "user_explicit"]
    },
    "orchestration_mode": {
      "type": "string",
      "enum": ["serial", "parallel"]
    },
    "skills_invoked": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["skill_name", "start_time", "end_time", "tokens_used", "status"],
        "properties": {
          "skill_name": {"type": "string"},
          "start_time": {"type": "string", "format": "date-time"},
          "end_time": {"type": "string", "format": "date-time"},
          "duration_seconds": {"type": "number"},
          "tokens_used": {"type": "integer"},
          "status": {
            "type": "string",
            "enum": ["completed", "failed", "skipped", "aborted"]
          },
          "error": {"type": "string"}
        }
      }
    },
    "total_tokens": {"type": "integer"},
    "total_duration_seconds": {"type": "number"},
    "stop_reason": {
      "type": "string",
      "enum": ["completed", "timeout", "loop_detected", "user_abort", "user_decision_required", "token_limit_exceeded", "step_limit_exceeded", "skill_failed"]
    },
    "rollback_available": {
      "type": "boolean",
      "description": "用户是否可一键回滚到 v5.4 行为"
    }
  }
}
```

## 存储位置

- 默认：`~/.zcode/logs/orchestrator-traces/<trace_id>.json`
- 可配置：`LOOPENGINE_TRACE_DIR` 环境变量

## 隐私保护

- **不存储**用户输入原文
- 仅存储 SHA256 哈希用于回溯匹配
- 用户输入如含敏感信息（密码/token），哈希也安全

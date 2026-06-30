#!/usr/bin/env bash
# skills/orch/hooks/orch-bootstrap.sh
# session-start bootstrap - 注入 orch (多技能编排器) 全文到系统提示

set -euo pipefail

# 定位插件根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# 读取 orch/SKILL.md 全文
ORCH_MD="${PLUGIN_ROOT}/skills/orch/SKILL.md"
if [ ! -f "$ORCH_MD" ]; then
  echo "ERROR: orch/SKILL.md not found at $ORCH_MD" >&2
  exit 1
fi

SKILL_CONTENT=$(cat "$ORCH_MD")

# JSON 转义（5 个特殊字符）
escape_for_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

# 构造 session context
SESSION_CONTEXT="<EXTREMELY_IMPORTANT>
You have orch (multi-skill orchestrator, v1.0.0) installed.

Below is the full content of your orch skill. Read it carefully.

${SKILL_CONTENT}

For single-skill tasks: native description matching handles it — do not call /orch.
For multi-skill tasks: user must explicitly type /orch — see above for the 5 task chains.
</EXTREMELY_IMPORTANT>"

ESCAPED_CONTEXT=$(escape_for_json "$SESSION_CONTEXT")

# 按平台分支输出 JSON
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
  # Cursor 格式（顶层 snake_case）
  printf '{"additional_context": "%s"}' "$ESCAPED_CONTEXT"
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
  # Claude Code 格式（嵌套）
  printf '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "%s"}}' "$ESCAPED_CONTEXT"
else
  # Copilot CLI / 其他标准格式
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
fi

exit 0
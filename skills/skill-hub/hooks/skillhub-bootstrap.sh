#!/usr/bin/env bash
# skills/skill-hub/hooks/skillhub-bootstrap.sh
# v6.7 session-start bootstrap - 注入 skill-hub 全文到系统提示
# 参照 superpowers/session-start 实现

set -euo pipefail

# 定位插件根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# 读取 skill-hub/SKILL.md 全文
SKILLHUB_MD="${PLUGIN_ROOT}/skills/skill-hub/SKILL.md"
if [ ! -f "$SKILLHUB_MD" ]; then
  echo "ERROR: skill-hub/SKILL.md not found at $SKILLHUB_MD" >&2
  exit 1
fi

SKILL_CONTENT=$(cat "$SKILLHUB_MD")

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

ESCAPED_CONTENT=$(escape_for_json "$SKILL_CONTENT")

# 构造 session context
SESSION_CONTEXT="<EXTREMELY_IMPORTANT>
You have skill-hub (v6.7.0-alpha) installed as your meta-skill for routing.

Below is the full content of your skill-hub skill. Read it carefully.

${SKILL_CONTENT}

For all other skills, follow the 1% rule: even 1% chance a skill applies -> invoke it.
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

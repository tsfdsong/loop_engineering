#!/usr/bin/env bash
# skills/orch/hooks/orch-bootstrap.sh
# session-start bootstrap - 注入 orch (多技能编排器) 全文到系统提示

set -euo pipefail

# 定位插件根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# 读取 orch runtime bundle（skill + 关键 reference）
load_bundle() {
  local refs_root="${PLUGIN_ROOT}/skills/orch/references"
  local files=(
    "${PLUGIN_ROOT}/skills/orch/SKILL.md"
    "${refs_root}/intent-schema.json"
    "${refs_root}/capability-registry.yaml"
    "${refs_root}/dag-rules.yaml"
    "${refs_root}/executor-contracts/direct-skill.json"
    "${refs_root}/executor-contracts/loop.json"
    "${refs_root}/executor-contracts/go.json"
  )

  for path in "${files[@]}"; do
    if [ -f "$path" ]; then
      printf '\n### %s ###\n' "${path#${PLUGIN_ROOT}/}"
      cat "$path"
      printf '\n'
    fi
  done
}

SKILL_CONTENT=$(load_bundle)

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
You have orch v2 installed: a natural-language-first, family-first, rule-first multi-skill orchestrator.

Below is the orch runtime bundle (skill + orchestration references). Read it carefully.

${SKILL_CONTENT}

For single-skill tasks: native description matching handles it.
For multi-skill goals: orch should infer the family and actions automatically; /orch remains only as an explicit force-orchestrate entry.
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
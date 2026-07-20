#!/usr/bin/env bash
# skills/go/hooks/go-bootstrap.sh
#
# session-start bootstrap —— 注入 go（编排层）runtime bundle 到宿主系统提示。
# **工具无关**：自动识别宿主（Cursor / Claude Code / Copilot / ZCode / Codex / Gemini / Pi / TRAE）并按对应格式输出。
# 由 orch 的 orch-bootstrap.sh（v1）演化而来（D6.3 迁移 + 多目标扩展）。

set -euo pipefail

# 定位插件根目录（hooks → skill → plugin root）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# ──────────────────────────────────────────────────────────────
# 读取 go runtime bundle（skill + 关键 reference）
# ──────────────────────────────────────────────────────────────
load_bundle() {
  local refs_root="${PLUGIN_ROOT}/skills/go/references"
  local files=(
    "${PLUGIN_ROOT}/skills/go/SKILL.md"
    "${PLUGIN_ROOT}/skills/go/routing-rules.yaml"
    "${refs_root}/family-routing.md"
    "${refs_root}/dag-assembly.md"
    "${refs_root}/state-protocol.md"
    "${refs_root}/degradation.md"
    "${refs_root}/runtime-config.md"
    "${refs_root}/handoff-protocol.md"
    "${refs_root}/breakpoint-recovery.md"
    "${refs_root}/complexity-rules.md"
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

# ──────────────────────────────────────────────────────────────
# JSON 转义（5 个特殊字符）
# ──────────────────────────────────────────────────────────────
escape_for_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

# ──────────────────────────────────────────────────────────────
# 构造 session context
# ──────────────────────────────────────────────────────────────
SESSION_CONTEXT="<EXTREMELY_IMPORTANT>
You have go v2.0 installed: the orchestration layer of LoopEngine (worktree-isolated, multi-skill, system-review-aware).

Below is the go runtime bundle (skill + orchestration references). Read it carefully.

${SKILL_CONTENT}

Key points:
- For single-task closed-loop coding: use loop skill (/loop).
- For multi-module parallel orchestration with worktree isolation: use go (/go).
- For cross-cutting concerns: see degradation.md (fallback chain) and runtime-config.md (.loopengine.yaml).
- The orchestration layer absorbed orch v1 (family recognition + DAG assembly). Use /go for multi-skill orchestration.
- This bootstrap is host-tool agnostic and works with any MCP-compatible AI coding tool.
</EXTREMELY_IMPORTANT>"

ESCAPED_CONTEXT=$(escape_for_json "$SESSION_CONTEXT")

# ──────────────────────────────────────────────────────────────
# 按宿主工具分支输出 JSON
# ──────────────────────────────────────────────────────────────
# 探测顺序：Cursor → Claude Code（非 Copilot）→ Copilot → ZCode → Codex → Gemini → Pi → TRAE → fallback
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
  # Cursor 格式（顶层 snake_case additional_context）
  printf '{"additional_context": "%s"}' "$ESCAPED_CONTEXT"
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
  # Claude Code 格式（嵌套 hookSpecificOutput.additionalContext）
  printf '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "%s"}}' "$ESCAPED_CONTEXT"
elif [ -n "${COPILOT_CLI:-}" ]; then
  # GitHub Copilot CLI / 其它 flat additionalContext
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
elif [ -n "${ZCODE_CLI:-}" ] || [ -d "${HOME}/.zcode" ]; then
  # ZCode 格式（同 flat additionalContext）
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
elif [ -n "${CODEX_CLI:-}" ] || [ -d "${HOME}/.codex" ]; then
  # Codex
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
elif [ -n "${GEMINI_CLI:-}" ] || [ -d "${HOME}/.gemini" ]; then
  # Gemini CLI（claude 风格嵌套）
  printf '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "%s"}}' "$ESCAPED_CONTEXT"
elif [ -n "${PI_CLI:-}" ] || [ -d "${HOME}/.pi" ]; then
  # Pi
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
elif [ -n "${TRAE_CLI:-}" ] || [ -d "${HOME}/.trae" ]; then
  # TRAE
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
else
  # 默认 / 未识别宿主：fallback flat 格式（最通用）
  printf '{"additionalContext": "%s"}' "$ESCAPED_CONTEXT"
fi

exit 0

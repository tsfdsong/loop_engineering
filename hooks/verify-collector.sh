#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────
# hooks/verify-collector.sh — PostToolUse hook: 采集验证证据到状态目录
# ────────────────────────────────────────────────────────────
# 职责：监听 Write/Edit/Bash/Agent 工具调用，累积证据到 .verify-state/<SID>/
#   - Write|Edit      → 标记 has_code_changes=true（触发 Stop gate）
#   - Bash            → 检测 test/build/curl 等验证命令 → 追加 evidence-log.jsonl
#   - Agent           → 解析返回是否含 verdict 签名 → 写 verdict.json
#
# 输入：stdin JSON（hook runner 注入，含 tool_name + tool_input）
# 输出：无（静默采集，exit 0 不阻断工具流）
# 降级：stdin 解析失败 → 静默 exit 0（不阻断正常工作流）
# ────────────────────────────────────────────────────────────
set -uo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_ROOT="${CLAUDE_PROJECT_DIR:-${ZCODE_PROJECT_DIR:-$PLUGIN_ROOT}}/.verify-state"
SESSION_ID="${CLAUDE_SESSION_ID:-${ZCODE_SESSION_ID:-default}}"
SESSION_DIR="$STATE_ROOT/$SESSION_ID"

# 安全降级：目录不存在（SessionStart 未跑）→ 静默退出
[ -d "$SESSION_DIR" ] || exit 0

# 读取 stdin（hook runner 通过 stdin 传 JSON）
INPUT="$(cat 2>/dev/null || true)"
[ -z "$INPUT" ] && exit 0

# 提取 tool_name（兼容 jq 缺失的场景，用 grep fallback）
TOOL_NAME=""
if command -v jq >/dev/null 2>&1; then
    TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)"
else
    # grep fallback：匹配 "tool_name": "Bash" 模式
    TOOL_NAME="$(printf '%s' "$INPUT" | grep -oE '"tool_name"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | grep -oE '"[^"]+"$' | tr -d '"' || true)"
fi
[ -z "$TOOL_NAME" ] && exit 0

# 提取 tool_input.command（Bash 工具时用）和 tool_result（Agent 工具时用）
TOOL_CMD=""
TOOL_RESULT=""
if command -v jq >/dev/null 2>&1; then
    TOOL_CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
    TOOL_RESULT="$(printf '%s' "$INPUT" | jq -r '.tool_result // empty' 2>/dev/null || true)"
fi

NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

case "$TOOL_NAME" in
    Write|Edit|MultiEdit|ApplyPatch)
        # 标记本轮有代码改动（触发 Stop gate）
        printf 'true' > "$SESSION_DIR/has_code_changes"
        ;;

    Bash)
        # 检测验证命令 → 追加到 evidence-log.jsonl
        # 匹配 test/build/curl/agent-browser/pytest/jest/npm test 等验证命令
        if printf '%s' "$TOOL_CMD" | grep -qiE '(^|[[:space:]/])(pytest|jest|npm[[:space:]]+test|[[:space:]]test[[:space:]]|npx[[:space:]]+playwright|agent-browser[[:space:]]+(open|screenshot|errors|network)|curl[[:space:]]+http|tsc[[:space:]]|--check|my|vite[[:space:]]+build|go[[:space:]]+test|cargo[[:space:]]+test)'; then
            # 追加一行 JSON 到 evidence-log.jsonl（JSON Lines 格式）
            ESCAPED_CMD="$(printf '%s' "$TOOL_CMD" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr '\n' ' ' | sed 's/  */ /g')"
            printf '{"tool":"Bash","cmd":"%s","timestamp":"%s"}\n' "${ESCAPED_CMD:0:500}" "$NOW" \
                >> "$SESSION_DIR/evidence-log.jsonl" 2>/dev/null || true
        fi
        ;;

    Agent|Task)
        # 解析 subagent 返回是否含 verdict 签名 → 写 verdict.json
        # 签名格式：<verdict:VERIFIED|FAILED:reason> 或 JSON verdict 块
        if printf '%s' "$TOOL_RESULT" | grep -qiE 'verdict[[:space:]]*:[[:space:]]*(VERIFIED|FAILED)'; then
            STATUS="$(printf '%s' "$TOOL_RESULT" | grep -oiE '(VERIFIED|FAILED)' | head -1 || true)"
            # 提取 STATUS 之后的 reason（到行尾或 < 或 > 边界）
            # 用 sed 先匹配整个 verdict:STATUS 前缀，取剩余部分，再去掉尾部的 > 或空白
            REASON="$(printf '%s' "$TOOL_RESULT" \
                | grep -oiE 'verdict[[:space:]]*:[[:space:]]*(VERIFIED|FAILED)[^<\n]*' \
                | head -1 \
                | sed -E 's/.*verdict[[:space:]]*:[[:space:]]*(VERIFIED|FAILED)//I; s/^[[:space:]]*:?[[:space:]]*//; s/[>[:space:]]*$//' \
                || true)"
            [ -n "$STATUS" ] && cat > "$SESSION_DIR/verdict.json" <<EOF
{"status":"$STATUS","reason":"${REASON:-}","verifier":"subagent","timestamp":"$NOW"}
EOF
        fi
        ;;
esac

# 始终 exit 0：采集是观察性的，不阻断工具流
exit 0

#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────
# hooks/verify-gate.sh — Stop hook: 完成声明的机器级阻断 gate
# ────────────────────────────────────────────────────────────
# 职责：AI 尝试停止时，校验是否存在验证证据。缺失则阻断（exit 2）。
# 这是三层防御 A（Stop hook 硬拦截）的核心。
#
# 判定逻辑：
#   has_code_changes=false → exit 0（纯对话/纯读，放行）
#   has_code_changes=true:
#     verdict.json 不存在 → exit 2 阻断（"必须先验证"）
#     verdict.status=VERIFIED → exit 0 放行
#     verdict.status=FAILED  → exit 2 阻断（附 reason）
#     verdict 过期(>5min)    → exit 2 阻断（"重新验证"）
#   block_count ≥ 3         → exit 0 + 软警告（防无限循环）
#
# 退出码：0=放行，2=阻断（强制 agent 再跑一轮验证）
# ────────────────────────────────────────────────────────────
set -uo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_ROOT="${CLAUDE_PROJECT_DIR:-${ZCODE_PROJECT_DIR:-$PLUGIN_ROOT}}/.verify-state"
SESSION_ID="${CLAUDE_SESSION_ID:-${ZCODE_SESSION_ID:-default}}"
SESSION_DIR="$STATE_ROOT/$SESSION_ID"

# ────────────────────────────────────────────────────────────
# emit_block <reason_text>: 统一输出阻断 JSON 到 stdout 并 exit 2
# 将多行 reason 转义为合法 JSON 字符串（换行→\n，引号→\"，反斜杠→\\）
# ────────────────────────────────────────────────────────────
emit_block() {
    local reason="$1"
    # 正确的 JSON 字符串转义：先转义反斜杠，再转义引号，最后转义换行
    local escaped
    escaped="$(printf '%s' "$reason" \
        | sed 's/\\/\\\\/g; s/"/\\"/g' \
        | awk '{printf "%s%s", (NR>1?"\\n":""), $0}')"
    # additionalContext JSON → stdout（ZCode 解析 stdout，strict schema）
    printf '{"additionalContext":"%s"}\n' "$escaped"
    exit 2
}

# ── 降级 0：状态目录不存在（SessionStart 未跑）→ 静默放行 ──
if [ ! -d "$SESSION_DIR" ]; then
    exit 0
fi

# ── 读状态 ──
HAS_CHANGES="$(cat "$SESSION_DIR/has_code_changes" 2>/dev/null || printf 'false')"
BLOCK_COUNT="$(cat "$SESSION_DIR/block_count" 2>/dev/null || printf '0')"
VERDICT_FILE="$SESSION_DIR/verdict.json"

# ── 降级：无代码改动 → 放行（纯对话/调研/只读场景）──
if [ "$HAS_CHANGES" != "true" ]; then
    exit 0
fi

# ── 防无限循环：阻断 ≥3 次后软警告放行 ──
if [ "$BLOCK_COUNT" -ge 3 ] 2>/dev/null; then
    # exit 0 放行，但注入 additionalContext 软警告（用户可见）
    MSG="⚠️ 验证 Gate：已阻断 3 次仍无有效验证证据（verdict.json 缺失或 FAILED）。本次放行，但请注意：代码改动未经独立验证。建议手动验证后再合并/部署。"
    # 软警告：用 emit_block 同款转义，但 exit 0（放行不阻断）
    ESCAPED_MSG="$(printf '%s' "$MSG" | sed 's/\\/\\\\/g; s/"/\\"/g')"
    printf '{"additionalContext":"%s"}\n' "$ESCAPED_MSG"
    exit 0
fi

# ── 核心判定：有代码改动时校验 verdict ──
if [ ! -f "$VERDICT_FILE" ]; then
    # 无 verdict → 阻断
    NEW_COUNT=$((BLOCK_COUNT + 1))
    printf '%s' "$NEW_COUNT" > "$SESSION_DIR/block_count"

    REASON="验证 Gate 阻断 (第 ${NEW_COUNT}/3 次)：检测到代码改动（Write/Edit），但无验证证据 verdict.json。

必须先完成验证，才能宣称任务完成：
  - 前端任务：用 agent-browser 执行 F1-F5 四阶段协议（errors=0 + 网络状态码 + snapshot 元素命中）
  - API 任务：curl 关键端点 + 校验状态码 + 响应体断言
  - 后端任务：跑测试（pytest/jest）+ 确认 exit code 0 + 失败计数 0
  - 脚本任务：黄金路径裸命令测试（零 flag，遵循 §1.10 测试纪律）

验证通过后，将 verdict 写入 ${VERDICT_FILE#"$CLAUDE_PROJECT_DIR"/}：
  {\"status\":\"VERIFIED\",\"evidence\":{...}}

或派验证官 subagent（/verify）自动完成验证并写 verdict。"

    emit_block "$REASON"
fi

# ── verdict.json 存在 → 校验 status ──
VERDICT_STATUS=""
VERDICT_REASON=""
if command -v jq >/dev/null 2>&1; then
    VERDICT_STATUS="$(jq -r '.status // empty' "$VERDICT_FILE" 2>/dev/null || true)"
    VERDICT_REASON="$(jq -r '.reason // empty' "$VERDICT_FILE" 2>/dev/null || true)"
else
    # grep fallback
    VERDICT_STATUS="$(grep -oE '"status"[[:space:]]*:[[:space:]]*"[^"]+"' "$VERDICT_FILE" | head -1 | grep -oE '"[^"]+"$' | tr -d '"' || true)"
    VERDICT_REASON="$(grep -oE '"reason"[[:space:]]*:[[:space:]]*"[^"]*"' "$VERDICT_FILE" | head -1 | sed 's/.*: *"//; s/"$//' || true)"
fi

# ── 过期判定：verdict mtime > 5 分钟 → 需重新验证 ──
VERDICT_MTIME=0
if [ -f "$VERDICT_FILE" ]; then
    # macOS/BSD 和 GNU stat 语法不同，兼容两种
    VERDICT_MTIME="$(stat -f %m "$VERDICT_FILE" 2>/dev/null || stat -c %Y "$VERDICT_FILE" 2>/dev/null || printf '0')"
fi
NOW_EPOCH="$(date +%s 2>/dev/null || printf '0')"
if [ "$VERDICT_MTIME" -gt 0 ] && [ "$NOW_EPOCH" -gt 0 ]; then
    AGE=$((NOW_EPOCH - VERDICT_MTIME))
    if [ "$AGE" -gt 300 ]; then  # 5 分钟 = 300 秒
        NEW_COUNT=$((BLOCK_COUNT + 1))
        printf '%s' "$NEW_COUNT" > "$SESSION_DIR/block_count"
        REASON="验证 Gate 阻断 (第 ${NEW_COUNT}/3 次)：验证证据已过期（${AGE}s > 300s）。代码可能在上次验证后又被修改，需重新验证。"
        emit_block "$REASON"
    fi
fi

case "$VERDICT_STATUS" in
    VERIFIED)
        # 验证通过 → 放行 + 重置计数器
        printf '0' > "$SESSION_DIR/block_count"
        exit 0
        ;;
    FAILED)
        # 验证失败 → 阻断 + 附 reason
        NEW_COUNT=$((BLOCK_COUNT + 1))
        printf '%s' "$NEW_COUNT" > "$SESSION_DIR/block_count"
        REASON="验证 Gate 阻断 (第 ${NEW_COUNT}/3 次)：验证官判定 FAILED。${VERDICT_REASON}

必须修复以下问题后重新验证：见 verdict.json 的 failures 字段。
修复后删除 verdict.json 并重新验证（派验证官或手动）。"
        emit_block "$REASON"
        ;;
    *)
        # status 字段缺失或非法 → 当作未验证
        NEW_COUNT=$((BLOCK_COUNT + 1))
        printf '%s' "$NEW_COUNT" > "$SESSION_DIR/block_count"
        REASON="验证 Gate 阻断 (第 ${NEW_COUNT}/3 次)：verdict.json 存在但 status 字段非法（期望 VERIFIED|FAILED，实际 '$VERDICT_STATUS'）。请修正 verdict.json 格式。"
        emit_block "$REASON"
        ;;
esac

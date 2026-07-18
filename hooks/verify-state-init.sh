#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────
# hooks/verify-state-init.sh — SessionStart hook: 初始化验证 Gate 状态目录
# ────────────────────────────────────────────────────────────
# 职责：为当前 session 创建 .verify-state/<SID>/ 并清理 >24h 的旧目录。
# 这是三层防御 D（证据文件）的初始化入口。
#
# 输入：${CLAUDE_SESSION_ID} 环境变量（由 ZCode hook runner 注入）
# 输出：无（静默初始化，失败不阻断会话）
# 退出码：始终 exit 0（init 失败不阻断会话，降级为"gate 静默失效"）
# ────────────────────────────────────────────────────────────
set -uo pipefail

# 解析项目根目录（hook 脚本在 hooks/ 下，根在上一级）
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_ROOT="${CLAUDE_PROJECT_DIR:-${ZCODE_PROJECT_DIR:-$PLUGIN_ROOT}}/.verify-state"
SESSION_ID="${CLAUDE_SESSION_ID:-${ZCODE_SESSION_ID:-default}}"

# 安全降级：session_id 为空或含路径分隔符时用 fallback（防目录穿越）
if [ -z "$SESSION_ID" ] || [[ "$SESSION_ID" == */* ]] || [[ "$SESSION_ID" == *..* ]]; then
    SESSION_ID="default"
fi

SESSION_DIR="$STATE_ROOT/$SESSION_ID"

# 1. 创建当前 session 状态目录（静默失败 → gate 降级失效）
mkdir -p "$SESSION_DIR" 2>/dev/null || exit 0

# 2. 初始化状态文件（不覆盖已存在的 — resume 场景保留历史）
[ -f "$SESSION_DIR/has_code_changes" ] || printf 'false' > "$SESSION_DIR/has_code_changes"
[ -f "$SESSION_DIR/block_count" ] || printf '0' > "$SESSION_DIR/block_count"
# verdict.json 不预创建（不存在 = 未验证，是 Stop hook 判定依据）

# 3. 记录 session 启动时间戳（用于过期判定 + 清理）
date -u +%Y-%m-%dT%H:%M:%SZ > "$SESSION_DIR/session_started_at"

# 4. 清理 >24h 的旧 session 目录（防 .verify-state 膨胀）
# 用 find -mtime 按修改时间清理，保留当前 session
if command -v find >/dev/null 2>&1; then
    find "$STATE_ROOT" -maxdepth 1 -mindepth 1 -type d -mtime +1 -not -name "$SESSION_ID" \
        -exec rm -rf {} + 2>/dev/null || true
fi

# 始终 exit 0：init 是幂等的，失败不应阻断会话
exit 0

#!/usr/bin/env bash
# skills/go/hooks/install-hooks.sh
#
# 注册 go（编排层）session-start hook 到宿主 AI 编码工具。
# **工具无关**：自动探测已安装的宿主工具并注册 hook。
# 支持 8 个目标（spec §3.5.6）：ZCode / Claude Code / Cursor / Codex / Gemini / Copilot / Pi / TRAE。
#
# 用法：
#   bash skills/go/hooks/install-hooks.sh            # 探测所有候选，逐一注册
#   bash skills/go/hooks/install-hooks.sh --target claude   # 仅注册指定目标

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOTSTRAP="${PLUGIN_ROOT}/skills/go/hooks/go-bootstrap.sh"

VERSION="2.0.0"

# ──────────────────────────────────────────────────────────────
# 候选目标（spec §3.5.6 · 8 目标）
# 格式: "显示名|用户级目录|配置文件|字段风格"
# 字段风格：
#   claude  = Claude Code 嵌套 hooks.SessionStart[].hooks[]
#   flat    = 顶层 hooks.SessionStart[]
#   zcode   = ZCode settings.hooks
# ──────────────────────────────────────────────────────────────
TARGETS=(
  "ZCode|$HOME/.zcode|$HOME/.zcode/cli/config.json|zcode"
  "Claude Code|$HOME/.claude|$HOME/.claude/settings.json|claude"
  "Cursor|$HOME/.cursor|$HOME/.cursor/mcp.json|flat"
  "Codex|$HOME/.codex|$HOME/.codex/config.toml|flat"
  "Gemini|$HOME/.gemini|$HOME/.gemini/settings.json|claude"
  "Copilot|$HOME/.copilot|$HOME/.copilot/config.json|flat"
  "Pi|$HOME/.pi|$HOME/.pi/settings.json|claude"
  "TRAE|$HOME/.trae|$HOME/.trae/config.json|flat"
)

# 命令行：过滤单目标
FILTER=""
if [ "${1:-}" = "--target" ] && [ -n "${2:-}" ]; then
  FILTER="$2"
fi

echo "=== Installing go v${VERSION} session-start hook ==="
echo "  bootstrap: $BOOTSTRAP"
[ -n "$FILTER" ] && echo "  --target filter: $FILTER"
echo ""

REGISTERED=0
SKIPPED=0

for entry in "${TARGETS[@]}"; do
  IFS='|' read -r NAME DIR CFG STYLE <<< "$entry"

  # 过滤
  if [ -n "$FILTER" ]; then
    # 大小写不敏感匹配显示名
    lower_filter=$(echo "$FILTER" | tr '[:upper:]' '[:lower:]')
    lower_name=$(echo "$NAME" | tr '[:upper:]' '[:lower:]')
    case "$lower_name" in
      *"$lower_filter"*) : ;;  # 命中，继续
      *) continue ;;
    esac
  fi

  if [ ! -d "$DIR" ]; then
    echo "  SKIP  $NAME  (目录不存在: $DIR)"
    SKIPPED=$((SKIPPED+1))
    continue
  fi

  mkdir -p "$(dirname "$CFG")"

  # 备份
  if [ -f "$CFG" ]; then
    cp "$CFG" "$CFG.bak.$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
  fi

  # 写入 hook 配置（按风格）
  case "$STYLE" in
    claude)
      cat > "$CFG" <<EOF
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup|clear|compact",
      "hooks": [{
        "type": "command",
        "command": "$BOOTSTRAP",
        "async": false
      }]
    }]
  }
}
EOF
      ;;
    zcode)
      cat > "$CFG" <<EOF
{
  "settings": {
    "hooks": {
      "SessionStart": [{
        "matcher": "startup|clear|compact",
        "command": "$BOOTSTRAP",
        "async": false
      }]
    }
  }
}
EOF
      ;;
    flat)
      cat > "$CFG" <<EOF
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup|clear|compact",
      "type": "command",
      "command": "$BOOTSTRAP",
      "async": false
    }]
  }
}
EOF
      ;;
  esac

  echo "  OK    $NAME  → $CFG"
  REGISTERED=$((REGISTERED+1))
done

echo ""
echo "=== Installation complete ==="
echo "  registered: $REGISTERED  skipped: $SKIPPED"
if [ "$REGISTERED" -gt 0 ]; then
  echo "  重启对应宿主工具以激活 go v${VERSION}。"
else
  echo "  ⚠️  未注册任何目标。检查候选目录是否存在（默认仅当目录存在才注册）。"
  echo "      若需强制指定，使用: bash install-hooks.sh --target claude"
  exit 1
fi

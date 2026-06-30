#!/usr/bin/env bash
# skills/skill-hub/hooks/install-hooks.sh
# 注册 skill-hub session-start hook 到 Claude Code

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
HOOK_CMD="\"${PLUGIN_ROOT}/skills/skill-hub/hooks/skillhub-bootstrap.sh\""

echo "=== Installing skill-hub v6.7 session-start hook ==="

# Claude Code (~/.claude/settings.json)
if [ -d "$HOME/.claude" ]; then
  SETTINGS="$HOME/.claude/settings.json"
  mkdir -p "$(dirname "$SETTINGS")"

  if [ -f "$SETTINGS" ]; then
    cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d)"
  fi

  cat > "$SETTINGS" <<EOF
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup|clear|compact",
      "hooks": [{
        "type": "command",
        "command": "$HOOK_CMD",
        "async": false
      }]
    }]
  }
}
EOF
  echo "Claude Code hook registered: $SETTINGS"
else
  echo "WARN: ~/.claude/ not found. Skipping Claude Code registration."
fi

echo ""
echo "=== Installation complete ==="
echo "Restart your agent to activate skill-hub v6.7.0-alpha."

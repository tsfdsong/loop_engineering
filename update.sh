#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# LoopEngine 一键更新 — 等价于 curl install.sh | bash
# ════════════════════════════════════════════════════════════
# 设计哲学: 「更新 = 重新走 install」
# update.sh = git pull 本地源码 + exec install.sh
#
# 一行更新:
#   bash <(curl -fsSL https://raw.githubusercontent.com/tsfdsong/loop_engineering/main/update.sh)
# ════════════════════════════════════════════════════════════

set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"

echo -e "\033[1m\033[36m🔄 LoopEngine 更新: 拉取源码 + 重跑 install\033[0m"

# Step 1: 同步本地源码到 main HEAD
echo "  📥 git pull origin main..."
cd "$SELF" && git pull --quiet origin main 2>/dev/null || {
    echo "  ⚠️  git pull 失败 — 直接走 install.sh (本地源码可能不是最新)"
}

# Step 2: exec install.sh (重新部署技能 + MCP)
echo "  🔄 重新跑 install.sh..."
exec bash "$SELF/install.sh"

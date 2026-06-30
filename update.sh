#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# LoopEngine 一键更新
# ════════════════════════════════════════════════════════════
# 因为 install.sh 总是拉最新源码，所以更新 = 重新安装:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
#
# 本文件 = 本地已有仓库用户专用: git pull + exec install.sh
# ════════════════════════════════════════════════════════════

set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"

echo -e "\033[1m\033[36m🔄 LoopEngine 更新: git pull + 重跑 install\033[0m"
cd "$SELF"
git pull --quiet origin main 2>/dev/null || echo "  ⚠️  git pull 失败 — 继续按本地源码安装"
exec bash install.sh

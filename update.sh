#!/usr/bin/env bash
# ════════════════════════════════════════════════════
# LoopEngine 一键更新 v1.1.0
# ════════════════════════════════════════════════════
# v1.0.2 设计：本脚本 = git pull + exec install.sh
#   缺陷：仅对"本地已 git clone 过仓库"的用户有用；curl 用户用不上。
#   历史：d2e6370 "治本 v2" 被 ecae795 Revert（反复治本失败）。
#
# v1.1.0 重构：本脚本 = 自愈入口 + 转发到 install.sh
#   - 任何用户（curl / 本地仓库）跑本脚本都生效
#   - 内部拉最新源码到 $WORK，exec $WORK/install.sh（永远用最新版）
#   - 与 curl 跑 install.sh 完全等价，但保留了"update.sh"命名（IDE 集成、用户习惯）
#
# 推荐用法（与 v1.0.2 兼容）：
#   bash update.sh                   # 默认更新到 main 最新版
#   bash update.sh --branch fix/xxx  # 更新到指定分支（开发用）
#   bash update.sh --dry-run         # 只检查版本，不实际安装
# ════════════════════════════════════════════════════

set -euo pipefail

REPO="https://github.com/tsfdsong/loop_engineering"
BRANCH="main"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "用法: bash update.sh [--branch <name>] [--dry-run]"
            echo "  --branch <name>  指定分支（默认 main）"
            echo "  --dry-run        只检查版本，不实际安装"
            exit 0
            ;;
        *)
            echo "未知参数: $1" >&2
            exit 1
            ;;
    esac
done

echo -e "\033[1m\033[36m🔄 LoopEngine 更新 (v1.1.0 自愈入口)\033[0m"

# 拉最新源码到临时目录
WORK="${TMPDIR:-/tmp}/loopengine-update-$$"
trap 'rm -rf "$WORK"' EXIT

echo "  ↳ 拉取 ${REPO}@${BRANCH} ..."
if ! git clone --depth 1 --branch "$BRANCH" --quiet "$REPO" "$WORK" 2>/dev/null; then
    echo -e "  \033[31m❌\033[0m  无法 clone ${REPO}@${BRANCH}，请检查网络 / 分支名"
    exit 1
fi

# 检查版本
NEW_VERSION=$(grep -E '^VERSION=' "$WORK/install.sh" | head -1 | cut -d'"' -f2 || echo "unknown")
INSTALLED_VERSION_FILE="$HOME/.loopengine/.installed_version"
INSTALLED_VERSION=""
[ -f "$INSTALLED_VERSION_FILE" ] && INSTALLED_VERSION=$(cat "$INSTALLED_VERSION_FILE" 2>/dev/null || echo "")

echo "  ↳ 已装版本: ${INSTALLED_VERSION:-未装}"
echo "  ↳ 远端版本: ${NEW_VERSION}"

if [ "$DRY_RUN" = true ]; then
    if [ "$INSTALLED_VERSION" = "$NEW_VERSION" ]; then
        echo -e "  \033[32m✅\033[0m  已是最新版本（dry-run 不执行安装）"
    else
        echo -e "  \033[33m⚠\033[0m  需要更新（dry-run 不执行安装）"
    fi
    exit 0
fi

if [ "$INSTALLED_VERSION" = "$NEW_VERSION" ]; then
    echo -e "  \033[32m✅\033[0m  已是最新版本，无需操作"
    echo "  ↳ 如需强制重装，请删除 $INSTALLED_VERSION_FILE 后重跑"
    exit 0
fi

# 转发到 install.sh（永远用 clone 出来的最新版）
echo "  ↳ 启动 install.sh @ $NEW_VERSION ..."
exec bash "$WORK/install.sh"

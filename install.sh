#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# LoopEngine 一键安装 v1.2.4 — 跨平台调度器（macOS/Windows/Linux）
# ════════════════════════════════════════════════════════════
# 一行安装:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
#
# 智能模式（默认）：
#   - 未装 ~/.loopengine/.installed_version → 首次安装
#   - 已装同版 → 5 秒等待（防误触，--force 跳过）
#   - 已装旧版 → 升级
#   - 拉源码每次都做（git clone --depth 1），所以 install.sh 天然具备"更新"能力
#
# 参数:
#   --dry-run   只检查版本不实际安装（拉源码 + 比对 + 输出计划）
#   --force     跳过 5 秒等待，强制重装（同版本也执行）
#   -h, --help  显示帮助
#
# 架构（v1.2.4 跨平台分层）：
#   install.sh              ← 顶层调度器（本文件 · 100 行）
#   scripts/install/_common.sh   ← 平台无关共享逻辑
#   scripts/install/macos.sh     ← macOS 特定（pip3 + ~/Library/Python/3.*/bin）
#   scripts/install/windows.sh   ← Windows 特定（Git Bash + %APPDATA%）
#   scripts/install/linux.sh     ← Linux 特定（pip3 + ~/.local/bin）
#
# v1.2.4 重构（2026-07-01 跨平台架构）：
#   • install.sh 610 → 100 行（精简为调度器）
#   • 提取 _common.sh / macos.sh / windows.sh / linux.sh 4 个子脚本
#   • 自动 uname -s 检测 → 平台分发
#   • LOCAL_SRC_DIR 保留（开发模式本地 scripts/ 覆盖 clone 副本）
#
# v1.2.3 修复（2026-07-01 macOS 跨平台兼容）：见 docs/lessons-learned.md L#001
#
# v1.2.0 修复（2026-07-01 智能模式合一）：新增 --dry-run / --force / --help
# v1.1.0 历史修复（保留）：5 条红线 sentinel markers / 数组化等
# ════════════════════════════════════════════════════════════

set -euo pipefail

# ── 加载共享逻辑 ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-/dev/null}")" 2>/dev/null && pwd || echo "")"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/scripts/install/_common.sh"

# ── 参数解析 ──────────────────────────────────────────────
COMMON_DRY_RUN=false
COMMON_FORCE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            COMMON_DRY_RUN=true
            shift
            ;;
        --force)
            COMMON_FORCE=true
            shift
            ;;
        -h|--help)
            cat <<'HELP'
LoopEngine 一键安装 v1.2.4（跨平台：macOS / Windows Git Bash / Linux）

用法:
  bash install.sh              # 智能模式（首次装 / 升级 / 同版本 5秒等待）
  bash install.sh --force      # 强制重装（跳过 5 秒等待）
  bash install.sh --dry-run    # 只检查不安装
  bash install.sh -h           # 显示此帮助

推荐一行安装:
  curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash

更新 = 重新跑 install.sh（自动智能模式）。
HELP
            exit 0
            ;;
        *)
            echo -e "\033[31m❌ 未知参数: $1\033[0m（用 -h 看帮助）" >&2
            exit 1
            ;;
    esac
done

# ── 本地优先覆盖（开发模式）──────────────────────────────
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    COMMON_LOCAL_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# ── 顶部横幅 ──────────────────────────────────────────────
echo ""
echo -e "${_BOLD}${_CYAN}╔══════════════════════════════════════════════════╗${_RESET}"
echo -e "${_BOLD}${_CYAN}║  LoopEngine v${COMMON_VERSION} — 跨平台一键安装/更新     ║${_RESET}"
echo -e "${_BOLD}${_CYAN}║  自动检测平台 · skills/AGENTS.md/hooks/MCP/7 红线 ║${_RESET}"
echo -e "${_BOLD}${_CYAN}╚══════════════════════════════════════════════════╝${_RESET}"
if [ "$COMMON_DRY_RUN" = true ]; then
    echo -e "  ${_CYAN}ℹ${_RESET}  ${_BOLD}--dry-run${_RESET} 模式：只检查不安装"
fi
if [ "$COMMON_FORCE" = true ]; then
    echo -e "  ${_CYAN}ℹ${_RESET}  ${_BOLD}--force${_RESET} 模式：跳过 5 秒等待，强制重装"
fi
echo ""

# ── 平台检测 ──────────────────────────────────────────────
PLATFORM=""
detect_platform() {
    local uname_s
    uname_s=$(uname -s 2>/dev/null || echo "Unknown")
    case "$uname_s" in
        Darwin*)
            echo "macos"
            ;;
        Linux*)
            echo "linux"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "windows"
            ;;
        *)
            return 1
            ;;
    esac
}

PLATFORM=$(detect_platform) || {
    local uname_s
    uname_s=$(uname -s 2>/dev/null || echo "Unknown")
    echo -e "${_RED}❌ 不支持的操作系统：${uname_s}${_RESET}"
    echo -e "  ${_CYAN}•${_RESET} 支持平台：macOS (Darwin) / Linux / Windows (Git Bash: MINGW/MSYS/CYGWIN)"
    echo -e "  ${_CYAN}•${_RESET} Windows 用户：请安装 Git for Windows（https://git-scm.com/）后用 Git Bash 执行"
    exit 1
}

echo -e "${_BOLD}🖥  检测到平台：${PLATFORM}${_RESET}"

# ── Step 0: 版本自检 ──────────────────────────────────────
echo ""
echo -e "${_BOLD}🔍 Step 0: 版本自检（智能模式）...${_RESET}"
INSTALLED_VERSION=""
[ -f "$COMMON_INSTALLED_VERSION_FILE" ] && INSTALLED_VERSION=$(cat "$COMMON_INSTALLED_VERSION_FILE" 2>/dev/null || echo "")
common_smart_check_version "$INSTALLED_VERSION" "$COMMON_VERSION"

# ── Step 1: 拉源码 ────────────────────────────────────────
common_clone_repo || exit 1

# ── dry-run 早退出 ────────────────────────────────────────
if [ "$COMMON_DRY_RUN" = true ]; then
    common_dry_run_summary "$INSTALLED_VERSION"
    exit 0
fi

# ── Step 2: 部署（共享）──────────────────────────────────
echo ""
echo -e "${_BOLD}📦 Step 2: 部署到 AI 工具约定目录...${_RESET}"
common_render_plugins || exit 1
common_deploy_to_9_tools

# ── 加载平台脚本 + 调 Step 3/4/5 ─────────────────────────
PLATFORM_SCRIPT="$SCRIPT_DIR/scripts/install/${PLATFORM}.sh"
if [ ! -f "$PLATFORM_SCRIPT" ]; then
    echo -e "${_RED}❌ 平台脚本缺失：${PLATFORM_SCRIPT}${_RESET}"
    echo -e "  ${_CYAN}•${_RESET} 请检查 scripts/install/ 目录"
    echo -e "  ${_CYAN}•${_RESET} 完整源码：https://github.com/tsfdsong/loop_engineering/tree/main/scripts/install"
    exit 1
fi

# shellcheck disable=SC1090
source "$PLATFORM_SCRIPT"

# 调度平台入口
case "$PLATFORM" in
    macos)   macos_main ;;
    windows) windows_main ;;
    linux)   linux_main ;;
    *)
        echo -e "${_RED}❌ 未知平台入口：${PLATFORM}${_RESET}"
        exit 1
        ;;
esac

# ── Step 6: 部署自检（共享）───────────────────────────────
common_deployment_check

# ── 总结 ──────────────────────────────────────────────────
common_print_target_summary "$PLATFORM"
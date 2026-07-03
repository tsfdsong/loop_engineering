#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# LoopEngine 一键安装 v1.3.2 — 跨平台自动感知调度器（macOS/Windows/Linux）
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
# 自动感知：
#   - OS：uname -s 自动检测（Darwin→macos / Linux→linux / MINGW|MSYS|CYGWIN→windows）
#   - AI Agent：common_detect_installed_agents 扫描本机 ~/.zcode ~/.claude ~/.cursor ...
#     等 7 个特征路径，默认只给已检测到的 Agent 部署；--all 强制全量；--only=zcode,cursor 显式指定
#     （Kimi / OpenCode 走各自平台原生命令手动部署，不在 install.sh 范围）
#
# 参数:
#   --dry-run           只检查版本不实际安装（拉源码 + 比对 + 输出计划）
#   --force             跳过 5 秒等待，强制重装（同版本也执行）
#   --all               绕过 detect，强制全部 9+ 工具全量部署
#   --only=<list>       指定 agent id 列表（空格或逗号分隔），覆盖 detect
#   -h, --help          显示帮助
#
# 架构（v1.2.4+ 跨平台分层 + v1.3.0 自动感知）：
#   install.sh                      ← 顶层调度器（本文件 · ~120 行）
#   scripts/install/_common.sh      ← 平台无关共享逻辑（含 detect + 平台分支 tool_root_dirs）
#   scripts/install/macos.sh        ← macOS 特定（pip3 + ~/Library/Python/3.*/bin）
#   scripts/install/windows.sh      ← Windows 特定（Git Bash + %APPDATA% + path → forward slash）
#   scripts/install/linux.sh        ← Linux 特定（pip3 + ~/.local/bin）
#   scripts/merge_mcp_config.py    ← ZCode + Cursor MCP 合并（v1.3.1 合一，--schema=zcode|cursor）
#
# v1.3.0 重构（2026-07-02 自动感知 + Cursor 适配 + Win 路径 bug 修复）：
#   • OS + AI Agent 平台全自动感知（默认按本机已装的 Agent 部署）
#   • 新增 --all / --only 参数覆盖 detect
#   • tool_root_dirs 重构成 common_tool_root_dirs_for_platform（修复 macOS/Linux
#     创建虚假 $HOME/AppData/... 目录的事实 bug）
#   • Cursor 平台 win/macos/linux 写 ~/.cursor/mcp.json（保留用户 drawio 等 server）
#   • 自检 self-check 阈值自适应（按平台分支后的实际目标数 80%）
#
# v1.3.1 精简（2026-07-02 三平台合一 + merge_mcp_config 合并 + 关联数组 + 5 sub-function）：
#   • scripts/install/{windows,macos,linux}.sh 从 ~145 → ~18 行（-87%）
#   • merge_zcode_config.py + merge_cursor_config.py 合并为 merge_mcp_config.py
#     （--schema=zcode|cursor 参数；atomic write 6 行在脚本内保留，不抽 _atomic_io.py）
#   • AGENT 标签双份真源 → COMMON_LABEL_TO_ID 关联数组
#   • common_deploy_to_9_tools 100 行拆 5 sub-function + _for_each_target 通用 iterator
#   • windows/macos|linux tool_root_dirs 共享 7 行 BASE_TARGETS
#   • Kimi/OpenCode 从 install.sh 自动感知范围移除（走各自平台原生命令）
#   • docs/skill-hub-install-reference.md + docs/RELEASE-NOTES-v1.2.0.md 删（外部/过期）
#
# 历史（v1.0.x–v1.2.x）：见 git log / docs/legacy/README.md
# ════════════════════════════════════════════════════════════

set -euo pipefail

# ── 加载共享逻辑 ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-/dev/null}")" 2>/dev/null && pwd || echo "")"
# shellcheck disable=SC1091
if [ -z "$SCRIPT_DIR" ] || [ "$SCRIPT_DIR" = "/dev" ]; then
    # Piped 模式（curl|bash / wget -O-|bash）：BASH_SOURCE[0] 为空 → 走网络拉取
    _COMMON_URL="https://github.com/tsfdsong/loop_engineering/raw/main/scripts/install/_common.sh"
    _COMMON_TMP="$(mktemp -t loopengine-common.XXXXXX.sh)"
    if ! curl -fsSL --max-time 30 "$_COMMON_URL" -o "$_COMMON_TMP"; then
        echo "❌ 无法下载 _common.sh: $_COMMON_URL" >&2
        rm -f "$_COMMON_TMP"
        exit 1
    fi
    # shellcheck disable=SC1090
    source "$_COMMON_TMP"
    rm -f "$_COMMON_TMP"
else
    source "$SCRIPT_DIR/scripts/install/_common.sh"
fi

# ── 参数解析 ──────────────────────────────────────────────
COMMON_DRY_RUN=false
COMMON_FORCE=false
COMMON_ALL=false
COMMON_ONLY=""
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
        --all)
            COMMON_ALL=true
            shift
            ;;
        --only=*)
            COMMON_ONLY="${1#*=}"
            # 支持空格或逗号分隔，转空格统一
            COMMON_ONLY=$(echo "$COMMON_ONLY" | tr ',' ' ' | xargs)
            shift
            ;;
        -h|--help)
            cat <<'HELP'
LoopEngine 一键安装 v1.3.2（跨平台：macOS / Windows Git Bash / Linux）

用法:
  bash install.sh                          # 智能模式 + 自动感知本机 AI Agent
  bash install.sh --all                     # 强制全量（11 工具，不走 detect）
  bash install.sh --only=zcode,cursor       # 只给指定 agent 部署（逗号或空格分隔）
  bash install.sh --force                   # 强制重装（跳过 5 秒等待）
  bash install.sh --dry-run                 # 只检查不安装
  bash install.sh -h                        # 显示此帮助

自动感知（v1.3.0）：
  • OS：uname -s 自动识别 Darwin/Linux/MINGW|MSYS|CYGWIN
  • AI Agent：扫描 ~/.zcode ~/.claude ~/.codex ~/.gemini ~/.copilot ~/.pi ~/.cursor
    ~/.kimi ~/.config/opencode 等特征路径，只给已检测到的工具部署

设计文档外部化（v1.3.2）：已删除（v1.3.2 简化：specs 仓库不存在，默认拉取会卡死）

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
# install.sh 与 _common.sh 在同目录；SCRIPT_DIR 即项目根
COMMON_LOCAL_SRC_DIR="${SCRIPT_DIR:-}"

# ── 顶部横幅 ──────────────────────────────────────────────
echo ""
echo -e "${_BOLD}${_CYAN}╔══════════════════════════════════════════════════╗${_RESET}"
echo -e "${_BOLD}${_CYAN}║  LoopEngine v${COMMON_VERSION} — 跨平台一键安装/更新     ║${_RESET}"
echo -e "${_BOLD}${_CYAN}║  自动检测平台 · skills/AGENTS.md/hooks/MCP/9 红线 ║${_RESET}"
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

# ── Step 0.5: AI Agent 自动感知 (v1.3.0) ──────────────────
# 把 PLATFORM 注入 COMMON_PLATFORM，让 _common.sh 的子函数能取到
COMMON_PLATFORM="$PLATFORM"
export COMMON_PLATFORM

echo ""
echo -e "${_BOLD}🔍 Step 0.5: AI Agent 自动感知（v1.3.0）...${_RESET}"
DETECTED_AGENTS=$(common_detect_installed_agents 2>/dev/null || true)
DETECTED_COUNT=$(printf '%s' "$DETECTED_AGENTS" | grep -c . || true)

# 决定最终要部署的 agent id 列表（--all > --only > detected）
if [ "$COMMON_ALL" = true ]; then
    AGENT_LIST="$COMMON_ALL_AGENT_IDS"
    echo -e "  ${_CYAN}ℹ${_RESET}  --all 模式：强制全量部署 ($COMMON_ALL_AGENT_IDS)"
elif [ -n "$COMMON_ONLY" ]; then
    AGENT_LIST="$COMMON_ONLY"
    echo -e "  ${_CYAN}ℹ${_RESET}  --only 模式：指定部署 ($AGENT_LIST)"
elif [ "$DETECTED_COUNT" -eq 0 ]; then
    echo -e "  ${_RED}❌${_RESET}  未检测到任何 AI Agent — 至少安装其中一个"
    echo -e "  ${_CYAN}•${_RESET} 推荐：用 ${_BOLD}bash install.sh --all${_RESET} 强制全量部署"
    exit 1
else
    AGENT_LIST="$DETECTED_AGENTS"
    echo -e "  ${_GREEN}✅${_RESET} 自动感知到 ${_BOLD}${DETECTED_COUNT}${_RESET} 个 AI Agent："
    while IFS= read -r agent; do
        [[ -z "$agent" ]] && continue
        echo -e "       ${_CYAN}•${_RESET} $agent"
    done <<< "$DETECTED_AGENTS"
fi

# 注入共享变量（_common.sh + 4 平台子脚本通过 env 读取）
# v1.3.2 修复：detect 用 printf '%s\n' 输出（换行分隔），但下游所有
# [[ " $list " == *" id "* ]] 匹配假设空格分隔 → 全部误判。
# 从源头标准化为空格分隔（换行/逗号/制表符 → 空格）。
COMMON_AGENT_LIST=$(printf '%s' "$AGENT_LIST" | tr '\n,\t' '   ' | tr -s ' ')
export COMMON_AGENT_LIST
echo ""

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
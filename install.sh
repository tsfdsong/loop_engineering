#!/usr/bin/env bash
# LoopEngine 一键安装脚本
# 自动检测 AI 编程工具并执行对应安装命令
#
# 用法:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
#   或
#   bash install.sh

set -euo pipefail

REPO_URL="https://github.com/tsfdsong/loop_engineering"
BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║       LoopEngine — 循环工程全家桶 安装脚本       ║${RESET}"
echo -e "${BOLD}${CYAN}║    loop闭环 + go编排 + skill-hub 55技能调度      ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

# Detect available tools
DETECTED=()

detect_tool() {
    local name="$1"
    local cmd="$2"
    if command -v "$cmd" &> /dev/null || (command -v which &> /dev/null && which "$cmd" &> /dev/null 2>/dev/null); then
        DETECTED+=("$name")
        return 0
    fi
    return 1
}

echo -e "${BOLD}🔍 检测已安装的 AI 编程工具...${RESET}"
echo ""

detect_tool "Claude Code" "claude" && echo -e "  ${GREEN}✅${RESET} Claude Code 已检测到"
detect_tool "Codex" "codex" && echo -e "  ${GREEN}✅${RESET} Codex 已检测到"
detect_tool "Gemini CLI" "gemini" && echo -e "  ${GREEN}✅${RESET} Gemini CLI 已检测到"
detect_tool "GitHub Copilot" "copilot" && echo -e "  ${GREEN}✅${RESET} GitHub Copilot CLI 已检测到"
detect_tool "Pi" "pi" && echo -e "  ${GREEN}✅${RESET} Pi 已检测到"

echo ""

if [ ${#DETECTED[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  未检测到已知的 AI 编程工具。${RESET}"
    echo ""
    echo "手动安装方式："
    echo "  git clone $REPO_URL ~/.loopengine"
    echo "  然后参考: $REPO_URL#readme"
    exit 0
fi

echo -e "${BOLD}📦 开始安装 LoopEngine...${RESET}"
echo ""

INSTALLED=0
FAILED=0

# ── Claude Code ──────────────────────────────────────────
# 验证通过的流程: marketplace add → plugin install
if echo "${DETECTED[@]}" | grep -q "Claude Code"; then
    echo -e "${CYAN}▶  安装到 Claude Code...${RESET}"
    
    # Step 1: 添加 marketplace（支持 GitHub URL 和本地路径）
    if claude plugin marketplace add "$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} marketplace 已添加"
    else
        # GitHub 不可用时尝试本地路径
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        if [ -f "$SCRIPT_DIR/.claude-plugin/marketplace.json" ]; then
            claude plugin marketplace add "$SCRIPT_DIR" 2>/dev/null && \
                echo -e "  ${GREEN}✅${RESET} marketplace 已添加（本地路径）" || \
                echo -e "  ${YELLOW}⚠️${RESET} marketplace 添加失败"
        fi
    fi
    
    # Step 2: 安装插件
    if claude plugin install loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Claude Code 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行:"
        echo -e "    claude plugin marketplace add $REPO_URL"
        echo -e "    claude plugin install loopengine"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── Codex ────────────────────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "Codex"; then
    echo -e "${CYAN}▶  安装到 Codex...${RESET}"
    if codex plugin install "$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Codex 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请在 Codex 插件市场中搜索 'loopengine' 安装"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── Gemini CLI ───────────────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "Gemini CLI"; then
    echo -e "${CYAN}▶  安装到 Gemini CLI...${RESET}"
    if gemini extensions install "$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Gemini CLI 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行: gemini extensions install $REPO_URL"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── GitHub Copilot CLI ───────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "GitHub Copilot"; then
    echo -e "${CYAN}▶  安装到 GitHub Copilot CLI...${RESET}"
    # Copilot 使用 marketplace 机制，类似 Claude Code
    if copilot plugin marketplace add "$REPO_URL" 2>/dev/null && \
       copilot plugin install loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} GitHub Copilot CLI 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行: copilot plugin install loopengine@tsfdsong"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── Pi ───────────────────────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "Pi"; then
    echo -e "${CYAN}▶  安装到 Pi...${RESET}"
    if pi install "git:$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Pi 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行: pi install git:$REPO_URL"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── 手动引导平台 ─────────────────────────────────────────
echo -e "${CYAN}▶  Cursor IDE${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  执行: /add-plugin tsfdsong/loop_engineering"
echo ""

echo -e "${CYAN}▶  ZCode${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  执行: zcode plugin install tsfdsong/loop_engineering"
echo ""

echo -e "${CYAN}▶  OpenCode${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  在 opencode.json 的 plugin 数组中添加:"
echo -e "  ${YELLOW}ℹ️${RESET}  \"loopengine@git+$REPO_URL.git\""
echo ""

echo -e "${CYAN}▶  Kimi Code${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  执行: /plugins install $REPO_URL"
echo ""

# ── 总结 ─────────────────────────────────────────────────
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}📊 安装总结${RESET}"
echo -e "  自动安装: ${GREEN}$INSTALLED${RESET} 个平台成功"
if [ $FAILED -gt 0 ]; then
    echo -e "  需手动安装: ${YELLOW}$FAILED${RESET} 个平台"
fi
echo ""
echo -e "${BOLD}🎉 LoopEngine 安装完成！${RESET}"
echo ""
echo -e "  验证安装: 打开新的 AI 会话，发送:"
echo -e "  ${CYAN}\"Tell me about LoopEngine\"${RESET}"
echo -e "  或直接使用:"
echo -e "  ${CYAN}\"/loop 帮我实现一个功能\"${RESET}"
echo -e "  ${CYAN}\"/go 全自动开发一个项目\"${RESET}"
echo ""

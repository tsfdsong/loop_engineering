#!/usr/bin/env bash
# LoopEngine 一键安装/更新脚本
# 自动检测 AI 编程工具并执行对应安装命令
#
# 用法:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash          # 新安装
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash -s -- --update  # 更新
#   或
#   bash install.sh              # 新安装
#   bash install.sh --update     # 更新已安装的插件

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

# ── 检查是否为更新模式 ─────────────────────────────────────
IS_UPDATE=false
if [ "${1:-}" = "--update" ] || [ "${1:-}" = "-u" ]; then
    IS_UPDATE=true
    echo -e "${BOLD}🔄 更新模式：将更新已安装的插件到最新版本${RESET}"
    echo ""
fi

if [ ${#DETECTED[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  未检测到已知的 AI 编程工具。${RESET}"
    echo ""
    echo "手动安装方式："
    echo "  git clone $REPO_URL ~/.loopengine"
    echo "  然后参考: $REPO_URL#readme"
    exit 0
fi

if $IS_UPDATE; then
    echo -e "${BOLD}📦 开始更新 LoopEngine...${RESET}"
else
    echo -e "${BOLD}📦 开始安装 LoopEngine...${RESET}"
fi
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

# ── ZCode 桌面版（更新模式） ──────────────────────────────
if $IS_UPDATE; then
    ZCODE_PKG=""
    if [ -d "$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
        ZCODE_PKG="$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin"
    elif [ -d "$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
        ZCODE_PKG="$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin"
    fi
    ZCODE_CACHE="$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/1.0.0"

    if [ -n "$ZCODE_PKG" ] || [ -d "$ZCODE_CACHE" ]; then
        echo -e "${CYAN}▶  更新 ZCode 桌面版...${RESET}"
        if [ -n "$ZCODE_PKG" ] && [ -d "$ZCODE_PKG" ]; then
            echo -e "  📦 更新内置包目录..."
            (cd "$ZCODE_PKG" && git pull 2>/dev/null) && \
                echo -e "  ${GREEN}✅${RESET} 内置包已更新" || \
                echo -e "  ${YELLOW}⚠️${RESET} git pull 失败，请手动 git pull"
        fi
        if [ -n "$ZCODE_PKG" ] && [ -d "$ZCODE_PKG" ]; then
            echo -e "  🔄 同步到 CLI 缓存..."
            mkdir -p "$ZCODE_CACHE"
            cp -r "$ZCODE_PKG/"* "$ZCODE_CACHE/" 2>/dev/null && \
                echo -e "  ${GREEN}✅${RESET} CLI 缓存已同步" || \
                echo -e "  ${YELLOW}⚠️${RESET} 同步失败"
        fi
        SKILL_COUNT=$(ls -1 "$ZCODE_CACHE/skills/" 2>/dev/null | wc -l)
        echo -e "  📊 技能数量: ${GREEN}${SKILL_COUNT}${RESET}"
        echo -e "  ${GREEN}✅${RESET} ZCode 更新完成"
        echo -e "  ${YELLOW}⚠️${RESET} 请重启 ZCode 桌面版使更新生效"
        ((INSTALLED++)) || true
        echo ""
    fi
fi

# ── 手动引导平台 ─────────────────────────────────────────
echo -e "${CYAN}▶  Cursor IDE${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  在 Cursor 中执行: /add-plugin tsfdsong/loop_engineering"
echo ""

echo -e "${CYAN}▶  ZCode 桌面版${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  ZCode 桌面版 v3.1.8+ 需手动安装到内置包目录："
echo ""
echo -e "  ${BOLD}PowerShell (管理员)${RESET}:"
echo -e "  git clone $REPO_URL \"\$env:LOCALAPPDATA\\Programs\\ZCode\\resources\\glm\\packages\\loopengine-plugin\""
echo -e "  mkdir -p \"\$env:USERPROFILE\\.zcode\\cli\\plugins\\cache\\zcode-plugins-official\\loopengine\\1.0.0\""
echo -e "  xcopy \"\$env:LOCALAPPDATA\\Programs\\ZCode\\resources\\glm\\packages\\loopengine-plugin\\*\" \"\$env:USERPROFILE\\.zcode\\cli\\plugins\\cache\\zcode-plugins-official\\loopengine\\1.0.0\\\" /E /I /Y"
echo -e "  mkdir \"\$env:USERPROFILE\\.zcode\\cli\\plugins\\data\\loopengine@zcode-plugins-official\""
echo ""
echo -e "  ${BOLD}然后编辑两个配置文件${RESET}:"
echo -e "  1. marketplace.json: 在 zcode-plugins-official 市场中添加 loopengine 条目"
echo -e "  2. config.json: 在 enabledPlugins 中添加 \"loopengine@zcode-plugins-official\": true"
echo -e "  ${BOLD}重启 ZCode 桌面版${RESET}"
echo -e "  详见: $REPO_URL/blob/main/docs/zcode-install-guide.md"
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
if $IS_UPDATE; then
    echo -e "${BOLD}📊 更新总结${RESET}"
else
    echo -e "${BOLD}📊 安装总结${RESET}"
fi
echo -e "  自动安装: ${GREEN}$INSTALLED${RESET} 个平台成功"
if [ $FAILED -gt 0 ]; then
    echo -e "  需手动安装: ${YELLOW}$FAILED${RESET} 个平台"
fi
echo ""

if $IS_UPDATE; then
    echo -e "${BOLD}🎉 LoopEngine 更新完成！${RESET}"
    echo ""
    echo -e "${BOLD}📋 本次更新内容${RESET}:"
    echo -e "  🔴 ${BOLD}新增 MCP 红线规则${RESET} — 任何理解代码的操作必须先用 MCP 工具"
    echo -e "  📝 适用范围从\"修改代码前\"扩展为\"所有理解代码的操作\""
    echo -e "  ⚡ 标准流程: get_repo_map → get_file_outline → search_symbols → Read(仅精确行)"
    echo -e "  🚨 违规判定: 连续 3 次直接 Read 全文件未用 MCP = 红线事故"
    echo ""
    echo -e "${YELLOW}⚠️  重要提醒${RESET}:"
    echo -e "  • ZCode 桌面版用户: 请${BOLD}重启${RESET} ZCode 使更新生效"
    echo -e "  • 其他平台: 新会话自动生效"
else
    echo -e "${BOLD}🎉 LoopEngine 安装完成！${RESET}"
fi
echo ""
echo -e "  验证安装: 打开新的 AI 会话，发送:"
echo -e "  ${CYAN}\"Tell me about LoopEngine\"${RESET}"
echo -e "  或直接使用:"
echo -e "  ${CYAN}\"/loop 帮我实现一个功能\"${RESET}"
echo -e "  ${CYAN}\"/go 全自动开发一个项目\"${RESET}"
echo ""

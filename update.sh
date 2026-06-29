#!/usr/bin/env bash
# LoopEngine 更新脚本 v1.0
# 一键更新所有已安装平台的 LoopEngine 插件到最新版本
#
# 用法:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/update.sh | bash
#   或
#   bash update.sh

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
echo -e "${BOLD}${CYAN}║     LoopEngine — 循环工程全家桶 更新脚本 v1.0    ║${RESET}"
echo -e "${BOLD}${CYAN}║         一键更新所有平台到最新版本                ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

UPDATED=0
SKIPPED=0
FAILED=0

# ═══════════════════════════════════════════════════════════
# ZCode 桌面版更新
# ═══════════════════════════════════════════════════════════
ZCODE_PACKAGES_DIR=""
if [ -d "$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
    ZCODE_PACKAGES_DIR="$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin"
elif [ -d "$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
    ZCODE_PACKAGES_DIR="$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin"
fi

# 自动检测实际安装的版本（避免硬编码 1.0.0 与未来 1.0.2/1.1.0 等版本不一致）
ZCODE_CACHE_BASE="$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
if [ -d "$ZCODE_CACHE_BASE/1.0.1" ]; then
    ZCODE_CACHE_DIR="$ZCODE_CACHE_BASE/1.0.1"
elif [ -d "$ZCODE_CACHE_BASE/1.0.0" ]; then
    ZCODE_CACHE_DIR="$ZCODE_CACHE_BASE/1.0.0"
else
    # 兜底：取该目录下最新的版本号
    ZCODE_CACHE_DIR=$(ls -1d "$ZCODE_CACHE_BASE"/*/ 2>/dev/null | sort -V | tail -1 | sed 's:/$::' || echo "")
fi

if [ -n "$ZCODE_PACKAGES_DIR" ] || [ -d "$ZCODE_CACHE_DIR" ]; then
    echo -e "${CYAN}▶  更新 ZCode 桌面版...${RESET}"

    # Step 1: 更新内置包目录
    if [ -n "$ZCODE_PACKAGES_DIR" ] && [ -d "$ZCODE_PACKAGES_DIR" ]; then
        echo -e "  📦 更新内置包目录..."
        if command -v git &> /dev/null; then
            (cd "$ZCODE_PACKAGES_DIR" && git pull 2>/dev/null) && \
                echo -e "  ${GREEN}✅${RESET} 内置包目录已更新 (git pull)" || \
                echo -e "  ${YELLOW}⚠️${RESET} git pull 失败，请手动更新"
        else
            echo -e "  ${YELLOW}⚠️${RESET} 未找到 git，请手动更新内置包目录"
        fi
    fi

    # Step 2: 同步到 CLI 缓存
    if [ -n "$ZCODE_PACKAGES_DIR" ] && [ -d "$ZCODE_PACKAGES_DIR" ]; then
        echo -e "  🔄 同步到 CLI 缓存..."
        mkdir -p "$ZCODE_CACHE_DIR"
        if command -v rsync &> /dev/null; then
            rsync -a --delete "$ZCODE_PACKAGES_DIR/" "$ZCODE_CACHE_DIR/" 2>/dev/null && \
                echo -e "  ${GREEN}✅${RESET} CLI 缓存已同步 (rsync)" || \
                echo -e "  ${YELLOW}⚠️${RESET} rsync 失败"
        else
            # 用 cp 兜底
            cp -r "$ZCODE_PACKAGES_DIR/"* "$ZCODE_CACHE_DIR/" 2>/dev/null && \
                echo -e "  ${GREEN}✅${RESET} CLI 缓存已同步 (cp)" || \
                echo -e "  ${YELLOW}⚠️${RESET} cp 同步失败"
        fi
    fi

    # Step 3: 确保 data 目录存在
    ZCODE_DATA_DIR="$HOME/.zcode/cli/plugins/data/loopengine@zcode-plugins-official"
    if [ ! -d "$ZCODE_DATA_DIR" ]; then
        mkdir -p "$ZCODE_DATA_DIR"
        echo -e "  📁 data 目录已创建"
    fi

    # Step 4: 验证技能数量
    SKILL_COUNT=$(ls -1 "$ZCODE_CACHE_DIR/skills/" 2>/dev/null | wc -l)
    echo -e "  📊 技能数量: ${GREEN}${SKILL_COUNT}${RESET}"

    # Step 5: 调用 MCP 自愈脚本（保证 ZCode 重启后 MCP 不丢失）
    # 根因：ZCode 启动时重写 marketplace.json，CLI 缓存 plugin.json 无 mcpServers → MCP 工具消失
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    ENSURE_SCRIPT="$SCRIPT_DIR/scripts/zcode-mcp-ensure.sh"
    if [ -f "$ENSURE_SCRIPT" ]; then
        echo -e "  ${CYAN}▶  MCP 自愈（修复 plugin.json mcpServers + marketplace 注册）...${RESET}"
        if bash "$ENSURE_SCRIPT" --quiet; then
            echo -e "  ${GREEN}✅${RESET} MCP 自愈完成"
        else
            echo -e "  ${YELLOW}⚠️${RESET}  MCP 自愈未完全通过，可手动执行: bash $ENSURE_SCRIPT"
        fi
    else
        echo -e "  ${YELLOW}ℹ️${RESET}  未找到 scripts/zcode-mcp-ensure.sh，跳过 MCP 自愈"
    fi

    # Step 6: 同步 skills 到 ~/.agents/skills/ 优先路径（修复 ZCode 加载 v5.4 旧版的 bug）
    # 根因（2026-06-29 实测发现）：
    #   ZCode 桌面版启动时优先扫描 ~/.agents/skills/ 目录里的 SKILL.md，
    #   marketplace.json 中 loopengine 注册失败时（ZCode 启动会重写）会回退到该路径，
    #   导致 v5.4 旧版 skill-hub 遮蔽 CLI 缓存里的 v6.0 新版。
    # 治本：把 skills/ 同步到 ~/.agents/skills/，让 ZCode 直接从此路径加载最新技能。
    AGENTS_SKILLS_DIR="$HOME/.agents/skills"
    if [ -d "$ZCODE_CACHE_DIR/skills" ]; then
        echo -e "  ${CYAN}▶  同步 skills 到 ~/.agents/skills/ 优先路径...${RESET}"
        mkdir -p "$AGENTS_SKILLS_DIR"
        # 一次性备份旧版 skill-hub（仅当 .v5.4.backup 尚未存在时）
        if [ -d "$AGENTS_SKILLS_DIR/skill-hub" ] && [ ! -d "$AGENTS_SKILLS_DIR/skill-hub.v5.4.backup" ]; then
            mv "$AGENTS_SKILLS_DIR/skill-hub" "$AGENTS_SKILLS_DIR/skill-hub.v5.4.backup"
            echo -e "  ${YELLOW}📦${RESET}  备份旧版 skill-hub → skill-hub.v5.4.backup"
        fi
        if cp -r "$ZCODE_CACHE_DIR/skills/." "$AGENTS_SKILLS_DIR/" 2>/dev/null; then
            SKILL_COUNT=$(ls -1 "$AGENTS_SKILLS_DIR" 2>/dev/null | grep -c 'SKILL\.md$' || true)
            echo -e "  ${GREEN}✅${RESET} skills 已同步到 ~/.agents/skills/（含 $SKILL_COUNT 个 SKILL.md）"
        else
            echo -e "  ${RED}❌${RESET}  skills 同步失败，可手动执行: cp -r $ZCODE_CACHE_DIR/skills/. $AGENTS_SKILLS_DIR/"
        fi
    else
        echo -e "  ${YELLOW}ℹ️${RESET}  未找到 CLI 缓存 skills 目录: $ZCODE_CACHE_DIR/skills，跳过 ~/.agents/skills/ 同步"
    fi

    echo -e "  ${GREEN}✅${RESET} ZCode 桌面版更新完成"
    echo -e "  ${YELLOW}⚠️${RESET} 请重启 ZCode 桌面版使更新生效"
    echo -e "  ${YELLOW}💡${RESET}  重启后若 MCP 工具仍消失，跑: bash $SCRIPT_DIR/scripts/zcode-mcp-ensure.sh"
    ((UPDATED++)) || true
    echo ""
else
    echo -e "${CYAN}▶  ZCode 桌面版${RESET} — 未检测到安装，跳过"
    ((SKIPPED++)) || true
    echo ""
fi

# ═══════════════════════════════════════════════════════════
# Claude Code 更新
# ═══════════════════════════════════════════════════════════
if command -v claude &> /dev/null; then
    echo -e "${CYAN}▶  更新 Claude Code...${RESET}"
    if claude plugin update loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Claude Code 更新完成"
        ((UPDATED++)) || true
    else
        # 降级: 重新安装
        echo -e "  ${YELLOW}⚠️${RESET} update 命令不可用，尝试重新安装..."
        if claude plugin install loopengine 2>/dev/null; then
            echo -e "  ${GREEN}✅${RESET} Claude Code 重新安装完成"
            ((UPDATED++)) || true
        else
            echo -e "  ${RED}❌${RESET} Claude Code 更新失败"
            ((FAILED++)) || true
        fi
    fi
    echo ""
fi

# ═══════════════════════════════════════════════════════════
# Codex 更新
# ═══════════════════════════════════════════════════════════
if command -v codex &> /dev/null; then
    echo -e "${CYAN}▶  更新 Codex...${RESET}"
    if codex plugin update loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Codex 更新完成"
        ((UPDATED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET} 请在 Codex 插件市场中手动更新 loopengine"
        ((SKIPPED++)) || true
    fi
    echo ""
fi

# ═══════════════════════════════════════════════════════════
# Gemini CLI 更新
# ═══════════════════════════════════════════════════════════
if command -v gemini &> /dev/null; then
    echo -e "${CYAN}▶  更新 Gemini CLI...${RESET}"
    if gemini extensions update loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Gemini CLI 更新完成"
        ((UPDATED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET} 请手动执行: gemini extensions install $REPO_URL"
        ((SKIPPED++)) || true
    fi
    echo ""
fi

# ═══════════════════════════════════════════════════════════
# GitHub Copilot CLI 更新
# ═══════════════════════════════════════════════════════════
if command -v copilot &> /dev/null; then
    echo -e "${CYAN}▶  更新 GitHub Copilot CLI...${RESET}"
    if copilot plugin update loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} GitHub Copilot CLI 更新完成"
        ((UPDATED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET} 请手动执行: copilot plugin install loopengine@tsfdsong"
        ((SKIPPED++)) || true
    fi
    echo ""
fi

# ═══════════════════════════════════════════════════════════
# Pi 更新
# ═══════════════════════════════════════════════════════════
if command -v pi &> /dev/null; then
    echo -e "${CYAN}▶  更新 Pi...${RESET}"
    if pi update loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Pi 更新完成"
        ((UPDATED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET} 请手动执行: pi install git:$REPO_URL"
        ((SKIPPED++)) || true
    fi
    echo ""
fi

# ═══════════════════════════════════════════════════════════
# 手动更新引导
# ═══════════════════════════════════════════════════════════
echo -e "${CYAN}▶  Cursor IDE${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  在 Cursor 中执行: /add-plugin tsfdsong/loop_engineering"
echo ""

echo -e "${CYAN}▶  OpenCode${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  在 opencode.json 中更新插件版本号"
echo ""

echo -e "${CYAN}▶  Kimi Code${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  执行: /plugins install $REPO_URL"
echo ""

# ═══════════════════════════════════════════════════════════
# 总结
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}📊 更新总结${RESET}"
echo -e "  已更新: ${GREEN}$UPDATED${RESET} 个平台"
if [ $SKIPPED -gt 0 ]; then
    echo -e "  已跳过: ${YELLOW}$SKIPPED${RESET} 个平台（未安装或需手动更新）"
fi
if [ $FAILED -gt 0 ]; then
    echo -e "  失败:   ${RED}$FAILED${RESET} 个平台"
fi
echo ""

if [ $UPDATED -gt 0 ]; then
    echo -e "${BOLD}🎉 LoopEngine 更新完成！${RESET}"
    echo ""
    echo -e "${BOLD}📋 更新内容（v1.0.0+）${RESET}:"
    echo -e "  🔴 ${BOLD}新增 MCP 红线规则${RESET} — 任何理解代码的操作必须先用 MCP 工具"
    echo -e "  📝 适用范围从\"修改代码前\"扩展为\"所有理解代码的操作\""
    echo -e "  ⚡ 标准流程: get_repo_map → get_file_outline → search_symbols → Read(仅精确行)"
    echo -e "  🚨 违规判定: 连续 3 次直接 Read 全文件未用 MCP = 红线事故"
    echo ""
    echo -e "${YELLOW}⚠️  重要提醒${RESET}:"
    echo -e "  • ZCode 桌面版用户: 请${BOLD}重启${RESET} ZCode 使更新生效"
    echo -e "  • Claude Code 用户: 新会话自动生效"
    echo -e "  • 其他平台: 新会话自动生效"
    echo ""
    echo -e "  验证更新: 打开新的 AI 会话，发送:"
    echo -e "  ${CYAN}\"告诉我 MCP 红线规则是什么\"${RESET}"
else
    echo -e "${YELLOW}⚠️  未检测到已安装的 LoopEngine，请先安装:${RESET}"
    echo -e "  ${CYAN}curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash${RESET}"
fi
echo ""

#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# scripts/install/macos.sh — LoopEngine macOS 平台实现
# ════════════════════════════════════════════════════════════
# macOS 特定逻辑：
#   • Step 3: MCP 三件套（pip3 + --break-system-packages 兼容 PEP 668）
#   • Step 4: 桌面版 ZCode MCP（~/Library/Python/3.*/bin/ 路径）
# 由 install.sh 通过 source 加载
#
# v1.2.4 新增（2026-07-01 跨平台架构）：
#   • 从 v1.2.3 install.sh 提取 macOS 特定代码
#   • 暴露函数：install_mcp_packages_macos / write_zcode_desktop_config_macos
#   • SENTINEL 防重入
# ════════════════════════════════════════════════════════════

# SENTINEL 防重入
if [ -n "${_MACOS_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_MACOS_LOADED=1

# ── install_mcp_packages_macos ────────────────────────────
# Step 3：安装 MCP 三件套（macOS）
# 修复 2026-07-01：macOS Homebrew Python 默认装 ~/Library/Python/3.*/bin/
#   - 优先用 pip3（无 pip）
#   - 加 --break-system-packages 解决 PEP 668
install_mcp_packages_macos() {
    # 格式：pkg|cmd|is_mcp_server
    local mcp_packages=(
        "jcodemunch-mcp|jcodemunch-mcp|true"
        "headroom|headroom|false"
        "repomix|repomix|true"
    )

    local pip_cmd
    if ! pip_cmd=$(common_detect_pip_cmd); then
        echo -e "  ${_YELLOW}⚠${_RESET}  未找到 pip/pip3，跳过 MCP 包安装"
        return 0
    fi

    for entry in "${mcp_packages[@]}"; do
        IFS='|' read -r pkg cmd is_mcp <<< "$entry"
        if command -v "$cmd" >/dev/null 2>&1; then
            echo -e "  ${_GREEN}✅${_RESET} ${cmd} 已装"
            continue
        fi
        if [[ "$pkg" == *"repomix"* ]]; then
            if command -v npm >/dev/null 2>&1; then
                npm install -g "$pkg" 2>/dev/null && \
                    echo -e "  ${_GREEN}✅${_RESET} ${pkg} (npm)" || true
            fi
        else
            # pip3 --user 优先；失败则 --break-system-packages（PEP 668）
            if $pip_cmd install --user "$pkg" >/dev/null 2>&1; then
                echo -e "  ${_GREEN}✅${_RESET} ${pkg} (${pip_cmd} --user)"
            elif $pip_cmd install --user --break-system-packages "$pkg" >/dev/null 2>&1; then
                echo -e "  ${_GREEN}✅${_RESET} ${pkg} (${pip_cmd} --user --break-system-packages)"
            else
                echo -e "  ${_YELLOW}⚠${_RESET}  ${pkg} 安装失败 — 手动: ${pip_cmd} install --user $pkg"
            fi
        fi
        if [ "$is_mcp" = "false" ]; then
            echo -e "  ${_CYAN}ℹ${_RESET}  ${cmd} 是 Python 库（非 MCP server），跳过桌面配置"
        fi
    done
}

# ── detect_mcp_exe_macos ──────────────────────────────────
# macOS 路径 fallback：~/Library/Python/3.*/bin/<name>
# 入参：<cmd_name>
# 输出：绝对路径 或 空字符串
detect_mcp_exe_macos() {
    local cmd_name="$1"
    # 1) PATH 内查找
    if command -v "$cmd_name" >/dev/null 2>&1; then
        command -v "$cmd_name"
        return 0
    fi
    # 2) macOS Homebrew Python 用户脚本目录（3.9 - 3.14）
    for d in "$HOME/Library/Python/3.9/bin" \
             "$HOME/Library/Python/3.10/bin" \
             "$HOME/Library/Python/3.11/bin" \
             "$HOME/Library/Python/3.12/bin" \
             "$HOME/Library/Python/3.13/bin" \
             "$HOME/Library/Python/3.14/bin"; do
        if [ -f "$d/$cmd_name" ]; then
            echo "$d/$cmd_name"
            return 0
        fi
    done
    return 1
}

# ── write_zcode_desktop_config_macos ──────────────────────
# Step 4：写入 ZCode 桌面版 MCP 配置（macOS）
write_zcode_desktop_config_macos() {
    local cfg="$HOME/.zcode/cli/config.json"

    local jcode_exe repo_exe
    jcode_exe=$(detect_mcp_exe_macos jcodemunch-mcp) || jcode_exe=""
    repo_exe=$(detect_mcp_exe_macos repomix) || repo_exe=""

    if [ -z "$jcode_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  jcodemunch/repomix 未全部找到，跳过桌面版配置写入"
        echo -e "  ${_YELLOW}⚠${_RESET}  手动: pip3 install --user --break-system-packages jcodemunch-mcp && npm i -g repomix"
        return 0
    fi

    mkdir -p "$(dirname "$cfg")"
    if python "$COMMON_SCRIPT_DIR/scripts/merge_zcode_config.py" "$cfg" "$jcode_exe" "$repo_exe"; then
        echo -e "  ${_GREEN}✅${_RESET} [ZCode 桌面版 MCP] $cfg"
        COMMON_TARGETS+=("ZCode 桌面版 MCP:$cfg")
    else
        echo -e "  ${_RED}❌${_RESET} 合并 $cfg 失败，详见上方 Python 错误"
        return 1
    fi
}

# ── macos_main ────────────────────────────────────────────
# 平台入口：被 install.sh 调用
# v1.3.0 新增 Step 5.5（Cursor MCP 合并），仅 detect 到 cursor 时执行
macos_main() {
    echo ""
    echo -e "${_BOLD}🔌 Step 3: 安装 MCP 三件套（macOS）...${_RESET}"
    install_mcp_packages_macos

    echo ""
    echo -e "${_BOLD}⚙️  Step 4: 配置 ZCode 桌面版 MCP (macOS · ~/.zcode/cli/config.json)...${_RESET}"
    write_zcode_desktop_config_macos

    echo ""
    echo -e "${_BOLD}🌐 Step 5: 注入全局红线规则...${_RESET}"
    common_inject_red_lines

    # v1.3.0：Cursor MCP 合并写入 ~/.cursor/mcp.json（仅 detect 到 cursor 时执行）
    if [[ " ${COMMON_AGENT_LIST:-} " == *" cursor "* ]]; then
        echo ""
        echo -e "${_BOLD}🎯 Step 5.5: 配置 Cursor MCP (macOS · ~/.cursor/mcp.json)...${_RESET}"
        common_deploy_cursor_mcp
    else
        echo -e "  ${_CYAN}ℹ${_RESET}  跳过 Cursor MCP（detect 结果不含 cursor）"
    fi
}
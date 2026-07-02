#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# scripts/install/linux.sh — LoopEngine Linux 平台实现
# ════════════════════════════════════════════════════════════
# Linux 特定逻辑：
#   • Step 3: MCP 三件套（pip3 + ~/.local/bin）
#   • Step 4: 桌面版 ZCode MCP（~/.local/bin 路径）
# 由 install.sh 通过 source 加载
#
# v1.2.4 新增（2026-07-01 跨平台架构）：
#   • 从 v1.2.3 install.sh 提取 Linux 特定代码
#   • 路径 fallback 优先 ~/.local/bin（PEP 668 --user 默认）
#   • SENTINEL 防重入
# ════════════════════════════════════════════════════════════

# SENTINEL 防重入
if [ -n "${_LINUX_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_LINUX_LOADED=1

# ── detect_mcp_exe_linux ──────────────────────────────────
# Linux 路径 fallback：
#   1) PATH 内查找
#   2) ~/.local/bin/<name>（PEP 668 --user 默认）
detect_mcp_exe_linux() {
    local cmd_name="$1"

    # 1) PATH 内
    if command -v "$cmd_name" >/dev/null 2>&1; then
        command -v "$cmd_name"
        return 0
    fi

    # 2) ~/.local/bin（pip3 --user 默认）
    local p="$HOME/.local/bin/$cmd_name"
    [ -f "$p" ] && { echo "$p"; return 0; }

    return 1
}

# ── install_mcp_packages_linux ────────────────────────────
# Step 3：安装 MCP 三件套（Linux）
# 多数 Linux distro 无 PEP 668，但新版 Debian/Ubuntu 可能启用
install_mcp_packages_linux() {
    local mcp_packages=(
        "jcodemunch-mcp|jcodemunch-mcp|true"
        "headroom|headroom|false"
        "repomix|repomix|true"
    )

    local pip_cmd
    if ! pip_cmd=$(common_detect_pip_cmd); then
        echo -e "  ${_YELLOW}⚠${_RESET}  未找到 pip/pip3，跳过 MCP 包安装"
        echo -e "  ${_YELLOW}⚠${_RESET}  手动: sudo apt install python3-pip  # Debian/Ubuntu"
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
            else
                echo -e "  ${_YELLOW}⚠${_RESET}  npm 未装 — 手动: sudo apt install npm && npm i -g repomix"
            fi
        else
            # pip3 --user 优先；PEP 668 启用时加 --break-system-packages
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

# ── write_zcode_desktop_config_linux ──────────────────────
# Step 4：写入 ZCode 桌面版 MCP 配置（Linux）
write_zcode_desktop_config_linux() {
    local cfg="$HOME/.zcode/cli/config.json"

    local jcode_exe repo_exe
    jcode_exe=$(detect_mcp_exe_linux jcodemunch-mcp) || jcode_exe=""
    repo_exe=$(detect_mcp_exe_linux repomix) || repo_exe=""

    if [ -z "$jcode_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  jcodemunch/repomix 未全部找到，跳过桌面版配置写入"
        echo -e "  ${_YELLOW}⚠${_RESET}  手动: ${pip_cmd:-pip3} install --user jcodemunch-mcp && npm i -g repomix"
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

# ── linux_main ────────────────────────────────────────────
# 平台入口：被 install.sh 调用
# v1.3.0 新增 Step 5.5（Cursor MCP 合并），仅 detect 到 cursor 时执行
linux_main() {
    echo ""
    echo -e "${_BOLD}🔌 Step 3: 安装 MCP 三件套（Linux）...${_RESET}"
    install_mcp_packages_linux

    echo ""
    echo -e "${_BOLD}⚙️  Step 4: 配置 ZCode 桌面版 MCP (Linux · ~/.zcode/cli/config.json)...${_RESET}"
    write_zcode_desktop_config_linux

    echo ""
    echo -e "${_BOLD}🌐 Step 5: 注入全局红线规则...${_RESET}"
    common_inject_red_lines

    # v1.3.0：Cursor MCP 合并写入 ~/.cursor/mcp.json（仅 detect 到 cursor 时执行）
    if [[ " ${COMMON_AGENT_LIST:-} " == *" cursor "* ]]; then
        echo ""
        echo -e "${_BOLD}🎯 Step 5.5: 配置 Cursor MCP (Linux · ~/.cursor/mcp.json)...${_RESET}"
        common_deploy_cursor_mcp
    else
        echo -e "  ${_CYAN}ℹ${_RESET}  跳过 Cursor MCP（detect 结果不含 cursor）"
    fi
}
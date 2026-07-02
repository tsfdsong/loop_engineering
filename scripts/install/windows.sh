#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# scripts/install/windows.sh — LoopEngine Windows 平台实现
# ════════════════════════════════════════════════════════════
# Windows 特定逻辑（Git Bash / MSYS2 / Cygwin 环境）：
#   • Step 3: MCP 三件套（py -m pip / .exe/.cmd 优先）
#   • Step 4: 桌面版 ZCode MCP（%APPDATA% 路径 + 路径转 forward slash）
# 由 install.sh 通过 source 加载
#
# v1.2.4 新增（2026-07-01 跨平台架构）：
#   • 从 v1.2.3 install.sh 提取 Windows 特定代码
#   • 路径转 forward slash（ZCode JSON 配置要求 / 分隔）
#   • SENTINEL 防重入
# ════════════════════════════════════════════════════════════

# SENTINEL 防重入
if [ -n "${_WINDOWS_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_WINDOWS_LOADED=1

# ── to_forward_slashes ────────────────────────────────────
# Windows 路径 \ → /（ZCode JSON 配置要求）
to_forward_slashes() {
    echo "$1" | sed 's|\\|/|g'
}

# ── detect_mcp_exe_windows ────────────────────────────────
# Windows 路径 fallback：
#   1) PATH 内查找
#   2) %APPDATA%\Python\Python*\Scripts\<name>.exe
#   3) %APPDATA%\npm\<name>.cmd
detect_mcp_exe_windows() {
    local cmd_name="$1"
    local cmd_exe="${cmd_name}.exe"
    local cmd_cmd="${cmd_name}.cmd"

    # 1) PATH 内
    for c in "$cmd_exe" "$cmd_cmd" "$cmd_name"; do
        if command -v "$c" >/dev/null 2>&1; then
            command -v "$c"
            return 0
        fi
    done

    # 2) Python Scripts 目录（3.9 - 3.14）
    local appdata="${APPDATA:-$HOME/AppData/Roaming}"
    for ver in 3.9 3.10 3.11 3.12 3.13 3.14; do
        local p="$appdata/Python/Python${ver}/Scripts/$cmd_exe"
        [ -f "$p" ] && { echo "$p"; return 0; }
    done

    # 3) npm 全局目录
    local p="$appdata/npm/$cmd_cmd"
    [ -f "$p" ] && { echo "$p"; return 0; }

    return 1
}

# ── install_mcp_packages_windows ──────────────────────────
# Step 3：安装 MCP 三件套（Windows Git Bash）
install_mcp_packages_windows() {
    local mcp_packages=(
        "jcodemunch-mcp|jcodemunch-mcp|true"
        "headroom|headroom|false"
        "repomix|repomix|true"
    )

    # Windows Python 通常用 py launcher + pip
    local pip_cmd=""
    if command -v py >/dev/null 2>&1; then
        pip_cmd="py -m pip"
    elif command -v pip3 >/dev/null 2>&1; then
        pip_cmd="pip3"
    elif command -v pip >/dev/null 2>&1; then
        pip_cmd="pip"
    fi

    for entry in "${mcp_packages[@]}"; do
        IFS='|' read -r pkg cmd is_mcp <<< "$entry"
        local exe="${cmd}.exe"
        if command -v "$exe" >/dev/null 2>&1 || command -v "${cmd}.cmd" >/dev/null 2>&1; then
            echo -e "  ${_GREEN}✅${_RESET} ${cmd} 已装"
            continue
        fi
        if [[ "$pkg" == *"repomix"* ]]; then
            if command -v npm >/dev/null 2>&1; then
                npm install -g "$pkg" 2>/dev/null && \
                    echo -e "  ${_GREEN}✅${_RESET} ${pkg} (npm)" || true
            fi
        else
            if [ -n "$pip_cmd" ]; then
                $pip_cmd install --user "$pkg" 2>/dev/null && \
                    echo -e "  ${_GREEN}✅${_RESET} ${pkg} (${pip_cmd} --user)" || true
            fi
        fi
        if [ "$is_mcp" = "false" ]; then
            echo -e "  ${_CYAN}ℹ${_RESET}  ${cmd} 是 Python 库（非 MCP server），跳过桌面配置"
        fi
    done
}

# ── write_zcode_desktop_config_windows ────────────────────
# Step 4：写入 ZCode 桌面版 MCP 配置（Windows）
write_zcode_desktop_config_windows() {
    local cfg_unix="$HOME/.zcode/cli/config.json"

    local jcode_exe repo_exe
    jcode_exe=$(detect_mcp_exe_windows jcodemunch-mcp) || jcode_exe=""
    repo_exe=$(detect_mcp_exe_windows repomix) || repo_exe=""

    if [ -z "$jcode_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  jcodemunch/repomix 未全部找到，跳过桌面版配置写入"
        echo -e "  ${_YELLOW}⚠${_RESET}  手动: py -m pip install --user jcodemunch-mcp && npm i -g repomix"
        return 0
    fi

    # 路径转 forward slash（ZCode JSON 配置要求）
    jcode_exe=$(to_forward_slashes "$jcode_exe")
    repo_exe=$(to_forward_slashes "$repo_exe")

    mkdir -p "$(dirname "$cfg_unix")"
    if python "$COMMON_SCRIPT_DIR/scripts/merge_zcode_config.py" "$cfg_unix" "$jcode_exe" "$repo_exe"; then
        echo -e "  ${_GREEN}✅${_RESET} [ZCode 桌面版 MCP] $cfg_unix"
        COMMON_TARGETS+=("ZCode 桌面版 MCP:$cfg_unix")
    else
        echo -e "  ${_RED}❌${_RESET} 合并 $cfg_unix 失败，详见上方 Python 错误"
        return 1
    fi
}

# ── windows_main ──────────────────────────────────────────
# 平台入口：被 install.sh 调用
# v1.3.0 新增 Step 5.5（Cursor MCP 合并），仅 detect 到 cursor 时执行
windows_main() {
    echo ""
    echo -e "${_BOLD}🔌 Step 3: 安装 MCP 三件套（Windows）...${_RESET}"
    install_mcp_packages_windows

    echo ""
    echo -e "${_BOLD}⚙️  Step 4: 配置 ZCode 桌面版 MCP (Windows · ~/.zcode/cli/config.json)...${_RESET}"
    write_zcode_desktop_config_windows

    echo ""
    echo -e "${_BOLD}🌐 Step 5: 注入全局红线规则...${_RESET}"
    common_inject_red_lines

    # v1.3.0：Cursor MCP 合并写入 ~/.cursor/mcp.json（仅 detect 到 cursor + common_deploy_cursor_mcp 自带检测）
    if [[ " ${COMMON_AGENT_LIST:-} " == *" cursor "* ]]; then
        echo ""
        echo -e "${_BOLD}🎯 Step 5.5: 配置 Cursor MCP (Windows · ~/.cursor/mcp.json)...${_RESET}"
        common_deploy_cursor_mcp
    else
        echo -e "  ${_CYAN}ℹ${_RESET}  跳过 Cursor MCP（detect 结果不含 cursor）"
    fi
}
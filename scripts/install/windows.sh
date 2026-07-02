#!/usr/bin/env bash
# scripts/install/windows.sh — LoopEngine Windows 平台入口
# v1.3.1 瘦身：原 detect_mcp_exe_windows / install_mcp_packages_windows /
# write_zcode_desktop_config_windows 3 函数已合并到 _common.sh:
#   - common_detect_mcp_exe 走 COMMON_MCP_FALLBACK_PATHS_WINDOWS 表
#   - common_install_mcp_packages / common_write_zcode_desktop_config 单函数
#   - common_run_platform_steps 主驱动 Step 3-5.5
# 本脚本只保留 Windows 特有的 to_forward_slashes + 单行 *_main
if [ -n "${_WINDOWS_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_WINDOWS_LOADED=1

# Windows 路径 \ → /（ZCode / Cursor JSON 配置要求）
to_forward_slashes() {
    echo "$1" | sed 's|\\|/|g'
}

# 平台入口：单行调用 _common.sh 统一驱动
windows_main() {
    common_run_platform_steps windows
}

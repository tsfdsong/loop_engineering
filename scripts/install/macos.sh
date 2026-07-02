#!/usr/bin/env bash
# scripts/install/macos.sh — LoopEngine macOS 平台入口
# v1.3.1 瘦身：原 install_mcp_packages_macos / detect_mcp_exe_macos /
# write_zcode_desktop_config_macos 3 函数已合并到 _common.sh:
#   - common_detect_mcp_exe 走 COMMON_MCP_FALLBACK_PATHS_MACOS 表
#   - common_install_mcp_packages / common_write_zcode_desktop_config 单函数
#   - common_run_platform_steps 主驱动 Step 3-5.5
if [ -n "${_MACOS_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_MACOS_LOADED=1

# 平台入口：单行调用 _common.sh 统一驱动
macos_main() {
    common_run_platform_steps macos
}

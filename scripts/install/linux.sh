#!/usr/bin/env bash
# scripts/install/linux.sh — LoopEngine Linux 平台入口
# v1.3.1 瘦身：原 install_mcp_packages_linux / detect_mcp_exe_linux /
# write_zcode_desktop_config_linux 3 函数已合并到 _common.sh:
#   - common_detect_mcp_exe 走 COMMON_MCP_FALLBACK_PATHS_LINUX 表
#   - common_install_mcp_packages / common_write_zcode_desktop_config 单函数
#   - common_run_platform_steps 主驱动 Step 3-5.5
if [ -n "${_LINUX_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_LINUX_LOADED=1

# 平台入口：单行调用 _common.sh 统一驱动
linux_main() {
    common_run_platform_steps linux
}

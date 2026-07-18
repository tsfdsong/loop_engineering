#!/usr/bin/env bash
# agent-browser 环境预检脚本（G0 门禁）
# 用法: bash check-agent-browser.sh
# 返回: 0=全部通过, 1=有失败项
# 输出: 结构化检查报告，供 loop/go 技能解析

set -uo pipefail

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
INFO_COUNT=0

check() {
    local status="$1" name="$2" detail="$3"
    case "$status" in
        pass) PASS_COUNT=$((PASS_COUNT+1)); echo "✅ PASS  $name: $detail" ;;
        fail) FAIL_COUNT=$((FAIL_COUNT+1)); echo "❌ FAIL  $name: $detail" ;;
        warn) WARN_COUNT=$((WARN_COUNT+1)); echo "⚠️  WARN  $name: $detail" ;;
        info) INFO_COUNT=$((INFO_COUNT+1)); echo "ℹ️  INFO  $name: $detail" ;;
    esac
}

echo "═══════════════════════════════════════════════════════════"
echo "  agent-browser 环境预检 (G0 门禁)"
echo "═══════════════════════════════════════════════════════════"

# 1. agent-browser CLI 是否安装
AB_PATH=$(command -v agent-browser 2>/dev/null || where agent-browser 2>/dev/null | head -1)
if [ -n "$AB_PATH" ]; then
    check pass "CLI 安装" "found at $AB_PATH"
else
    check fail "CLI 安装" "agent-browser 未找到 PATH，请运行 npm i -g agent-browser"
    echo "═══════════════════════════════════════════════════════════"
    exit 1
fi

# 2. 版本检查（要求 >= 0.29.0）
AB_VERSION=$(agent-browser --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "0.0.0")
AB_MAJOR=$(echo "$AB_VERSION" | cut -d. -f1)
AB_MINOR=$(echo "$AB_VERSION" | cut -d. -f2)
if [ "${AB_MAJOR:-0}" -gt 0 ] 2>/dev/null || { [ "${AB_MAJOR:-0}" -eq 0 ] 2>/dev/null && [ "${AB_MINOR:-0}" -ge 29 ] 2>/dev/null; }; then
    check pass "版本" "v$AB_VERSION (要求 >= 0.29.0)"
else
    check fail "版本" "v$AB_VERSION 过低，请升级到 >= 0.29.0 (agent-browser upgrade)"
fi

# 3. Chrome + 启动测试（依赖 doctor 的 Launch test 结果，避免重复启动守护进程）
DOCTOR_OUT=$(timeout 15 agent-browser doctor 2>&1 || echo "DOCTOR_TIMEOUT")
if echo "$DOCTOR_OUT" | grep -q "DOCTOR_TIMEOUT"; then
    check warn "Chrome+启动" "doctor 超时（可能有残留守护进程），尝试实测"
    LAUNCH_TEST=$(timeout 8 agent-browser open "about:blank" --json 2>/dev/null | grep -o '"success":true' || echo "")
    if [ -n "$LAUNCH_TEST" ]; then
        agent-browser close --json > /dev/null 2>&1
        check pass "Chrome+启动" "实测启动成功"
    else
        check fail "Chrome+启动" "启动失败，请运行 agent-browser close --all 后重试，或 agent-browser install"
    fi
elif echo "$DOCTOR_OUT" | grep -iA1 "Launch test" | grep -qi "pass"; then
    LAUNCH_TIME=$(echo "$DOCTOR_OUT" | grep -iA1 "Launch test" | grep -oE '[0-9.]+s' | head -1)
    LAUNCH_TIME=${LAUNCH_TIME:-"?"}
    check pass "Chrome+启动" "Headless 启动成功 (${LAUNCH_TIME})"
else
    check fail "Chrome+启动" "doctor 报告启动失败，请运行 agent-browser install"
fi

# 4. 守护进程残留检查
if echo "$DOCTOR_OUT" | grep -qi "No active daemons"; then
    check pass "守护进程" "无残留"
elif echo "$DOCTOR_OUT" | grep -qiE "(active daemon|Session .*pid)"; then
    check warn "守护进程" "有活跃守护进程（正常使用中，或残留需清理：agent-browser close --all）"
else
    check info "守护进程" "状态未知"
fi

# 5. 网络连通性
if echo "$DOCTOR_OUT" | grep -qi "CDN reachable"; then
    check pass "网络" "Chrome CDN 可达"
else
    check warn "网络" "Chrome CDN 不可达（离线环境 Chrome for Testing 下载会失败）"
fi

# 6. MCP 配置检查（多候选路径检测 · 工具无关）
# 候选配置文件（按优先级 · 与 agent-browser-setup.md 附录速查表一致）
CANDIDATES=(
  "./.mcp.json"                              # 项目级 MCP 标准（最优先）
  "$HOME/.zcode/cli/config.json"             # ZCode
  "$HOME/.claude/settings.json"              # Claude Code
  "$HOME/.cursor/mcp.json"                   # Cursor
  "$HOME/.codex/config.toml"                 # Codex
  "$HOME/.gemini/settings.json"              # Gemini CLI
  "$HOME/.trae/config.json"                  # TRAE
)

MCP_CONFIG=""
for cfg in "${CANDIDATES[@]}"; do
    if [ -f "$cfg" ] && grep -q "agent-browser" "$cfg" 2>/dev/null; then
        MCP_CONFIG="$cfg"
        check pass "MCP 配置" "在 $cfg 中检测到 agent-browser"
        break
    fi
done
[ -z "$MCP_CONFIG" ] && check warn "MCP 配置" "未在候选路径检测到 agent-browser（候选: ./.mcp.json、~/.zcode、~/.claude、~/.cursor、~/.codex、~/.gemini、~/.trae）"

# 7. Playwright 残留检查（针对命中的候选配置）
if [ -n "$MCP_CONFIG" ]; then
    if grep -q '"playwright"' "$MCP_CONFIG" 2>/dev/null; then
        check warn "Playwright残留" "$MCP_CONFIG 仍有 playwright 配置（方案 A 应已移除）"
    else
        check pass "Playwright移除" "$MCP_CONFIG 已无 playwright 配置（方案 A 已生效）"
    fi
fi

# 8. MCP 工具配置校验（仅查配置文件，不做实际握手避免 stdio 管道挂起）
if [ -n "$MCP_CONFIG" ]; then
    if grep -q 'core,network,debug,react' "$MCP_CONFIG" 2>/dev/null; then
        check pass "MCP 工具配置" "--tools core,network,debug,react（预期 64 工具）"
    elif grep -q '"--tools"' "$MCP_CONFIG" 2>/dev/null; then
        check warn "MCP 工具配置" "配置了 --tools 但非推荐组合（推荐 core,network,debug,react）"
    else
        check warn "MCP 工具配置" "未配置 --tools，将使用默认 core profile（仅基础工具）"
    fi
fi

# 汇总
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  汇总: ${PASS_COUNT} pass, ${WARN_COUNT} warn, ${FAIL_COUNT} fail, ${INFO_COUNT} info"
echo "═══════════════════════════════════════════════════════════"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo "❌ G0 门禁失败: 有 ${FAIL_COUNT} 项未通过，前端验证无法执行"
    echo "   修复后重跑: bash check-agent-browser.sh"
    exit 1
else
    echo ""
    echo "✅ G0 门禁通过: agent-browser 环境就绪，可执行前端验证 (F1-F5)"
    echo "   提示: 实际 MCP 工具数请查宿主工具日志的 toolCount 字段（预期 64，路径见 agent-browser-setup.md 附录）"
    exit 0
fi

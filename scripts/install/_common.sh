#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# scripts/install/_common.sh — LoopEngine 安装共享逻辑
# ════════════════════════════════════════════════════════════
# 平台无关的安装步骤（detect / clone / render / deploy / inject / check）
# 由 install.sh + scripts/install/{macos,windows,linux}.sh 通过 source 加载
# 3 平台脚本只保留 platform-specific 检测 + 单行 *_main 调用
# ════════════════════════════════════════════════════════════

# SENTINEL 防重入
if [ -n "${_COMMON_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_COMMON_LOADED=1

# ── 颜色（与 install.sh 同步）────────────────────────────
_BOLD="\033[1m"
_GREEN="\033[32m"
_YELLOW="\033[33m"
_CYAN="\033[36m"
_RED="\033[31m"
_RESET="\033[0m"

# ── 全局变量 ──────────────────────────────────────────────
COMMON_REPO="https://github.com/tsfdsong/loop_engineering"
COMMON_VERSION="1.3.2"
COMMON_WORK=""           # clone 出来的代码根
COMMON_SCRIPT_DIR=""     # 引用 scripts/*.py 的根（Step 1 后赋值）
COMMON_RENDERED_DIR=""   # 渲染后的 manifest 目录
COMMON_TARGETS=()        # 已部署路径数组（调度器汇总用）
COMMON_INSTALLED_VERSION_FILE="$HOME/.loopengine/.installed_version"

# ── AI Agent 标签映射 (v1.3.0) ────────────────────────────
# detect_installed_agents 输出内部 ID，install.sh 用此 map 把 ID
# 转成 tool_root_dirs_for_platform 的"label"做部署过滤
# 单一真源：tool root label ↔ 内部 agent id（v1.3.1 用关联数组，去除 filter 重复 case）
declare -A COMMON_LABEL_TO_ID
COMMON_LABEL_TO_ID["ZCode"]="zcode"
COMMON_LABEL_TO_ID["Claude Code"]="claude-code"
COMMON_LABEL_TO_ID["Codex"]="codex"
COMMON_LABEL_TO_ID["Gemini CLI"]="gemini-cli"
COMMON_LABEL_TO_ID["GitHub Copilot"]="github-copilot"
COMMON_LABEL_TO_ID["Pi"]="pi"
COMMON_LABEL_TO_ID["Cursor"]="cursor"
COMMON_LABEL_TO_ID["ZCode 内置包"]="zcode-bundled"
COMMON_LABEL_TO_ID["ZCode CLI 缓存"]="zcode-cli-cache"

# ── 全量 agent ID 列表（--all 时使用）────────────────────
COMMON_ALL_AGENT_IDS="zcode claude-code codex gemini-cli github-copilot pi cursor zcode-bundled zcode-cli-cache"

# ── MCP 可执行文件 fallback 路径表（v1.3.1 三平台合一）──
# 模板 {APPDATA} / {HOME} 在 common_detect_mcp_exe 里替换
# Windows 查 .exe/.cmd；其他平台查裸名
COMMON_MCP_FALLBACK_PATHS_WINDOWS=(
    "{APPDATA}/Python/Python39/Scripts"
    "{APPDATA}/Python/Python310/Scripts"
    "{APPDATA}/Python/Python311/Scripts"
    "{APPDATA}/Python/Python312/Scripts"
    "{APPDATA}/Python/Python313/Scripts"
    "{APPDATA}/Python/Python314/Scripts"
    "{APPDATA}/npm"
)
COMMON_MCP_FALLBACK_PATHS_MACOS=(
    "{HOME}/Library/Python/3.9/bin"
    "{HOME}/Library/Python/3.10/bin"
    "{HOME}/Library/Python/3.11/bin"
    "{HOME}/Library/Python/3.12/bin"
    "{HOME}/Library/Python/3.13/bin"
    "{HOME}/Library/Python/3.14/bin"
    # v1.3.2 补：Homebrew Python（Apple Silicon / Intel）+ npm global + volta/nvm
    "/opt/homebrew/bin"
    "/usr/local/bin"
    "/usr/local/lib/node_modules/.bin"
    "{HOME}/.npm-global/bin"
    "{HOME}/.volta/bin"
    "{HOME}/.bun/bin"
)
COMMON_MCP_FALLBACK_PATHS_LINUX=(
    "{HOME}/.local/bin"
    # v1.3.2 补：npm global + volta/nvm（repomix 走 npm）
    "/usr/local/bin"
    "/usr/lib/node_modules/.bin"
    "{HOME}/.npm-global/bin"
    "{HOME}/.volta/bin"
)

# ── smart_check_version ───────────────────────────────────
# 输出 + 等待（智能模式）
# 调用：common_smart_check_version <installed> <target>
common_smart_check_version() {
    local installed="$1" target="$2"
    local force="${COMMON_FORCE:-false}"
    local dry_run="${COMMON_DRY_RUN:-false}"
    local state
    state=$(common_describe_install_state "$installed" "$target")
    case "$state" in
        first_install)
            echo -e "  ${_GREEN}✅${_RESET}  首次安装 v${target}"
            ;;
        same_version)
            if [ "$force" = "true" ]; then
                echo -e "  ${_YELLOW}⚠${_RESET}  检测到 v${installed}（同版）— --force 强制重装"
            elif [ "$dry_run" = "true" ]; then
                echo -e "  ${_GREEN}✅${_RESET}  已装 v${installed}（同版）— dry-run 将跳过安装"
            else
                echo -e "  ${_YELLOW}⚠${_RESET}  检测到已安装 v${installed}（同版），5 秒后继续（强制重装请 --force）..."
                sleep 5
            fi
            ;;
        upgrade)
            echo -e "  ${_GREEN}✅${_RESET}  检测到 v${installed:-?}，升级到 v${target}"
            ;;
    esac
}

common_describe_install_state() {
    local installed="$1" target="$2"
    if [ -z "$installed" ]; then
        echo "first_install"
    elif [ "$installed" = "$target" ]; then
        echo "same_version"
    else
        echo "upgrade"
    fi
}

# ── detect_installed_agents (v1.3.0) ───────────────────────
# 自动检测本机已安装的 AI Agent
# 输出（stdout）：每行一个 agent 内部 ID（zcode / claude-code / codex / ...）
# 退出码：检测到的数量（即使为 0 也算成功）
# 特征路径参考：
#   - skill-hub agents.py:174-179 detect_installed_agents()
#   - 本机实测：~/.zcode / ~/.claude / ~/.cursor 都存在
common_detect_installed_agents() {
    local found=()
    local xdg="${XDG_CONFIG_HOME:-$HOME/.config}"

    # zcode: ~/.zcode/ 任意子目录存在即视为已装
    [ -d "$HOME/.zcode" ] && found+=("zcode")

    # claude-code: $CLAUDE_CONFIG_DIR 或 ~/.claude/
    if [ -n "${CLAUDE_CONFIG_DIR:-}" ] && [ -d "${CLAUDE_CONFIG_DIR}" ]; then
        found+=("claude-code")
    elif [ -d "$HOME/.claude" ]; then
        found+=("claude-code")
    fi

    # codex: $CODEX_HOME 或 ~/.codex/
    if [ -n "${CODEX_HOME:-}" ] && [ -d "${CODEX_HOME}" ]; then
        found+=("codex")
    elif [ -d "$HOME/.codex" ]; then
        found+=("codex")
    fi

    # gemini-cli: ~/.gemini/
    [ -d "$HOME/.gemini" ] && found+=("gemini-cli")

    # github-copilot: ~/.copilot/
    [ -d "$HOME/.copilot" ] && found+=("github-copilot")

    # pi: ~/.pi/
    [ -d "$HOME/.pi" ] && found+=("pi")

    # cursor: ~/.cursor/
    [ -d "$HOME/.cursor" ] && found+=("cursor")

    # 输出
    printf '%s\n' "${found[@]}"
    return ${#found[@]}
}

# ── filter_tool_root_dirs (v1.3.0) ────────────────────────
# 按 agent ID 列表过滤 tool_root_dirs 输出
# 入参：stdin 是 tool_root_dirs_for_platform 输出；$1 是 agent ID 列表（空格/换行/逗号分隔均可）
# 输出（stdout）：过滤后的 tool root 行
# v1.3.1 改用 COMMON_LABEL_TO_ID 关联数组（顶部单一真源），去除重复 case
# v1.3.2 修复：detect_installed_agents 用 printf '%s\n' 输出（换行分隔），
#   但匹配逻辑 [[ " $want_ids " == *" $id "* ]] 假设空格分隔 → 全部误拒。
#   入口处标准化为空格分隔（兼容换行/逗号/空格三种输入）。
common_filter_tool_root_dirs() {
    local want_ids="$1"
    # 标准化：换行/逗号/制表符 → 空格，并压紧多余空格
    want_ids=$(printf '%s' "$want_ids" | tr '\n,\t' '   ' | tr -s ' ')
    while IFS= read -r entry; do
        [[ -z "$entry" ]] && continue
        local label="${entry%%|*}"
        local label_id="${COMMON_LABEL_TO_ID[$label]:-}"
        # 未在表内 label 一律放行（如未来扩展）；否则只在 want_ids 里放行
        if [ -z "$label_id" ] || [[ " $want_ids " == *" $label_id "* ]]; then
            echo "$entry"
        fi
    done
}

# ── tool_root_dirs_for_platform (v1.3.0 重构) ─────────────
# 修复事实 bug (v1.2.4 行为)：macOS/Linux 上原来 9 路径会创建虚假的
# $HOME/AppData/Local/Programs/ZCode/ 目录（AppData 是 Windows 专属）。
# 改为按平台选两套独立数组：windows 9 路径（含 zcode-bundled AppData），
# macos|linux 8 路径（不含 zcode-bundled）。
# 注意：zcode-cli-cache 在所有平台都合法（$HOME/.zcode/cli/... 跨平台通用）。
#
# 调用：common_tool_root_dirs_for_platform <platform>
# v1.3.1：抽 8 行 BASE_TARGETS 共享数组，windows 追加 1 行 AppData
common_tool_root_dirs_for_platform() {
    local pf="${1:-}"
    # 跨平台共享 8 行基础目标（zcode-bundled 仅 Windows 追加）
    local base=(
        "ZCode|$HOME/.zcode/skills/loopengine"
        "Claude Code|$HOME/.claude/skills/loopengine"
        "Codex|$HOME/.codex/skills/loopengine"
        "Gemini CLI|$HOME/.gemini/extensions/loopengine"
        "GitHub Copilot|$HOME/.copilot/skills/loopengine"
        "Pi|$HOME/.pi/skills/loopengine"
        "Cursor|$HOME/.cursor/skills/loopengine"
    )
    case "$pf" in
        windows)
            printf '%s\n' "${base[@]}" \
                "ZCode 内置包|$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin" \
                "ZCode CLI 缓存|$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
            ;;
        macos|linux)
            printf '%s\n' "${base[@]}" \
                "ZCode CLI 缓存|$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
            ;;
        *)
            echo "  ❌ tool_root_dirs_for_platform: 未知平台 '$pf'" >&2
            return 1
            ;;
    esac
}

# ── detect_pip_cmd ────────────────────────────────────────
# 跨平台 pip 检测（macOS Homebrew Python 只有 pip3）
# 输出：pip3 / pip（任一存在）；空字符串（都不存在）
common_detect_pip_cmd() {
    if command -v pip3 >/dev/null 2>&1; then
        echo "pip3"
        return 0
    elif command -v pip >/dev/null 2>&1; then
        echo "pip"
        return 0
    fi
    return 1
}

# ── common_detect_mcp_exe (v1.3.1 三平台合一) ─────────────
# 按 $COMMON_PLATFORM 走平台表找 MCP 可执行文件
# 入参：<cmd_name> 输出：绝对路径 或 空
# 平台表 COMMON_MCP_FALLBACK_PATHS_<PF> 在 _common.sh 顶部定义
common_detect_mcp_exe() {
    local cmd_name="$1"
    local pf="${COMMON_PLATFORM:-}"

    # 1) PATH 内（带平台后缀 .exe/.cmd 仅 Windows）
    case "$pf" in
        windows)
            for c in "${cmd_name}.exe" "${cmd_name}.cmd" "$cmd_name"; do
                if command -v "$c" >/dev/null 2>&1; then
                    command -v "$c"
                    return 0
                fi
            done
            ;;
        *)
            if command -v "$cmd_name" >/dev/null 2>&1; then
                command -v "$cmd_name"
                return 0
            fi
            ;;
    esac

    # 2) 平台 fallback 目录（表驱动）
    local appdata=""
    [ "$pf" = "windows" ] && appdata="${APPDATA:-$HOME/AppData/Roaming}"
    local paths_var="COMMON_MCP_FALLBACK_PATHS_${pf^^}"
    eval "local paths=(\"\${${paths_var}[@]}\")" 2>/dev/null || local paths=()
    for p in "${paths[@]}"; do
        # 模板替换：{APPDATA} → $appdata, {HOME} → $HOME
        p="${p//\{APPDATA\}/$appdata}"
        p="${p//\{HOME\}/$HOME}"
        # Windows 优先查 .exe/.cmd，其他平台查裸名
        if [ "$pf" = "windows" ]; then
            for ext in ".exe" ".cmd" ""; do
                [ -f "${p}${ext}" ] && { echo "${p}${ext}"; return 0; }
            done
        else
            [ -f "$p" ] && { echo "$p"; return 0; }
        fi
    done
    return 1
}

# ── common_install_mcp_packages (v1.3.1 三平台合一) ───────
# 安装 MCP 三件套：jcodemunch-mcp / headroom / repomix
# 平台差异：Windows 用 py -m pip；macOS/Linux 用 pip3 + --break-system-packages fallback
common_install_mcp_packages() {
    local mcp_packages=(
        "jcodemunch-mcp|jcodemunch-mcp|true"
        "headroom|headroom|false"
        "repomix|repomix|true"
    )

    # 平台 pip 命令探测
    local pip_cmd=""
    case "${COMMON_PLATFORM:-}" in
        windows)
            if command -v py >/dev/null 2>&1; then
                pip_cmd="py -m pip"
            elif command -v pip3 >/dev/null 2>&1; then
                pip_cmd="pip3"
            elif command -v pip >/dev/null 2>&1; then
                pip_cmd="pip"
            fi
            ;;
        *)
            if ! pip_cmd=$(common_detect_pip_cmd); then
                echo -e "  ${_YELLOW}⚠${_RESET}  未找到 pip/pip3，跳过 MCP 包安装"
                return 0
            fi
            ;;
    esac

    for entry in "${mcp_packages[@]}"; do
        IFS='|' read -r pkg cmd is_mcp <<< "$entry"

        # 已装检查（Windows 多 .exe/.cmd 后缀）
        local installed=0
        if [ "${COMMON_PLATFORM:-}" = "windows" ]; then
            command -v "${cmd}.exe" >/dev/null 2>&1 && installed=1
            command -v "${cmd}.cmd" >/dev/null 2>&1 && installed=1
        else
            command -v "$cmd" >/dev/null 2>&1 && installed=1
        fi
        if [ "$installed" = "1" ]; then
            echo -e "  ${_GREEN}✅${_RESET} ${cmd} 已装"
            continue
        fi

        # repomix 走 npm
        if [[ "$pkg" == *"repomix"* ]]; then
            if command -v npm >/dev/null 2>&1; then
                if npm install -g "$pkg" 2>/dev/null; then
                    echo -e "  ${_GREEN}✅${_RESET} ${pkg} (npm)"
                fi
            else
                echo -e "  ${_YELLOW}⚠${_RESET}  npm 未装 — 手动: npm i -g $pkg"
            fi
            continue
        fi

        # 其余 pip
        if [ -z "$pip_cmd" ]; then
            echo -e "  ${_YELLOW}⚠${_RESET}  pip 未找到，跳过 ${pkg}"
            continue
        fi
        if $pip_cmd install --user "$pkg" >/dev/null 2>&1; then
            echo -e "  ${_GREEN}✅${_RESET} ${pkg} (${pip_cmd} --user)"
        elif $pip_cmd install --user --break-system-packages "$pkg" >/dev/null 2>&1; then
            echo -e "  ${_GREEN}✅${_RESET} ${pkg} (${pip_cmd} --user --break-system-packages)"
        else
            echo -e "  ${_YELLOW}⚠${_RESET}  ${pkg} 安装失败 — 手动: ${pip_cmd} install --user $pkg"
        fi

        if [ "$is_mcp" = "false" ]; then
            echo -e "  ${_CYAN}ℹ${_RESET}  ${cmd} 是 Python 库（非 MCP server），跳过桌面配置"
        fi
    done
}

# ── common_write_zcode_desktop_config (v1.3.1 三平台合一) ─
# 写入 ~/.zcode/cli/config.json (jcodemunch + repomix)
# Windows 多走 to_forward_slashes 转换（依赖平台脚本的该函数）
common_write_zcode_desktop_config() {
    local cfg="$HOME/.zcode/cli/config.json"
    local jcode_exe repo_exe
    jcode_exe=$(common_detect_mcp_exe jcodemunch-mcp) || jcode_exe=""
    repo_exe=$(common_detect_mcp_exe repomix) || repo_exe=""

    if [ -z "$jcode_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  jcodemunch/repomix 未全部找到，跳过桌面版配置写入"
        return 0
    fi

    # Windows 路径转 forward slash
    if [ "${COMMON_PLATFORM:-}" = "windows" ] && type to_forward_slashes >/dev/null 2>&1; then
        jcode_exe=$(to_forward_slashes "$jcode_exe")
        repo_exe=$(to_forward_slashes "$repo_exe")
    fi

    mkdir -p "$(dirname "$cfg")"
    if python "$COMMON_SCRIPT_DIR/scripts/merge_mcp_config.py" zcode "$cfg" "$jcode_exe" "$repo_exe"; then
        echo -e "  ${_GREEN}✅${_RESET} [ZCode 桌面版 MCP] $cfg"
        COMMON_TARGETS+=("ZCode 桌面版 MCP:$cfg")
    else
        echo -e "  ${_RED}❌${_RESET} 合并 $cfg 失败，详见上方 Python 错误"
        return 1
    fi
}

# ── common_platform_title (v1.3.1 抽出 · 去重) ─────────────
# platform id → 显示名 (windows/macos/linux → Windows/macOS/Linux)
# 调用：common_platform_title <pf> → 输出显示名（未知平台 → 空）
common_platform_title() {
    case "${1:-}" in
        windows) echo "Windows" ;;
        macos)   echo "macOS" ;;
        linux)   echo "Linux" ;;
    esac
}

# ── common_step5_5_cursor_mcp (v1.3.1 抽出) ───────────────
# v1.3.0 重复 3 平台 *_main 末尾，v1.3.1 抽到 _common.sh
# 仅当 detect 到 cursor 时调用
common_step5_5_cursor_mcp() {
    local pf_title
    pf_title=$(common_platform_title "${COMMON_PLATFORM:-}")

    if [[ " ${COMMON_AGENT_LIST:-} " == *" cursor "* ]]; then
        echo ""
        echo -e "${_BOLD}🎯 Step 5.5: 配置 Cursor MCP (${pf_title} · ~/.cursor/mcp.json)...${_RESET}"
        common_deploy_cursor_mcp
    else
        echo -e "  ${_CYAN}ℹ${_RESET}  跳过 Cursor MCP（detect 结果不含 cursor）"
    fi
}

# ── common_run_platform_steps (v1.3.1 主驱动) ──────────────
# 替代 3 平台 *_main 主体（Step 3-5.5）
# 3 平台 *_main 现在只是 1 行调用本函数
common_run_platform_steps() {
    local pf="${1:-${COMMON_PLATFORM:-}}"
    local pf_title
    pf_title=$(common_platform_title "$pf")
    if [ -z "$pf_title" ]; then
        echo -e "${_RED}❌ 未知平台：${pf}${_RESET}" >&2
        return 1
    fi

    echo ""
    echo -e "${_BOLD}🔌 Step 3: 安装 MCP 三件套（${pf_title}）...${_RESET}"
    common_install_mcp_packages

    echo ""
    echo -e "${_BOLD}⚙️  Step 4: 配置 ZCode 桌面版 MCP (${pf_title} · ~/.zcode/cli/config.json)...${_RESET}"
    common_write_zcode_desktop_config

    echo ""
    echo -e "${_BOLD}🌐 Step 5: 注入全局红线规则...${_RESET}"
    common_inject_red_lines

    common_step5_5_cursor_mcp
}

# ── clone_repo ────────────────────────────────────────────
# Step 1：拉取最新源码到 $COMMON_WORK
# 调用：common_clone_repo
common_clone_repo() {
    COMMON_WORK="${TMPDIR:-/tmp}/loopengine-install-$$"
    trap 'rm -rf "$COMMON_WORK"' EXIT
    echo ""
    echo -e "${_BOLD}📥 Step 1: 拉取最新源码...${_RESET}"
    if ! git clone --depth 1 --quiet "$COMMON_REPO" "$COMMON_WORK" 2>/dev/null; then
        echo -e "${_RED}❌ 无法 clone 仓库，请检查网络 / VPN${_RESET}"
        return 1
    fi
    COMMON_SCRIPT_DIR="$COMMON_WORK"

    # 本地优先覆盖 $COMMON_WORK/scripts/ + 关键 JSON overlay（仅当 install.sh 从本地文件运行）
    # v1.2.5 扩展：除 .py 外，还覆盖 .plugin-template.json 与 .*-plugin/plugin.json
    # 否则本地修改 plugin manifest 后，install.sh 仍从远端 clone 的旧版本渲染，修复不可见
    if [ -n "${COMMON_LOCAL_SRC_DIR:-}" ] && [ -d "$COMMON_LOCAL_SRC_DIR/scripts" ]; then
        # 修复: COMMON_LOCAL_SRC_DIR = 项目根（install.sh 与 _common.sh 同目录），不是 scripts/
        # 之前的 ../ 是 bug，去掉
        cp -f "$COMMON_LOCAL_SRC_DIR/scripts"/*.py "$COMMON_WORK/scripts/" 2>/dev/null
        # 覆盖 plugin manifest 关键 JSON
        if [ -f "$COMMON_LOCAL_SRC_DIR/.plugin-template.json" ]; then
            cp -f "$COMMON_LOCAL_SRC_DIR/.plugin-template.json" "$COMMON_WORK/.plugin-template.json"
        fi
        for overlay_dir in .zcode-plugin .claude-plugin .codex-plugin .cursor-plugin .copilot-plugin .pi-plugin; do
            if [ -f "$COMMON_LOCAL_SRC_DIR/$overlay_dir/plugin.json" ]; then
                cp -f "$COMMON_LOCAL_SRC_DIR/$overlay_dir/plugin.json" "$COMMON_WORK/$overlay_dir/plugin.json"
            fi
        done
        if [ -f "$COMMON_LOCAL_SRC_DIR/gemini-extension.json" ]; then
            cp -f "$COMMON_LOCAL_SRC_DIR/gemini-extension.json" "$COMMON_WORK/gemini-extension.json"
        fi
        echo -e "  ${_CYAN}ℹ${_RESET}  本地 scripts/ + plugin manifest 已覆盖 clone 副本（开发模式）"
    fi

    local skill_count
    skill_count=$(find "$COMMON_WORK/skills" -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${_GREEN}✅${_RESET} 已克隆到 $COMMON_WORK · ${skill_count} 个技能"
    return 0
}

# ── render_plugins ────────────────────────────────────────
# Step 2a：渲染 plugin manifest
# 调用：common_render_plugins
common_render_plugins() {
    echo -e "  ${_BOLD}Step 2a: 渲染 7 个 plugin manifest...${_RESET}"
    COMMON_RENDERED_DIR="$COMMON_WORK/.rendered-manifests"
    if python "$COMMON_SCRIPT_DIR/scripts/render_plugins.py" "$COMMON_WORK" "$COMMON_RENDERED_DIR"; then
        echo -e "  ${_GREEN}✅${_RESET}  manifest 渲染完成: $COMMON_RENDERED_DIR"
    else
        echo -e "  ${_RED}❌${_RESET}  manifest 渲染失败，终止安装"
        return 1
    fi
}

# ── deploy_to_9_tools (v1.3.1 拆 5 sub-function) ─────────
# Step 2b-2e：部署 skills / hooks / manifest / AGENTS.md / README.md 到目标工具
# v1.3.1 拆分为 5 sub-function 替代原 100 行单函数
common_deploy_to_9_tools() {
    local skills_dir="$COMMON_WORK/skills"
    local hooks_dir="$COMMON_WORK/hooks"
    local agents_md="$COMMON_WORK/AGENTS.md"
    local readme_md="$COMMON_WORK/README.md"

    local pf="${COMMON_PLATFORM:-}"
    if [ -z "$pf" ]; then
        echo -e "  ${_RED}❌${_RESET}  COMMON_PLATFORM 未设置（应在 install.sh 检测后注入）" >&2
        return 1
    fi

    local want_ids="${COMMON_AGENT_LIST:-$COMMON_ALL_AGENT_IDS}"
    local entries
    entries=$(common_tool_root_dirs_for_platform "$pf" | common_filter_tool_root_dirs "$want_ids")
    if [ -z "$entries" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  按平台 '$pf' + agent filter 后无目标可部署"
        return 0
    fi

    echo -e "  ${_BOLD}Step 2b-pre: 清理目标 plugin 顶层散落的旧平铺技能目录...${_RESET}"
    _for_each_target "$entries" common_cleanup_target_top_level

    echo -e "  ${_BOLD}Step 2b: 复制 skills/ 到目标 skills/ 子目录...${_RESET}"
    _for_each_target "$entries" common_copy_skills_for "$skills_dir"

    echo -e "  ${_BOLD}Step 2c: 复制 hooks/ 到目标...${_RESET}"
    _for_each_target "$entries" common_copy_hooks_for "$hooks_dir"

    echo -e "  ${_BOLD}Step 2d: 部署 plugin manifest...${_RESET}"
    _for_each_target "$entries" common_deploy_manifest_for

    echo -e "  ${_BOLD}Step 2e: 复制项目根文档 (AGENTS.md / README.md)...${_RESET}"
    _for_each_target "$entries" common_copy_root_docs_for "$agents_md" "$readme_md"
}

# 通用 iterator：每个 (label, root_dir) 调一次 $action
# action 签名：action <label> <root_dir> [extra args]
_for_each_target() {
    local entries="$1"; shift
    local action="$1"; shift
    while IFS= read -r entry; do
        [[ -z "$entry" ]] && continue
        IFS='|' read -r label root_dir <<< "$entry"
        "$action" "$label" "$root_dir" "$@"
    done <<< "$entries"
}

# ── deploy sub-functions (v1.3.1 拆分) ────────────────────
# 每个 sub-function 处理 1 个 Step，单一职责

# Step 2b-pre: 清理 plugin 顶层非元目录（v1.2.5 修复后旧目录残留）
common_cleanup_target_top_level() {
    local label="$1" root_dir="$2"
    [ -d "$root_dir" ] || return 0
    # 保留元目录/元文件：hooks/ skills/ .*-plugin/ AGENTS.md README.md package.json marketplace.json gemini-extension.json
    find "$root_dir" -mindepth 1 -maxdepth 1 \
        ! -name 'hooks' \
        ! -name 'skills' \
        ! -name '.zcode-plugin' \
        ! -name '.claude-plugin' \
        ! -name '.codex-plugin' \
        ! -name '.cursor-plugin' \
        ! -name '.copilot-plugin' \
        ! -name '.pi-plugin' \
        ! -name 'AGENTS.md' \
        ! -name 'README.md' \
        ! -name 'package.json' \
        ! -name 'marketplace.json' \
        ! -name 'gemini-extension.json' \
        -exec rm -rf {} + 2>/dev/null
    echo -e "  ${_GREEN}✅${_RESET}  [$label] 顶层清理完成: $root_dir"
}

# Step 2b: 复制 skills/ 到目标 skills/ 子目录
# v1.3.2 修复 Cursor 路径：Cursor 扁平扫描 ~/.cursor/skills/<skill>/SKILL.md，
# 而 ZCode 等支持 plugin 中间层 ~/.zcode/skills/loopengine/skills/<skill>/。
# 对 Cursor label，skills 平铺到 root_dir 父目录（~/.cursor/skills/），
# 而非 root_dir/skills（~/.cursor/skills/loopengine/skills/，多两层扫不到）。
# 安全约束：Cursor 平铺到公共目录，绝不能用 find -delete 清空（会删用户其他 skill），
# 改为逐个 skill 子目录 rsync 风格覆盖（只动 LoopEngine 拥有的目录）。
common_copy_skills_for() {
    local label="$1" root_dir="$2" skills_dir="$3"
    local skill_dst="$root_dir/skills"

    # Cursor: 扁平平铺到 ~/.cursor/skills/，逐 skill 覆盖（不清空公共目录）
    if [ "$label" = "Cursor" ]; then
        skill_dst="$(dirname "$root_dir")"
        if [ ! -d "$skills_dir" ]; then
            echo -e "  ${_YELLOW}⚠${_RESET}  [$label skills] 源不存在: $skills_dir（跳过）"
            return 0
        fi
        mkdir -p "$skill_dst"
        local count=0
        local sub
        for sub in "$skills_dir"/*/; do
            [ -d "$sub" ] || continue
            local name
            name=$(basename "$sub")
            # 只清这个 skill 子目录（LoopEngine 拥有的），不动其他
            rm -rf "${skill_dst:?}/$name" 2>/dev/null
            if cp -r "$sub" "${skill_dst}/$name" 2>/dev/null; then
                count=$((count + 1))
            else
                echo -e "  ${_YELLOW}⚠${_RESET}  [$label skills] 复制失败: $name"
            fi
        done
        COMMON_TARGETS+=("$label skills:${skill_dst}")
        echo -e "  ${_GREEN}✅${_RESET} [$label skills] ${count} 个 → $skill_dst（扁平）"
        return 0
    fi

    # 其他 harness：标准 plugin 中间层路径
    common_copy_tree "$label skills" "$skills_dir" "$skill_dst"
}

# Step 2c: 复制 hooks/ 到目标
common_copy_hooks_for() {
    local label="$1" root_dir="$2" hooks_dir="$3"
    common_copy_tree "$label hooks" "$hooks_dir" "$root_dir/hooks"
}

# Step 2d: 部署 plugin manifest (按 label 分发)
common_deploy_manifest_for() {
    local label="$1" root_dir="$2"
    case "$label" in
        "ZCode"|"ZCode 内置包"|"ZCode CLI 缓存")
            common_copy_file "$label plugin.json" "$COMMON_RENDERED_DIR/zcode-plugin/plugin.json" "$root_dir/.zcode-plugin/plugin.json"
            ;;
        "Claude Code")
            common_copy_file "$label plugin.json" "$COMMON_RENDERED_DIR/claude-plugin/plugin.json" "$root_dir/.claude-plugin/plugin.json"
            common_copy_file "$label marketplace.json" "$COMMON_RENDERED_DIR/claude-plugin/marketplace.json" "$root_dir/.claude-plugin/marketplace.json"
            ;;
        "Codex")
            common_copy_file "$label plugin.json" "$COMMON_RENDERED_DIR/codex-plugin/plugin.json" "$root_dir/.codex-plugin/plugin.json"
            ;;
        "Cursor")
            common_copy_file "$label plugin.json" "$COMMON_RENDERED_DIR/cursor-plugin/plugin.json" "$root_dir/.cursor-plugin/plugin.json"
            ;;
        "Gemini CLI")
            common_copy_file "$label gemini-extension.json" "$COMMON_RENDERED_DIR/gemini-extension.json" "$root_dir/gemini-extension.json"
            ;;
        "GitHub Copilot"|"Pi")
            : # 不通过 manifest 部署
            ;;
    esac
}

# Step 2e: 复制项目根文档 (AGENTS.md / README.md)
common_copy_root_docs_for() {
    local label="$1" root_dir="$2" agents_md="$3" readme_md="$4"
    common_copy_file "$label AGENTS.md" "$agents_md" "$root_dir/AGENTS.md"
    common_copy_file "$label README.md" "$readme_md" "$root_dir/README.md"
}

# ── copy_tree / copy_file ─────────────────────────────────
common_copy_tree() {
    local label="$1" src="$2" dst="$3"
    if [ ! -d "$src" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  [$label] 源不存在: $src（跳过）"
        return 0
    fi
    mkdir -p "$dst"
    if ! find "$dst" -mindepth 1 -delete 2>/dev/null; then
        echo -e "  ${_YELLOW}⚠${_RESET}  [$label] 清理旧文件失败: $dst（继续复制）"
    fi
    if cp -r "$src/." "$dst/" 2>/dev/null; then
        COMMON_TARGETS+=("$label:$dst")
        echo -e "  ${_GREEN}✅${_RESET} [$label] $dst"
    else
        echo -e "  ${_YELLOW}⚠${_RESET}  [$label] 复制失败: $dst"
    fi
}

common_copy_file() {
    local label="$1" src="$2" dst="$3"
    if [ ! -f "$src" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  [$label] 源不存在: $src（跳过）"
        return 0
    fi
    mkdir -p "$(dirname "$dst")"
    if cp "$src" "$dst" 2>/dev/null; then
        COMMON_TARGETS+=("$label:$dst")
        echo -e "  ${_GREEN}✅${_RESET} [$label] $dst"
    else
        echo -e "  ${_YELLOW}⚠${_RESET}  [$label] 复制失败: $dst"
    fi
}

# ── deploy_cursor_mcp (v1.3.0 新增) ────────────────────────
# Step 5.5：写入 Cursor 全局 MCP 配置 ~/.cursor/mcp.json
# 要求：
#   1) agent filter 列表中包含 cursor（仅当 detect 到 Cursor 才调用）
#   2) jcodemunch-mcp + repomix 可执行文件已通过 detect_mcp_exe 找到（必需）
#      headroom 可选——找不到时只跳过 headroom entry，仍写 jcodemunch + repomix
#      （v1.3.2 修复：原逻辑强制 3 个全找到才写，导致 macOS headroom 装在
#       Homebrew 路径不在 fallback 表时整个 Cursor MCP 配置被跳过）
# schema: Cursor 用 mcpServers (无 type 字段)，与 ZCode mcp.servers+type:"stdio" 不同
# 复用平台子脚本的 detect_mcp_exe_<platform> 函数 + windows.sh 的 to_forward_slashes
common_deploy_cursor_mcp() {
    local jcode_exe repo_exe hdrm_exe
    jcode_exe=$(common_detect_mcp_exe jcodemunch-mcp) || jcode_exe=""
    repo_exe=$(common_detect_mcp_exe repomix) || repo_exe=""
    hdrm_exe=$(common_detect_mcp_exe headroom) || hdrm_exe=""

    # 必需：jcodemunch + repomix
    if [ -z "$jcode_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  jcodemunch/repomix 未找到，跳过 ~/.cursor/mcp.json 写入"
        echo -e "  ${_CYAN}ℹ${_RESET}  手动: 安装 jcodemunch-mcp + repomix 后重跑 bash install.sh --force"
        return 0
    fi

    # 可选：headroom 找不到仅告警，不阻断
    if [ -z "$hdrm_exe" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  headroom 未找到（可选）— Cursor mcp.json 将不写 headroom entry"
        hdrm_exe=""
    fi

    # Windows 路径转 forward slash（依赖平台脚本的 to_forward_slashes 函数）
    if [ "${COMMON_PLATFORM:-}" = "windows" ] && type to_forward_slashes >/dev/null 2>&1; then
        jcode_exe=$(to_forward_slashes "$jcode_exe")
        repo_exe=$(to_forward_slashes "$repo_exe")
        hdrm_exe=$(to_forward_slashes "$hdrm_exe")
    fi

    local cfg="$HOME/.cursor/mcp.json"
    mkdir -p "$(dirname "$cfg")"
    if python "$COMMON_SCRIPT_DIR/scripts/merge_mcp_config.py" cursor "$cfg" "$jcode_exe" "$repo_exe" "$hdrm_exe"; then
        echo -e "  ${_GREEN}✅${_RESET} [Cursor MCP] $cfg"
        COMMON_TARGETS+=("Cursor MCP:$cfg")
    else
        echo -e "  ${_RED}❌${_RESET} 合并 $cfg 失败，详见上方 Python 错误"
        return 1
    fi
}

# ── inject_red_lines ──────────────────────────────────────
# Step 5：注入 8 条红线到 7 工具用户级 AGENTS.md
# 调用：common_inject_red_lines
common_inject_red_lines() {
    local src="$COMMON_WORK/AGENTS.md"
    [ ! -f "$src" ] && { echo -e "  ${_YELLOW}⚠${_RESET}  $src 不存在，跳过"; return 0; }

    # 8 条红线（与 AGENTS.md v1.0.3+ 同步）
    local managed_rules=(
        "用户交互红线:INTERACTION-RULES"
        "MCP 红线规则:MCP-RULES"
        "事实优先硬规则:EVIDENCE-RULES"
        "摘要输出红线:SUMMARY-RULES"
        "完成前验证红线:VERIFICATION-RULES"
        "进度汇报红线:PROGRESS-RULES"
        "Subagent 边界红线:SUBAGENT-RULES"
        "一致性核对红线:CONSISTENCY-RULES"
    )

    # 7 工具用户级红线文件
    local managed_targets=(
        "ZCode|$HOME/.zcode/AGENTS.md"
        "Claude Code|$HOME/.claude/CLAUDE.md"
        "Gemini CLI|$HOME/.gemini/GEMINI.md"
        "Codex|$HOME/.codex/AGENTS.md"
        "Cursor|$HOME/.cursor/rules/loopengine-interaction.mdc"
        "GitHub Copilot|$HOME/.copilot/AGENTS.md"
        "Pi|$HOME/.pi/AGENTS.md"
    )

    local block_dir
    block_dir=$(mktemp -d)

    local extracted_count=0
    for entry in "${managed_rules[@]}"; do
        local title="${entry%%:*}"
        local marker="${entry##*:}"
        if common_extract_rule_block "$src" "$title" "$marker" "$block_dir"; then
            extracted_count=$((extracted_count + 1))
        fi
    done

    if [ "$extracted_count" -eq 0 ]; then
        echo -e "  ${_RED}❌${_RESET}  未提取到任何规则章节，退出"
        rm -rf "$block_dir"
        return 1
    fi

    for entry in "${managed_targets[@]}"; do
        local label="${entry%%|*}"
        local target="${entry##*|}"
        common_inject_rules_to_target "$label" "$target" "$block_dir" || true
    done

    rm -rf "$block_dir"
    return 0
}

common_extract_rule_block() {
    local src="$1" title="$2" marker="$3" block_dir="$4"
    local begin_line
    begin_line=$(awk -v t="^## .*🔴.*$title" '$0 ~ t { print NR; exit }' "$src")
    if [ -z "$begin_line" ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  AGENTS.md 中未找到 '$title' 章节，跳过"
        return 1
    fi
    local next_section_line
    next_section_line=$(awk -v start="$begin_line" '
        BEGIN { in_code = 0 }
        NR > start {
            if (/^[ \t]*```[a-zA-Z0-9]*[ \t]*(<[^>]*>)?[ \t]*$/) { in_code = !in_code; next }
            if (!in_code && /^## /) { print NR; exit }
        }
    ' "$src")
    local end_line
    if [ -n "$next_section_line" ]; then
        end_line=$((next_section_line - 1))
    else
        end_line=$(wc -l < "$src")
    fi
    local managed_block
    managed_block=$(awk -v start="$begin_line" -v end="$end_line" 'NR>=start && NR<=end' "$src")
    local wrapped_block
    wrapped_block=$(printf '<!-- BEGIN LOOPENGINE-MANAGED %s -->\n%s\n<!-- END LOOPENGINE-MANAGED %s -->' \
        "$marker" "$managed_block" "$marker")
    echo "$wrapped_block" > "$block_dir/$marker"
    echo -e "  ${_GREEN}✅${_RESET} 提取: ${_CYAN}${title}${_RESET} → ${marker}"
    return 0
}

common_inject_rules_to_target() {
    local label="$1" target="$2" block_dir="$3"
    mkdir -p "$(dirname "$target")"
    if python "$COMMON_SCRIPT_DIR/scripts/inject_rules.py" "$target" "$block_dir"; then
        echo -e "  ${_GREEN}✅${_RESET} [$label 红线] $target"
        COMMON_TARGETS+=("$label 红线:$target")
        return 0
    fi
    echo -e "  ${_RED}❌${_RESET} [$label 红线] 注入失败: $target"
    return 1
}

# ── write_version_file ────────────────────────────────────
common_write_version_file() {
    mkdir -p "$HOME/.loopengine"
    echo "$COMMON_VERSION" > "$COMMON_INSTALLED_VERSION_FILE"
    echo -e "  ${_GREEN}✅${_RESET} 写入版本号文件: $COMMON_INSTALLED_VERSION_FILE"
}

# ── deployment_check ──────────────────────────────────────
# Step 6：部署自检
# 调用：common_deployment_check
common_deployment_check() {
    local check_pass=0
    local check_fail=0

    echo ""
    echo -e "${_BOLD}🔬 Step 6: 部署自检...${_RESET}"

    # 检查目标 skills 目录（按平台分支 + agent 过滤；v1.3.0 自适应）
    local skill_ok=0
    local skill_total=0
    local pf="${COMMON_PLATFORM:-}"
    local want_ids="${COMMON_AGENT_LIST:-$COMMON_ALL_AGENT_IDS}"
    if [ -n "$pf" ]; then
        while IFS= read -r entry; do
            [[ -z "$entry" ]] && continue
            IFS='|' read -r label root_dir <<< "$entry"
            skill_total=$((skill_total + 1))
            if [ -d "$root_dir/skills/orch" ] || [ -d "$root_dir/skills/loop" ]; then
                skill_ok=$((skill_ok + 1))
            fi
        done < <(common_tool_root_dirs_for_platform "$pf" | common_filter_tool_root_dirs "$want_ids")
    fi
    # v1.3.0 阈值：技能数 ≥ 实际总目标的 80%（保留对 agent filter 的容错）
    local threshold=$(( skill_total * 80 / 100 ))
    [ "$threshold" -lt 1 ] && threshold=1
    if [ "$skill_ok" -ge "$threshold" ]; then
        echo -e "  ${_GREEN}✅${_RESET} 至少 $threshold 个目标的 skills 目录已部署（实际 $skill_ok/$skill_total）"
        check_pass=$((check_pass + 1))
    else
        echo -e "  ${_RED}❌${_RESET} skills 目录部署不足：$skill_ok/$skill_total (< $threshold)"
        check_fail=$((check_fail + 1))
    fi

    # manifest 渲染数 ≥ 7
    local rendered_count
    rendered_count=$(find "$COMMON_RENDERED_DIR" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$rendered_count" -ge 7 ]; then
        echo -e "  ${_GREEN}✅${_RESET} 渲染 manifest 数: $rendered_count (>=7)"
        check_pass=$((check_pass + 1))
    else
        echo -e "  ${_RED}❌${_RESET} 渲染 manifest 数: $rendered_count (<7)"
        check_fail=$((check_fail + 1))
    fi

    common_write_version_file
    check_pass=$((check_pass + 1))

    if [ "$check_fail" -gt 0 ]; then
        echo -e "  ${_YELLOW}⚠${_RESET}  自检: ${check_pass} 通过 / ${check_fail} 失败"
    else
        echo -e "  ${_GREEN}✅${_RESET} 自检: ${check_pass} 项全部通过"
    fi
    return 0
}

# ── dry_run_summary ───────────────────────────────────────
# dry-run 模式早退出（拉完源码后）
# 调用：common_dry_run_summary <installed_version>
common_dry_run_summary() {
    local installed="$1"
    echo ""
    echo -e "${_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${_RESET}"
    echo -e "${_BOLD}${_CYAN}🔍 --dry-run 模式总结（不执行部署）${_RESET}"
    echo -e "${_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${_RESET}"
    local state
    state=$(common_describe_install_state "$installed" "$COMMON_VERSION")
    case "$state" in
        first_install)
            echo -e "  ${_CYAN}•${_RESET} 状态: 未安装"
            echo -e "  ${_CYAN}•${_RESET} 计划: 首次安装 v${COMMON_VERSION}"
            ;;
        same_version)
            echo -e "  ${_CYAN}•${_RESET} 状态: 已装 v${installed}（同版）"
            echo -e "  ${_CYAN}•${_RESET} 计划: 无需更新（如需强制重装请 --force）"
            ;;
        upgrade)
            echo -e "  ${_CYAN}•${_RESET} 状态: 已装 v${installed:-?}"
            echo -e "  ${_CYAN}•${_RESET} 计划: 升级到 v${COMMON_VERSION}（如需执行请去掉 --dry-run）"
            ;;
    esac
    echo -e "  ${_CYAN}•${_RESET} 远端版本: v${COMMON_VERSION}"
    local skill_count
    skill_count=$(find "$COMMON_WORK/skills" -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${_CYAN}•${_RESET} 技能数: ${skill_count}"
    echo -e "  ${_CYAN}•${_RESET} 工作目录: $COMMON_WORK"
    echo ""
}

# ── print_target_summary ──────────────────────────────────
# 任务结束输出部署路径汇总
# 调用：common_print_target_summary <platform>
common_print_target_summary() {
    local platform="$1"
    echo ""
    echo -e "${_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${_RESET}"
    echo -e "${_BOLD}${_GREEN}✅ LoopEngine v${COMMON_VERSION} 安装完成${_RESET} · 平台: ${platform} · 部署到 ${#COMMON_TARGETS[@]} 个路径"
    echo -e "${_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${_RESET}"
    for t in "${COMMON_TARGETS[@]}"; do
        echo -e "  ${_CYAN}•${_RESET} $t"
    done
    echo ""
    echo -e "${_BOLD}💡 验证 (开新 AI 会话后发送):${_RESET}"
    echo -e "  ${_CYAN}\"告诉我 LoopEngine 的核心价值，并说明 orch v2 的场景家族（family）有哪些\"${_RESET}"
    echo ""
}
#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# scripts/install/_common.sh — LoopEngine 安装共享逻辑
# ════════════════════════════════════════════════════════════
# 平台无关的安装步骤（git clone / 9 工具部署 / 7 红线 / 自检）
# 由 install.sh + scripts/install/{macos,windows,linux}.sh 通过 source 加载
#
# v1.2.4 新增（2026-07-01 跨平台架构）：
#   • 从 v1.2.3 install.sh 提取平台无关逻辑
#   • 暴露函数：clone_repo / deploy_to_9_tools / inject_red_lines /
#     deployment_check / smart_check_version / write_version_file
#   • SENTINEL 防重入
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
COMMON_VERSION="1.2.4"
COMMON_WORK=""           # clone 出来的代码根
COMMON_SCRIPT_DIR=""     # 引用 scripts/*.py 的根（Step 1 后赋值）
COMMON_RENDERED_DIR=""   # 渲染后的 manifest 目录
COMMON_TARGETS=()        # 已部署路径数组（调度器汇总用）
COMMON_INSTALLED_VERSION_FILE="$HOME/.loopengine/.installed_version"

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

    # 本地优先覆盖 $COMMON_WORK/scripts/（仅当 install.sh 从本地文件运行）
    if [ -n "${COMMON_LOCAL_SRC_DIR:-}" ] && [ -d "$COMMON_LOCAL_SRC_DIR/scripts" ]; then
        cp -f "$COMMON_LOCAL_SRC_DIR/scripts"/*.py "$COMMON_WORK/scripts/" 2>/dev/null && \
            echo -e "  ${_CYAN}ℹ${_RESET}  本地 scripts/ 已覆盖 clone 副本（开发模式）" || true
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

# ── deploy_to_9_tools ─────────────────────────────────────
# Step 2b-2e：部署 skills / hooks / manifest / AGENTS.md / README.md 到 9 工具
# 调用：common_deploy_to_9_tools
common_deploy_to_9_tools() {
    local skills_dir="$COMMON_WORK/skills"
    local hooks_dir="$COMMON_WORK/hooks"
    local agents_md="$COMMON_WORK/AGENTS.md"
    local readme_md="$COMMON_WORK/README.md"

    # 9 工具的"约定根目录"（v1.2.3 9 项，含 Windows 内置包）
    local tool_root_dirs=(
        "ZCode|$HOME/.zcode/skills/loopengine"
        "Claude Code|$HOME/.claude/skills/loopengine"
        "Codex|$HOME/.codex/skills/loopengine"
        "Gemini CLI|$HOME/.gemini/extensions/loopengine"
        "GitHub Copilot|$HOME/.copilot/skills/loopengine"
        "Pi|$HOME/.pi/skills/loopengine"
        "Cursor|$HOME/.cursor/skills/loopengine"
        "ZCode 内置包|$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin"
        "ZCode CLI 缓存|$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
    )

    echo -e "  ${_BOLD}Step 2b: 复制 skills/ 到 9 个目标...${_RESET}"
    for entry in "${tool_root_dirs[@]}"; do
        IFS='|' read -r label root_dir <<< "$entry"
        common_copy_tree "$label skills" "$skills_dir" "$root_dir"
    done

    echo -e "  ${_BOLD}Step 2c: 复制 hooks/ 到 9 个目标...${_RESET}"
    for entry in "${tool_root_dirs[@]}"; do
        IFS='|' read -r label root_dir <<< "$entry"
        common_copy_tree "$label hooks" "$hooks_dir" "$root_dir/hooks"
    done

    echo -e "  ${_BOLD}Step 2d: 部署 7 个 plugin manifest...${_RESET}"
    for entry in "${tool_root_dirs[@]}"; do
        IFS='|' read -r label root_dir <<< "$entry"
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
    done

    echo -e "  ${_BOLD}Step 2e: 复制项目根文档 (AGENTS.md / README.md)...${_RESET}"
    for entry in "${tool_root_dirs[@]}"; do
        IFS='|' read -r label root_dir <<< "$entry"
        common_copy_file "$label AGENTS.md" "$agents_md" "$root_dir/AGENTS.md"
        common_copy_file "$label README.md" "$readme_md" "$root_dir/README.md"
    done
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

# ── inject_red_lines ──────────────────────────────────────
# Step 5：注入 7 条红线到 7 工具用户级 AGENTS.md
# 调用：common_inject_red_lines
common_inject_red_lines() {
    local src="$COMMON_WORK/AGENTS.md"
    [ ! -f "$src" ] && { echo -e "  ${_YELLOW}⚠${_RESET}  $src 不存在，跳过"; return 0; }

    # 7 条红线（与 AGENTS.md v1.0.2+ 同步）
    local managed_rules=(
        "用户交互红线:INTERACTION-RULES"
        "MCP 红线规则:MCP-RULES"
        "事实优先硬规则:EVIDENCE-RULES"
        "摘要输出红线:SUMMARY-RULES"
        "完成前验证红线:VERIFICATION-RULES"
        "进度汇报红线:PROGRESS-RULES"
        "Subagent 边界红线:SUBAGENT-RULES"
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
            if (/^[ \t]*```[ \t]*(<[^>]*>)?[ \t]*$/) { in_code = !in_code; next }
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

    # 检查 9 工具 skills 目录至少 8 个部署成功
    local skill_ok=0
    local tool_root_dirs=(
        "$HOME/.zcode/skills/loopengine"
        "$HOME/.claude/skills/loopengine"
        "$HOME/.codex/skills/loopengine"
        "$HOME/.gemini/extensions/loopengine"
        "$HOME/.copilot/skills/loopengine"
        "$HOME/.pi/skills/loopengine"
        "$HOME/.cursor/skills/loopengine"
        "$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin"
        "$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
    )
    for d in "${tool_root_dirs[@]}"; do
        if [ -d "$d/orch" ] || [ -d "$d/loop" ]; then
            skill_ok=$((skill_ok + 1))
        fi
    done
    if [ "$skill_ok" -ge 8 ]; then
        echo -e "  ${_GREEN}✅${_RESET} 至少 8 个工具的 skills 目录已部署（实际 $skill_ok/9）"
        check_pass=$((check_pass + 1))
    else
        echo -e "  ${_RED}❌${_RESET} skills 目录部署不足：$skill_ok/9 (< 8)"
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
    echo -e "  ${_CYAN}\"告诉我 LoopEngine 的核心价值，并列出 orch 调度的 5 类复合任务\"${_RESET}"
    echo ""
}
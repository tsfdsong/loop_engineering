#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# LoopEngine 一键安装 v1.1.0 — 极简 curl 一条龙
# ════════════════════════════════════════════════════════════
# 一行安装:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
#
# 设计哲学:
#   • 不依赖 ZCode 内部插件市场 / marketplace.json / plugin.json 注册
#   • 一次拉源码 → 渲染 plugin manifest → 部署 7 工具 + MCP 三件套 + 5 红线
#   • 装完就能用，不依赖 AI 工具的"重启"行为
#   • 幂等：重复执行不破坏（sentinel markers + 模板渲染）
#
# v1.1.0 修复（2026-07-01 完整批处理）：
#   • Step 0  新增版本自检（防止装到一半发现已装过）
#   • Step 2  同步范围扩大：skills/ + hooks/ + AGENTS.md + README.md + .mcp.json + 6 个 plugin manifest
#   • Step 2a 新增：render_plugins.py 渲染 6 个 manifest（去 _comment，version 同步）
#   • Step 3  优化：3 个 MCP 包用数组循环替代重复 if
#   • Step 4  保持：仅写 ZCode 桌面版 MCP（其他 6 工具通过 .mcp.json 模板间接支持）
#   • Step 5  保持：5 条红线 sentinel markers 注入 7 工具
#   • Step 6  新增：部署自检（7 工具关键路径存在性 + manifest version 一致性）
#   • update.sh 文档化：调用本脚本（不再用 zcode-mcp-ensure.sh）
#   • 删除 scripts/zcode-mcp-ensure.sh（与 install.sh Step 4 重复 70 行）
# ════════════════════════════════════════════════════════════

set -euo pipefail

VERSION="1.1.0"
REPO="https://github.com/tsfdsong/loop_engineering"
BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"; RED="\033[31m"; RESET="\033[0m"
TARGETS=()

# SCRIPT_DIR = 安装脚本所在目录（指向 $WORK 的副本根；用于引用 scripts/*.py）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║  LoopEngine v${VERSION} — 一键安装 (curl 一条龙)    ║${RESET}"
echo -e "${BOLD}${CYAN}║  把技能/AGENTS.md/hooks/MCP/5 红线全量同步      ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Step 0: 版本自检（v1.1.0 新增）──────────────────────
echo -e "${BOLD}🔍 Step 0: 版本自检...${RESET}"
INSTALLED_VERSION_FILE="$HOME/.loopengine/.installed_version"
if [ -f "$INSTALLED_VERSION_FILE" ]; then
    INSTALLED_VERSION=$(cat "$INSTALLED_VERSION_FILE" 2>/dev/null || echo "")
    if [ "$INSTALLED_VERSION" = "$VERSION" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  检测到已安装 v${INSTALLED_VERSION}，5 秒后继续（强制重装请 Ctrl+C 后 --force）..."
        sleep 5
    else
        echo -e "  ${GREEN}✅${RESET}  检测到 v${INSTALLED_VERSION:-?}, 升级到 v${VERSION}"
    fi
else
    echo -e "  ${GREEN}✅${RESET}  首次安装 v${VERSION}"
fi

# ── Step 1: 拉最新源码 ────────────────────────────────────
WORK="${TMPDIR:-/tmp}/loopengine-install-$$"
trap 'rm -rf "$WORK"' EXIT
echo ""
echo -e "${BOLD}📥 Step 1: 拉取最新源码...${RESET}"
if ! git clone --depth 1 --quiet "$REPO" "$WORK" 2>/dev/null; then
    echo -e "${RED}❌ 无法 clone 仓库，请检查网络 / VPN${RESET}"
    exit 1
fi
SKILLS_DIR="$WORK/skills"
SKILL_COUNT=$(find "$SKILLS_DIR" -name SKILL.md 2>/dev/null | wc -l)
echo -e "  ${GREEN}✅${RESET} 已克隆到 $WORK · ${SKILL_COUNT} 个技能"

# ── Step 2: 部署（5 个子步骤 · v1.1.0 扩展）─────────────
# 7 个目标工具的"约定技能目录" + 同步内容映射
# 格式：tool|skills_dir|docs_dir|plugin_dir
TOOL_TARGETS=(
    "ZCode|.zcode/skills/loopengine|.zcode/skills/loopengine|.zcode/skills/loopengine"
    "Claude Code|.claude/skills/loopengine|.claude/skills/loopengine|.claude/skills/loopengine"
    "Codex|.codex/skills/loopengine|.codex/skills/loopengine|.codex/skills/loopengine"
    "Gemini CLI|.gemini/extensions/loopengine/skills|.gemini/extensions/loopengine|.gemini/extensions/loopengine"
    "GitHub Copilot|.copilot/skills/loopengine|.copilot/skills/loopengine|.copilot/skills/loopengine"
    "Pi|.pi/skills/loopengine|.pi/skills/loopengine|.pi/skills/loopengine"
    "ZCode 内置包|AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin/skills|AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin|AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin"
    "ZCode CLI 缓存|.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/skills|.zcode/cli/plugins/cache/zcode-plugins-official/loopengine|.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
)

# 通用复制函数：源 → 目标（保留目录，先清空再 cp）
copy_tree() {
    local label="$1" src="$2" dst="$3"
    if [ ! -d "$src" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  [$label] 源不存在: $src（跳过）"
        return 0
    fi
    mkdir -p "$dst"
    if ! find "$dst" -mindepth 1 -delete 2>/dev/null; then
        echo -e "  ${YELLOW}⚠${RESET}  [$label] 清理旧文件失败: $dst（继续复制）"
    fi
    if cp -r "$src/." "$dst/" 2>/dev/null; then
        TARGETS+=("$label:$dst")
        echo -e "  ${GREEN}✅${RESET} [$label] $dst"
    else
        echo -e "  ${YELLOW}⚠${RESET}  [$label] 复制失败: $dst"
    fi
}

# 复制单个文件（创建父目录）
copy_file() {
    local label="$1" src="$2" dst="$3"
    if [ ! -f "$src" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  [$label] 源不存在: $src（跳过）"
        return 0
    fi
    mkdir -p "$(dirname "$dst")"
    if cp "$src" "$dst" 2>/dev/null; then
        TARGETS+=("$label:$dst")
        echo -e "  ${GREEN}✅${RESET} [$label] $dst"
    else
        echo -e "  ${YELLOW}⚠${RESET}  [$label] 复制失败: $dst"
    fi
}

echo ""
echo -e "${BOLD}📦 Step 2: 部署到 AI 工具约定目录 (5 子步)...${RESET}"

# Step 2a: 渲染 plugin manifest（v1.1.0 新增）
echo -e "  ${BOLD}Step 2a: 渲染 6 个 plugin manifest...${RESET}"
RENDERED_DIR="$WORK/.rendered-manifests"
if python "$SCRIPT_DIR/scripts/render_plugins.py" "$WORK" "$RENDERED_DIR"; then
    echo -e "  ${GREEN}✅${RESET}  manifest 渲染完成: $RENDERED_DIR"
else
    echo -e "  ${RED}❌${RESET}  manifest 渲染失败，终止安装"
    exit 1
fi

# Step 2b: 复制 skills/ 到 7 工具的 skills_dir
echo -e "  ${BOLD}Step 2b: 复制 skills/ 到 8 个目标...${RESET}"
for entry in "${TOOL_TARGETS[@]}"; do
    IFS='|' read -r label skills_dir docs_dir plugin_dir <<< "$entry"
    copy_tree "$label skills" "$SKILLS_DIR" "$HOME/$skills_dir"
done

# Step 2c: 复制 hooks/ 到 7 工具的 docs_dir
echo -e "  ${BOLD}Step 2c: 复制 hooks/ 到 8 个目标...${RESET}"
for entry in "${TOOL_TARGETS[@]}"; do
    IFS='|' read -r label skills_dir docs_dir plugin_dir <<< "$entry"
    # hooks 复制到 docs_dir 下（作为插件资源，与 skills 平级）
    copy_tree "$label hooks" "$WORK/hooks" "$HOME/$docs_dir/hooks"
done

# Step 2d: 复制 plugin manifest 到 7 工具的 plugin_dir
echo -e "  ${BOLD}Step 2d: 部署 6 个 plugin manifest...${RESET}"
# 各工具对应不同的 manifest 路径
# 通用映射：tool → manifest source file → target
for entry in "${TOOL_TARGETS[@]}"; do
    IFS='|' read -r label skills_dir docs_dir plugin_dir <<< "$entry"
    case "$label" in
        "ZCode"|"ZCode 内置包"|"ZCode CLI 缓存")
            copy_file "$label plugin.json" "$RENDERED_DIR/zcode-plugin/plugin.json" "$HOME/$plugin_dir/.zcode-plugin/plugin.json"
            ;;
        "Claude Code")
            copy_file "$label plugin.json" "$RENDERED_DIR/claude-plugin/plugin.json" "$HOME/$plugin_dir/.claude-plugin/plugin.json"
            copy_file "$label marketplace.json" "$RENDERED_DIR/claude-plugin/marketplace.json" "$HOME/$plugin_dir/.claude-plugin/marketplace.json"
            ;;
        "Codex")
            copy_file "$label plugin.json" "$RENDERED_DIR/codex-plugin/plugin.json" "$HOME/$plugin_dir/.codex-plugin/plugin.json"
            ;;
        "Gemini CLI")
            copy_file "$label gemini-extension.json" "$RENDERED_DIR/gemini-extension.json" "$HOME/$plugin_dir/gemini-extension.json"
            ;;
        "GitHub Copilot")
            # Copilot 用通用 .mcp.json 即可，不复制 manifest
            ;;
        "Pi")
            # Pi 用 .pi/extensions/loopengine.ts（已是 TypeScript，不通过 manifest 部署）
            ;;
    esac
done

# Step 2e: 复制项目根文档文件到各工具 docs 目录（v1.1.0 新增）
echo -e "  ${BOLD}Step 2e: 复制项目根文档 (AGENTS.md / README.md)...${RESET}"
for entry in "${TOOL_TARGETS[@]}"; do
    IFS='|' read -r label skills_dir docs_dir plugin_dir <<< "$entry"
    copy_file "$label AGENTS.md" "$WORK/AGENTS.md" "$HOME/$docs_dir/AGENTS.md"
    copy_file "$label README.md" "$WORK/README.md" "$HOME/$docs_dir/README.md"
done

# ── Step 3: 安装 MCP 三件套（v1.1.0 数组化）─────────────
# 格式：pkg|cmd1|cmd2|...
MCP_PACKAGES=(
    "jcodemunch-mcp|jcodemunch-mcp"
    "headroom|headroom"
    "repomix|repomix"
)

install_pkg() {
    local pkg="$1" cmd="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅${RESET} ${cmd} 已装"
        return 0
    fi
    # jcodemunch + headroom 用 pip；repomix 用 npm
    if [[ "$pkg" == *"repomix"* ]]; then
        if command -v npm >/dev/null 2>&1; then
            npm install -g "$pkg" 2>/dev/null && { echo -e "  ${GREEN}✅${RESET} ${pkg} (npm)"; return 0; }
        fi
    else
        if command -v pip >/dev/null 2>&1; then
            pip install --user "$pkg" 2>/dev/null && { echo -e "  ${GREEN}✅${RESET} ${pkg} (pip)"; return 0; }
        fi
    fi
    echo -e "  ${YELLOW}⚠${RESET}  ${pkg} 安装失败 — 手动: $([ "$pkg" == *"repomix"* ] && echo "npm i -g $pkg" || echo "pip install --user $pkg")"
}

echo ""
echo -e "${BOLD}🔌 Step 3: 安装 MCP 三件套...${RESET}"
for entry in "${MCP_PACKAGES[@]}"; do
    IFS='|' read -r pkg cmd <<< "$entry"
    install_pkg "$pkg" "$cmd"
done

# ── Step 4: 写 ZCode 桌面版 MCP 配置 ─────────────────────
# 关键：项目根 .mcp.json 只对当前工作区生效；桌面版 ZCode 真正读的是
#       用户级 cli/config.json 的 mcp.servers 字段。
#       2026-06-30 实测发现：手动在桌面 UI 配置三次才成功，根因就是缺这步。
# v1.1.0 简化：删除 zcode-mcp-ensure.sh，Step 4 自身就是自愈入口。

detect_mcp_exe() {
    local fallback="$1"; shift
    for c in "$@"; do
        if command -v "$c" >/dev/null 2>&1; then
            command -v "$c"
            return 0
        fi
    done
    [ -n "$fallback" ] && [ -f "$fallback" ] && printf '%s' "$fallback" && return 0
    return 1
}

to_forward_slashes() {
    echo "$1" | sed 's|\\|/|g'
}

merge_zcode_desktop_config() {
    local cfg="$1" jcode="$2" head="$3" repo="$4"
    mkdir -p "$(dirname "$cfg")"
    python "$SCRIPT_DIR/scripts/merge_zcode_config.py" "$cfg" "$jcode" "$head" "$repo"
}

write_zcode_desktop_config() {
    local cfg="$HOME/.zcode/cli/config.json"

    local jcode_exe head_exe repo_exe
    jcode_exe=$(detect_mcp_exe \
        "$HOME/AppData/Roaming/Python/Python314/Scripts/jcodemunch-mcp.exe" \
        jcodemunch-mcp jcodemunch-mcp.exe) || jcode_exe=""
    head_exe=$(detect_mcp_exe \
        "$HOME/AppData/Roaming/Python/Python314/Scripts/headroom.exe" \
        headroom headroom.exe) || head_exe=""
    repo_exe=$(detect_mcp_exe \
        "$HOME/AppData/Roaming/npm/repomix.cmd" \
        repomix.cmd repomix) || repo_exe=""

    if [ -z "$jcode_exe" ] || [ -z "$head_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  三个 MCP 工具未全部找到，跳过桌面版配置写入"
        echo -e "  ${YELLOW}⚠${RESET}  手动重装: pip install --user jcodemunch-mcp headroom && npm i -g repomix"
        return 0
    fi

    jcode_exe=$(to_forward_slashes "$jcode_exe")
    head_exe=$(to_forward_slashes "$head_exe")
    repo_exe=$(to_forward_slashes "$repo_exe")

    if merge_zcode_desktop_config "$cfg" "$jcode_exe" "$head_exe" "$repo_exe"; then
        echo -e "  ${GREEN}✅${RESET} [ZCode 桌面版 MCP] $cfg"
        TARGETS+=("ZCode 桌面版 MCP:$cfg")
    else
        echo -e "  ${RED}❌${RESET} 合并 $cfg 失败，详见上方 Python 错误"
        return 1
    fi
}

echo ""
echo -e "${BOLD}⚙️  Step 4: 配置 ZCode 桌面版 MCP (~/.zcode/cli/config.json)...${RESET}"
write_zcode_desktop_config

# ── Step 5: 注入全局红线规则（5 条 · v6.9） ──────────────
# 把 AGENTS.md 中的 5 条 🔴 红线章节注入到所有 AI 工具的**用户级**规则文件：
#   1. 用户交互红线       → LOOPENGINE-MANAGED INTERACTION-RULES
#   2. MCP 红线规则       → LOOPENGINE-MANAGED MCP-RULES
#   3. 事实优先硬规则     → LOOPENGINE-MANAGED EVIDENCE-RULES
#   4. 摘要输出红线       → LOOPENGINE-MANAGED SUMMARY-RULES
#   5. 完成前验证红线     → LOOPENGINE-MANAGED VERIFICATION-RULES
MANAGED_RULES=(
    "用户交互红线:INTERACTION-RULES"
    "MCP 红线规则:MCP-RULES"
    "事实优先硬规则:EVIDENCE-RULES"
    "摘要输出红线:SUMMARY-RULES"
    "完成前验证红线:VERIFICATION-RULES"
)

MANAGED_TARGETS=(
    "ZCode|$HOME/.zcode/AGENTS.md"
    "Claude Code|$HOME/.claude/CLAUDE.md"
    "Gemini CLI|$HOME/.gemini/GEMINI.md"
    "Codex|$HOME/.codex/AGENTS.md"
    "Cursor|$HOME/.cursor/rules/loopengine-interaction.mdc"
    "Copilot CLI|$HOME/.copilot/AGENTS.md"
    "Pi|$HOME/.pi/AGENTS.md"
)

extract_rule_block() {
    local src="$1" title="$2" marker="$3" block_dir="$4"
    local begin_line
    begin_line=$(awk -v t="^## 🔴 $title" '$0 ~ t { print NR; exit }' "$src")
    if [ -z "$begin_line" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  AGENTS.md 中未找到 '$title' 章节，跳过"
        return 1
    fi
    local next_section_line
    next_section_line=$(awk -v start="$begin_line" 'NR > start && /^## / { print NR; exit }' "$src")
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
    echo -e "  ${GREEN}✅${RESET} 提取: ${CYAN}${title}${RESET} → ${marker}"
    return 0
}

inject_rules_to_target() {
    local label="$1" target="$2" block_dir="$3"
    mkdir -p "$(dirname "$target")"
    if python "$SCRIPT_DIR/scripts/inject_rules.py" "$target" "$block_dir"; then
        echo -e "  ${GREEN}✅${RESET} [$label 红线] $target"
        TARGETS+=("$label 红线:$target")
        return 0
    fi
    echo -e "  ${RED}❌${RESET} [$label 红线] 注入失败: $target"
    return 1
}

install_managed_rules() {
    local src="$WORK/AGENTS.md"
    [ ! -f "$src" ] && { echo -e "  ${YELLOW}⚠${RESET}  $src 不存在，跳过"; return 0; }

    local block_dir
    block_dir=$(mktemp -d)
    __cleanup_block_dir() { rm -rf "$block_dir"; }

    local extracted_count=0
    for entry in "${MANAGED_RULES[@]}"; do
        local title="${entry%%:*}"
        local marker="${entry##*:}"
        if extract_rule_block "$src" "$title" "$marker" "$block_dir"; then
            extracted_count=$((extracted_count + 1))
        fi
    done

    if [ "$extracted_count" -eq 0 ]; then
        echo -e "  ${RED}❌${RESET}  未提取到任何规则章节，退出"
        __cleanup_block_dir
        return 1
    fi

    for entry in "${MANAGED_TARGETS[@]}"; do
        local label="${entry%%|*}"
        local target="${entry##*|}"
        inject_rules_to_target "$label" "$target" "$block_dir" || true
    done

    __cleanup_block_dir
}

echo ""
echo -e "${BOLD}🌐 Step 5: 注入全局红线规则 (7 工具 × 5 红线)...${RESET}"
install_managed_rules

# ── Step 6: 部署自检（v1.1.0 新增） ─────────────────────
# 验证关键路径都生成了；防止静默失败
echo ""
echo -e "${BOLD}🔬 Step 6: 部署自检...${RESET}"
CHECK_PASS=0
CHECK_FAIL=0
check_path() {
    local desc="$1" path="$2"
    if [ -e "$path" ]; then
        echo -e "  ${GREEN}✅${RESET} $desc"
        CHECK_PASS=$((CHECK_PASS + 1))
    else
        echo -e "  ${RED}❌${RESET} $desc 缺失: $path"
        CHECK_FAIL=$((CHECK_FAIL + 1))
    fi
}
# 至少 1 个 skills 目录应包含 SKILL.md
SKILL_OK=false
for entry in "${TOOL_TARGETS[@]}"; do
    IFS='|' read -r label skills_dir docs_dir plugin_dir <<< "$entry"
    if [ -d "$HOME/$skills_dir/orch" ] || [ -d "$HOME/$skills_dir/loop" ]; then
        SKILL_OK=true
        break
    fi
done
if $SKILL_OK; then
    echo -e "  ${GREEN}✅${RESET} 至少 1 个工具的 skills 目录已部署"
    CHECK_PASS=$((CHECK_PASS + 1))
else
    echo -e "  ${RED}❌${RESET} 所有工具的 skills 目录都未正确部署"
    CHECK_FAIL=$((CHECK_FAIL + 1))
fi
# manifest 渲染目录应至少含 5 个 JSON
RENDERED_COUNT=$(find "$RENDERED_DIR" -name "*.json" 2>/dev/null | wc -l)
if [ "$RENDERED_COUNT" -ge 5 ]; then
    echo -e "  ${GREEN}✅${RESET} 渲染 manifest 数: $RENDERED_COUNT (>=5)"
    CHECK_PASS=$((CHECK_PASS + 1))
else
    echo -e "  ${RED}❌${RESET} 渲染 manifest 数: $RENDERED_COUNT (<5)"
    CHECK_FAIL=$((CHECK_FAIL + 1))
fi
# 写入版本号文件
mkdir -p "$HOME/.loopengine"
echo "$VERSION" > "$INSTALLED_VERSION_FILE"
echo -e "  ${GREEN}✅${RESET} 写入版本号文件: $INSTALLED_VERSION_FILE"
CHECK_PASS=$((CHECK_PASS + 1))

if [ "$CHECK_FAIL" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠${RESET}  自检: ${CHECK_PASS} 通过 / ${CHECK_FAIL} 失败"
else
    echo -e "  ${GREEN}✅${RESET} 自检: ${CHECK_PASS} 项全部通过"
fi

# ── 总结 ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}${GREEN}✅ LoopEngine v${VERSION} 安装完成${RESET} · 部署到 ${#TARGETS[@]} 个路径"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
for t in "${TARGETS[@]}"; do
    echo -e "  ${CYAN}•${RESET} $t"
done
echo ""
echo -e "${BOLD}💡 验证 (开新 AI 会话后发送):${RESET}"
echo -e "  ${CYAN}\"告诉我 LoopEngine 的核心价值，并列出 orch 调度的 5 类复合任务\"${RESET}"
echo ""

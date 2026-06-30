#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# LoopEngine 一键安装 — 极简 curl 一条龙
# ════════════════════════════════════════════════════════════
# 一行安装:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
#
# 设计哲学:
#   • 不依赖 ZCode 内部插件市场 / marketplace.json / plugin.json 注册
#   • 只复制技能源 (skills/*) 到各 AI 工具的"约定技能目录"
#   • MCP 三件套 (jcodemunch-mcp / repomix / headroom) 一次装好
#   • 装完就能用，不依赖 AI 工具的"重启"行为
# ════════════════════════════════════════════════════════════

set -euo pipefail

REPO="https://github.com/tsfdsong/loop_engineering"
BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"; RED="\033[31m"; RESET="\033[0m"
TARGETS=()

# SCRIPT_DIR = 安装脚本所在目录（指向 $WORK 的副本根；用于引用 scripts/*.py）
# 注：本脚本通常被 curl | bash 执行，无 $0；故用 BASH_SOURCE 兜底
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║  LoopEngine — 一键安装 (curl 一条龙)            ║${RESET}"
echo -e "${BOLD}${CYAN}║  把全部技能直接塞到 AI 工具目录                  ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Step 1: 拉最新源码 ────────────────────────────────────
WORK="${TMPDIR:-/tmp}/loopengine-install-$$"
# 用单引号包 trap 命令，$WORK 在 trap 触发时再展开并已带引号，可安全处理空格路径
trap 'rm -rf "$WORK"' EXIT
echo -e "${BOLD}📥 Step 1: 拉取最新源码...${RESET}"
if ! git clone --depth 1 --quiet "$REPO" "$WORK" 2>/dev/null; then
    echo -e "${RED}❌ 无法 clone 仓库，请检查网络 / VPN${RESET}"
    exit 1
fi
SKILLS_DIR="$WORK/skills"
SKILL_COUNT=$(find "$SKILLS_DIR" -name SKILL.md 2>/dev/null | wc -l)
echo -e "  ${GREEN}✅${RESET} 已克隆到 $WORK · ${SKILL_COUNT} 个技能"

# ── Step 2: 复制技能到各工具的约定目录 ──────────────────────
copy_skills() {
    local label="$1"
    local target="$2"
    mkdir -p "$target"
    # 先清空目标目录（保留目录本身），避免已删除/重命名的技能（如 skill-hub→orch）残留
    # 注：find 失败通常因目录为空（无文件可删），属正常；不视为错误
    if ! find "$target" -mindepth 1 -delete 2>/dev/null; then
        echo -e "  ${YELLOW}⚠${RESET}  [$label] 清理旧文件失败: $target（继续复制）"
    fi
    if cp -r "$SKILLS_DIR/." "$target/" 2>/dev/null; then
        TARGETS+=("$label:$target")
        echo -e "  ${GREEN}✅${RESET} [$label] $target"
    else
        echo -e "  ${YELLOW}⚠${RESET}  [$label] 复制失败: $target"
    fi
}

echo ""
echo -e "${BOLD}📦 Step 2: 部署技能到 AI 工具约定目录...${RESET}"

# 关键：ZCode 用户级 fallback (让 ZCode 找技能 + 兼容其它扫描)
copy_skills "ZCode(.agents fallback)" "$HOME/.agents/skills"

# 各 AI 编程工具
copy_skills "Claude Code"        "$HOME/.claude/skills/loopengine"
copy_skills "Codex"              "$HOME/.codex/skills/loopengine"
copy_skills "Gemini CLI"         "$HOME/.gemini/extensions/loopengine/skills"
copy_skills "GitHub Copilot"     "$HOME/.copilot/skills/loopengine"
copy_skills "Pi"                 "$HOME/.pi/skills/loopengine"
copy_skills "ZCode 内置包"        "$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin/skills"
copy_skills "ZCode CLI 缓存"      "$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/skills"

# ── Step 3: 安装 MCP 三件套 ────────────────────────────────
install_pkg() {
    local pkg="$1"; shift
    local cmds=("$@")
    for c in "${cmds[@]}"; do
        if command -v "$c" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✅${RESET} ${cmds[*]} 已装"
            return 0
        fi
    done
    if command -v pip >/dev/null 2>&1 && [[ "$pkg" == *"jcodemunch"* || "$pkg" == *"headroom"* ]]; then
        pip install --user "$pkg" 2>/dev/null && {
            echo -e "  ${GREEN}✅${RESET} ${pkg} (pip)"; return 0
        }
    fi
    if command -v npm >/dev/null 2>&1 && [[ "$pkg" == *"repomix"* ]]; then
        npm install -g "$pkg" 2>/dev/null && {
            echo -e "  ${GREEN}✅${RESET} ${pkg} (npm)"; return 0
        }
    fi
    echo -e "  ${YELLOW}⚠${RESET}  ${pkg} 安装失败 — 手动: pip install --user $pkg"
}

echo ""
echo -e "${BOLD}🔌 Step 3: 安装 MCP 三件套 (jcodemunch + repomix + headroom)...${RESET}"
install_pkg "jcodemunch-mcp"  "jcodemunch-mcp"
install_pkg "headroom"        "headroom"
install_pkg "repomix"         "repomix"

# ── Step 4: 写入 ZCode 桌面版 MCP 配置（~/.zcode/cli/config.json） ─────
# 关键：项目根 .mcp.json 只对当前工作区生效；桌面版 ZCode 真正读的是
#       用户级 cli/config.json 的 mcp.servers 字段。
#       2026-06-30 实测发现：手动在桌面 UI 配置三次才成功，根因就是缺这步。

# 探测单个 MCP 工具可执行路径（候选命令 + Windows fallback）
# 用法：detect_mcp_exe <fallback_path> <cmd>...
# 返回：找到的绝对路径（stdout），找不到返回 1
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

# 把 3 个 MCP exe 路径统一转正斜杠（Windows JSON 推荐）
to_forward_slashes() {
    echo "$1" | sed 's|\\|/|g'
}

# 合并 MCP 配置到 ZCode 桌面版 config.json（delegates to Python 脚本）
# 保留用户其他顶层字段（provider / model / 自定义设置等）
merge_zcode_desktop_config() {
    local cfg="$1" jcode="$2" head="$3" repo="$4"
    mkdir -p "$(dirname "$cfg")"
    python "$SCRIPT_DIR/scripts/merge_zcode_config.py" "$cfg" "$jcode" "$head" "$repo"
}

# 主入口：探测 + 合并 + 报告
write_zcode_desktop_config() {
    local cfg="$HOME/.zcode/cli/config.json"

    # 探测 3 个 MCP exe 路径
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

    # 三个任一缺失 → 警告并跳过（不中断整体安装）
    if [ -z "$jcode_exe" ] || [ -z "$head_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  三个 MCP 工具未全部找到，跳过桌面版配置写入"
        echo -e "  ${YELLOW}⚠${RESET}  手动重装: pip install --user jcodemunch-mcp headroom && npm i -g repomix"
        return 0
    fi

    # Windows 路径统一转正斜杠
    jcode_exe=$(to_forward_slashes "$jcode_exe")
    head_exe=$(to_forward_slashes "$head_exe")
    repo_exe=$(to_forward_slashes "$repo_exe")

    # 调用 Python 脚本做合并
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

# ── Step 5: 注入全局红线规则（5 条 · 2026-06-30 扩展为 v6.9） ──────────────
# 把 AGENTS.md 中的 5 条 🔴 红线章节注入到所有 AI 工具的**用户级**规则文件：
#   1. 用户交互红线       → LOOPENGINE-MANAGED INTERACTION-RULES
#   2. MCP 红线规则       → LOOPENGINE-MANAGED MCP-RULES
#   3. 事实优先硬规则     → LOOPENGINE-MANAGED EVIDENCE-RULES
#   4. 摘要输出红线       → LOOPENGINE-MANAGED SUMMARY-RULES（v6.8 新增）
#   5. 完成前验证红线     → LOOPENGINE-MANAGED VERIFICATION-RULES（v6.9 新增）
# 关键设计：sentinel markers（HTML 注释）+ Python 合并，保证：
#   1. 幂等性 —— 重复执行不重复插入（找到旧块则替换）
#   2. 用户保留 —— 用户在文件其他章节的自定义内容**不会被覆盖**
#   3. 自动更新 —— 项目升级（update.sh → install.sh）时，规则自动同步
#   4. 全局生效 —— 用户级 (~/.xxx/...) 而非项目级，新会话立即生效
#   5. 多规则支持 —— 每条红线独立标记，独立追加/更新（v6.8 扩展）
# 规则注册表：(章节标题 | marker 类型)
# 注意：使用 awk 而非 grep —— Git Bash Windows 下 grep 处理 `^## 🔴`（4 字节 UTF-8 emoji + ^ 锚点）失败
MANAGED_RULES=(
    "用户交互红线:INTERACTION-RULES"
    "MCP 红线规则:MCP-RULES"
    "事实优先硬规则:EVIDENCE-RULES"
    "摘要输出红线:SUMMARY-RULES"
    "完成前验证红线:VERIFICATION-RULES"
)

# 目标：(标签 | 用户级规则文件路径)
# 注意：路径是用户级 (~/.xxx/...)，与项目级 (./AGENTS.md) 不同，确保**全局生效**
MANAGED_TARGETS=(
    "ZCode|$HOME/.zcode/AGENTS.md"
    "Claude Code|$HOME/.claude/CLAUDE.md"
    "Gemini CLI|$HOME/.gemini/GEMINI.md"
    "Codex|$HOME/.codex/AGENTS.md"
    "Cursor|$HOME/.cursor/rules/loopengine-interaction.mdc"
    "Copilot CLI|$HOME/.copilot/AGENTS.md"
    "Pi|$HOME/.pi/AGENTS.md"
)

# 从 AGENTS.md 提取单条规则章节 → 写入 $block_dir/$marker
# 用法：extract_rule_block <src> <title> <marker> <block_dir>
# 返回 0 成功，1 章节未找到（不致命，调用方继续）
extract_rule_block() {
    local src="$1" title="$2" marker="$3" block_dir="$4"

    local begin_line
    begin_line=$(awk -v t="^## 🔴 $title" '$0 ~ t { print NR; exit }' "$src")
    if [ -z "$begin_line" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  AGENTS.md 中未找到 '$title' 章节，跳过"
        return 1
    fi

    # 找下一 `## ` 章节的起始行，作为本章节结束边界
    local next_section_line
    next_section_line=$(awk -v start="$begin_line" 'NR > start && /^## / { print NR; exit }' "$src")
    local end_line
    if [ -n "$next_section_line" ]; then
        end_line=$((next_section_line - 1))
    else
        end_line=$(wc -l < "$src")
    fi

    # 用 awk 提取行范围（更跨平台、避免 sed 在 Windows 下的转义问题）
    local managed_block
    managed_block=$(awk -v start="$begin_line" -v end="$end_line" 'NR>=start && NR<=end' "$src")
    local wrapped_block
    wrapped_block=$(printf '<!-- BEGIN LOOPENGINE-MANAGED %s -->\n%s\n<!-- END LOOPENGINE-MANAGED %s -->' \
        "$marker" "$managed_block" "$marker")
    echo "$wrapped_block" > "$block_dir/$marker"
    echo -e "  ${GREEN}✅${RESET} 提取: ${CYAN}${title}${RESET} → ${marker}"
    return 0
}

# 把 $block_dir 下所有 marker 块注入到单个目标文件
# 用法：inject_rules_to_target <label> <target_path> <block_dir>
# 返回 0 成功，1 Python 失败
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

# 主入口：编排 extract → inject → cleanup
install_managed_rules() {
    local src="$WORK/AGENTS.md"
    [ ! -f "$src" ] && { echo -e "  ${YELLOW}⚠${RESET}  $src 不存在，跳过"; return 0; }

    # 临时目录存放提取的规则块（避免 bash 参数长度限制 + 多 marker 一次性传给 Python）
    # 改用显式清理（bash < 4.4 不支持 trap ... RETURN；EXIT/ERR 在函数内行为不稳定）
    local block_dir
    block_dir=$(mktemp -d)
    # 显式清理（任何 return 路径前都需调用 __cleanup_block_dir）
    __cleanup_block_dir() { rm -rf "$block_dir"; }

    # 阶段 1：批量提取
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

    # 阶段 2：批量注入
    for entry in "${MANAGED_TARGETS[@]}"; do
        local label="${entry%%|*}"
        local target="${entry##*|}"
        inject_rules_to_target "$label" "$target" "$block_dir" || true
    done

    # 显式清理临时块目录（兼容 bash 3.2+；旧 trap RETURN 方案在 macOS 默认 bash 上失败）
    __cleanup_block_dir
}

echo ""
echo -e "${BOLD}🌐 Step 5: 注入全局红线规则（7 个 AI 工具 × 5 条红线）...${RESET}"
install_managed_rules

# ── 总结 ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}${GREEN}✅ 安装完成${RESET} · 部署到 ${#TARGETS[@]} 个 AI 工具技能目录"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
for t in "${TARGETS[@]}"; do
    echo -e "  ${CYAN}•${RESET} $t"
done
echo ""
echo -e "${BOLD}💡 验证 (开新 AI 会话后发送):${RESET}"
echo -e "  ${CYAN}\"告诉我 LoopEngine 的核心价值，并列出 orch 调度的 5 类复合任务\"${RESET}"
echo ""

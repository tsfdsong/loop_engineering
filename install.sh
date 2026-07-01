#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# LoopEngine 一键安装 v1.2.2 — 首次安装 + 版本更新合一
# ════════════════════════════════════════════════════════════
# 一行安装:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
#
# 智能模式（默认）：
#   - 未装 ~/.loopengine/.installed_version → 首次安装
#   - 已装同版 → 5 秒等待（防误触，--force 跳过）
#   - 已装旧版 → 升级
#   - 拉源码每次都做（git clone --depth 1），所以 install.sh 天然具备"更新"能力
#
# 参数:
#   --dry-run   只检查版本不实际安装（拉源码 + 比对 + 输出计划）
#   --force     跳过 5 秒等待，强制重装（同版本也执行）
#   -h, --help  显示帮助
#
# 设计哲学:
#   • 不依赖 ZCode 内部插件市场 / marketplace.json / plugin.json 注册
#   • 一次拉源码 → 渲染 plugin manifest → 部署 7 工具 + MCP 三件套 + 7 红线
#   • 装完就能用，不依赖 AI 工具的"重启"行为
#   • 幂等：重复执行不破坏（sentinel markers + 模板渲染）
#   • 单点真源：v1.2.2 起 install.sh = install + update
#
# v1.2.2 修复（2026-07-01 Cursor 兼容 + 7 红线同步）：
#   • extract_rule_block 加 ``` 围栏状态跟踪 — 修复 SUMMARY-RULES 在 4.3 模板
#     `## 📌 核心摘要` 处被误截断的 bug（同时修章节 6 PROGRESS-RULES 的 6.4
#     模板内 `## 📊 进度汇报 (N/M)` 同类问题）
#   • MANAGED_RULES 5 → 7 条（新增进度汇报红线 + Subagent 边界红线，
#     与 AGENTS.md v1.0.2+ 的 7 条红线章节一致）
#   • TOOL_ROOT_DIRS 加 Cursor 项（~/.cursor/skills/loopengine/）
#   • Step 2d case 加 Cursor 分支（部署已渲染的 cursor-plugin/plugin.json）
#   • VERSION 1.2.1 → 1.2.2
#
# v1.2.1 修复（2026-07-01 同步 v1.2.1 git tag）：
#   • VERSION 1.2.0 → 1.2.1（与 git tag v1.2.1 同步）
#   • 头注释 5 红线 → 7 红线（与 AGENTS.md 实际注入的红线数一致）
#   • plugin manifest version 1.0.2 → 1.2.1（与 install.sh VERSION 同步）
#
# v1.2.0 修复（2026-07-01 智能模式合一）：
#   • 新增参数：--dry-run / --force / --help
#   • Step 0 智能模式：自动判断 首次装 / 升级 / 同版本 5秒等待
#   • docs/INSTALL.md 更新：去掉 update.sh 章节，改用 bash install.sh
#
# v1.1.0 历史修复（保留）：
#   • Step 0  初始版本自检
#   • Step 2  同步范围扩大：skills/ + hooks/ + AGENTS.md + README.md + 6 个 plugin manifest
#   • Step 2a render_plugins.py 渲染 7 个 manifest
#   • Step 3  数组化（消除 3 个重复 if）
#   • Step 4  ZCode 桌面版 MCP
#   • Step 5  5 条红线 sentinel markers（v1.2.2 升级到 7 条）
#   • Step 6  部署自检
# ════════════════════════════════════════════════════════════

set -euo pipefail

VERSION="1.2.2"
REPO="https://github.com/tsfdsong/loop_engineering"
BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"
TARGETS=()

# ── 参数解析（v1.2.0 新增）────────────────────────────
DRY_RUN=false
FORCE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            cat <<'HELP'
LoopEngine 一键安装 v1.2.2（首次安装 + 版本更新合一）

用法:
  bash install.sh              # 智能模式（首次装 / 升级 / 同版本 5秒等待）
  bash install.sh --force      # 强制重装（跳过 5 秒等待）
  bash install.sh --dry-run    # 只检查不安装
  bash install.sh -h           # 显示此帮助

推荐一行安装:
  curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash

更新 = 重新跑 install.sh（自动智能模式）。
HELP
            exit 0
            ;;
        *)
            echo -e "\033[31m❌ 未知参数: $1\033[0m（用 -h 看帮助）" >&2
            exit 1
            ;;
    esac
done

# SCRIPT_DIR = $WORK（clone 出来的代码根），用于引用 scripts/*.py。
# 关键：不能用 BASH_SOURCE — curl | bash 时 BASH_SOURCE 为空；本地 install.sh
# 也不指向 clone 出来的代码副本。统一用 $WORK 更可靠。
SCRIPT_DIR=""  # Step 1 后赋值（$WORK）

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║  LoopEngine v${VERSION} — 一键安装/更新合一        ║${RESET}"
echo -e "${BOLD}${CYAN}║  把技能/AGENTS.md/hooks/MCP/7 红线全量同步      ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
if [ "$DRY_RUN" = true ]; then
    echo -e "  ${CYAN}ℹ${RESET}  ${BOLD}--dry-run${RESET} 模式：只检查不安装"
fi
if [ "$FORCE" = true ]; then
    echo -e "  ${CYAN}ℹ${RESET}  ${BOLD}--force${RESET} 模式：跳过 5 秒等待，强制重装"
fi
echo ""

# ── Step 0: 版本自检 + 智能模式（v1.2.0 升级）──────────────
# 抽出 2 个函数（P1）：describe_install_state（纯状态判断） + smart_check_version（输出+等待）
# 状态: first_install / same_version / upgrade
describe_install_state() {
    local installed="$1" target="$2"
    if [ -z "$installed" ]; then
        echo "first_install"
    elif [ "$installed" = "$target" ]; then
        echo "same_version"
    else
        echo "upgrade"
    fi
}

# 输出 + 等待（Step 0 用）
smart_check_version() {
    local installed="$1" target="$2"
    local state
    state=$(describe_install_state "$installed" "$target")
    case "$state" in
        first_install)
            echo -e "  ${GREEN}✅${RESET}  首次安装 v${target}"
            ;;
        same_version)
            if [ "$FORCE" = true ]; then
                echo -e "  ${YELLOW}⚠${RESET}  检测到 v${installed}（同版）— --force 强制重装"
            elif [ "$DRY_RUN" = true ]; then
                echo -e "  ${GREEN}✅${RESET}  已装 v${installed}（同版）— dry-run 将跳过安装"
            else
                echo -e "  ${YELLOW}⚠${RESET}  检测到已安装 v${installed}（同版），5 秒后继续（强制重装请 --force）..."
                sleep 5
            fi
            ;;
        upgrade)
            echo -e "  ${GREEN}✅${RESET}  检测到 v${installed:-?}，升级到 v${target}"
            ;;
    esac
}

echo -e "${BOLD}🔍 Step 0: 版本自检（智能模式）...${RESET}"
INSTALLED_VERSION_FILE="$HOME/.loopengine/.installed_version"
INSTALLED_VERSION=""
[ -f "$INSTALLED_VERSION_FILE" ] && INSTALLED_VERSION=$(cat "$INSTALLED_VERSION_FILE" 2>/dev/null || echo "")
smart_check_version "$INSTALLED_VERSION" "$VERSION"

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
SCRIPT_DIR="$WORK"  # 引用 scripts/*.py 的根
SKILL_COUNT=$(find "$SKILLS_DIR" -name SKILL.md 2>/dev/null | wc -l)
echo -e "  ${GREEN}✅${RESET} 已克隆到 $WORK · ${SKILL_COUNT} 个技能"

# ── --dry-run 早退出（v1.2.0 新增）────────────────────────
# 拉完源码 + 自检后即退出，不执行 Step 2-6 部署
# 输出计划：复用 describe_install_state（P1 重构）
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${BOLD}${CYAN}🔍 --dry-run 模式总结（不执行部署）${RESET}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    state=$(describe_install_state "$INSTALLED_VERSION" "$VERSION")
    case "$state" in
        first_install)
            echo -e "  ${CYAN}•${RESET} 状态: 未安装"
            echo -e "  ${CYAN}•${RESET} 计划: 首次安装 v${VERSION}"
            ;;
        same_version)
            echo -e "  ${CYAN}•${RESET} 状态: 已装 v${INSTALLED_VERSION}（同版）"
            echo -e "  ${CYAN}•${RESET} 计划: 无需更新（如需强制重装请 --force）"
            ;;
        upgrade)
            echo -e "  ${CYAN}•${RESET} 状态: 已装 v${INSTALLED_VERSION:-?}"
            echo -e "  ${CYAN}•${RESET} 计划: 升级到 v${VERSION}（如需执行请去掉 --dry-run）"
            ;;
    esac
    echo -e "  ${CYAN}•${RESET} 远端版本: v${VERSION}"
    echo -e "  ${CYAN}•${RESET} 技能数: ${SKILL_COUNT}"
    echo -e "  ${CYAN}•${RESET} 工作目录: $WORK"
    echo ""
    exit 0
fi

# ── Step 2: 部署（5 个子步骤 · v1.1.0 扩展 · v1.2.2 Cursor 集成）─────
# 9 个目标工具的"约定根目录" + 单一映射（P2 重构：3 列同值 → 单列）
# 格式：label|root_dir（skills/hooks/plugin 全部部署到 root_dir）
TOOL_ROOT_DIRS=(
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
echo -e "  ${BOLD}Step 2a: 渲染 7 个 plugin manifest...${RESET}"
RENDERED_DIR="$WORK/.rendered-manifests"
if python "$SCRIPT_DIR/scripts/render_plugins.py" "$WORK" "$RENDERED_DIR"; then
    echo -e "  ${GREEN}✅${RESET}  manifest 渲染完成: $RENDERED_DIR"
else
    echo -e "  ${RED}❌${RESET}  manifest 渲染失败，终止安装"
    exit 1
fi

# Step 2b: 复制 skills/ 到 9 工具的 root_dir
echo -e "  ${BOLD}Step 2b: 复制 skills/ 到 9 个目标...${RESET}"
for entry in "${TOOL_ROOT_DIRS[@]}"; do
    IFS='|' read -r label root_dir <<< "$entry"
    copy_tree "$label skills" "$SKILLS_DIR" "$root_dir"
done

# Step 2c: 复制 hooks/ 到 9 工具的 root_dir/hooks
echo -e "  ${BOLD}Step 2c: 复制 hooks/ 到 9 个目标...${RESET}"
for entry in "${TOOL_ROOT_DIRS[@]}"; do
    IFS='|' read -r label root_dir <<< "$entry"
    copy_tree "$label hooks" "$WORK/hooks" "$root_dir/hooks"
done

# Step 2d: 部署 7 plugin manifest 到 9 工具的 root_dir/.xxx-plugin
echo -e "  ${BOLD}Step 2d: 部署 7 个 plugin manifest...${RESET}"
for entry in "${TOOL_ROOT_DIRS[@]}"; do
    IFS='|' read -r label root_dir <<< "$entry"
    case "$label" in
        "ZCode"|"ZCode 内置包"|"ZCode CLI 缓存")
            copy_file "$label plugin.json" "$RENDERED_DIR/zcode-plugin/plugin.json" "$root_dir/.zcode-plugin/plugin.json"
            ;;
        "Claude Code")
            copy_file "$label plugin.json" "$RENDERED_DIR/claude-plugin/plugin.json" "$root_dir/.claude-plugin/plugin.json"
            copy_file "$label marketplace.json" "$RENDERED_DIR/claude-plugin/marketplace.json" "$root_dir/.claude-plugin/marketplace.json"
            ;;
        "Codex")
            copy_file "$label plugin.json" "$RENDERED_DIR/codex-plugin/plugin.json" "$root_dir/.codex-plugin/plugin.json"
            ;;
        "Cursor")
            # v1.2.2 新增：Cursor plugin manifest（render_plugins.py 已渲染到 out_dir/cursor-plugin/）
            copy_file "$label plugin.json" "$RENDERED_DIR/cursor-plugin/plugin.json" "$root_dir/.cursor-plugin/plugin.json"
            ;;
        "Gemini CLI")
            copy_file "$label gemini-extension.json" "$RENDERED_DIR/gemini-extension.json" "$root_dir/gemini-extension.json"
            ;;
        "GitHub Copilot")
            # Copilot 用通用 .mcp.json 即可，不复制 manifest
            ;;
        "Pi")
            # Pi 用 .pi/extensions/loopengine.ts（已是 TypeScript，不通过 manifest 部署）
            ;;
    esac
done

# Step 2e: 复制项目根文档文件到各工具 root_dir
echo -e "  ${BOLD}Step 2e: 复制项目根文档 (AGENTS.md / README.md)...${RESET}"
for entry in "${TOOL_ROOT_DIRS[@]}"; do
    IFS='|' read -r label root_dir <<< "$entry"
    copy_file "$label AGENTS.md" "$WORK/AGENTS.md" "$root_dir/AGENTS.md"
    copy_file "$label README.md" "$WORK/README.md" "$root_dir/README.md"
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

# ── Step 5: 注入全局红线规则（7 条 · v6.10 · v1.2.2 升级） ──────────
# 把 AGENTS.md 中的 7 条 🔴 红线章节注入到所有 AI 工具的**用户级**规则文件：
#   1. 用户交互红线       → LOOPENGINE-MANAGED INTERACTION-RULES
#   2. MCP 红线规则       → LOOPENGINE-MANAGED MCP-RULES
#   3. 事实优先硬规则     → LOOPENGINE-MANAGED EVIDENCE-RULES
#   4. 摘要输出红线       → LOOPENGINE-MANAGED SUMMARY-RULES
#   5. 完成前验证红线     → LOOPENGINE-MANAGED VERIFICATION-RULES
#   6. 进度汇报红线       → LOOPENGINE-MANAGED PROGRESS-RULES       (v1.2.2 新增)
#   7. Subagent 边界红线  → LOOPENGINE-MANAGED SUBAGENT-RULES      (v1.2.2 新增)
MANAGED_RULES=(
    "用户交互红线:INTERACTION-RULES"
    "MCP 红线规则:MCP-RULES"
    "事实优先硬规则:EVIDENCE-RULES"
    "摘要输出红线:SUMMARY-RULES"
    "完成前验证红线:VERIFICATION-RULES"
    "进度汇报红线:PROGRESS-RULES"
    "Subagent 边界红线:SUBAGENT-RULES"
)

MANAGED_TARGETS=(
    "ZCode|$HOME/.zcode/AGENTS.md"
    "Claude Code|$HOME/.claude/CLAUDE.md"
    "Gemini CLI|$HOME/.gemini/GEMINI.md"
    "Codex|$HOME/.codex/AGENTS.md"
    "Cursor|$HOME/.cursor/rules/loopengine-interaction.mdc"
    "GitHub Copilot|$HOME/.copilot/AGENTS.md"
    "Pi|$HOME/.pi/AGENTS.md"
)

extract_rule_block() {
    local src="$1" title="$2" marker="$3" block_dir="$4"
    # v1.2.0 修复：兼容章节标题的数字前缀（如 "## 🔴 1. MCP 红线规则..."）
    # 用 "## .*🔴.*$title" 而非 "^## 🔴 $title" — 这样 main/fix 分支都兼容
    local begin_line
    begin_line=$(awk -v t="^## .*🔴.*$title" '$0 ~ t { print NR; exit }' "$src")
    if [ -z "$begin_line" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  AGENTS.md 中未找到 '$title' 章节，跳过"
        return 1
    fi
    local next_section_line
    # v1.2.2 修复：用 ``` 围栏跟踪状态，跳过代码块内的 ## 标题
    # 否则 SUMMARY-RULES 会在 4.3 模板 `## 📌 核心摘要` 处被误截断（丢失 4.3-4.5）；
    # 章节 6 PROGRESS-RULES 的 6.4 模板内 `## 📊 进度汇报 (N/M)` 同理。
    # 实现要点：
    #   - 切换 ``` 行用 `/^```/` 匹配（围栏行通常独占一行）
    #   - `in_code` 状态翻转：`!in_code && /^## /` 才算章节边界
    #   - `BEGIN{RS=""}` 不适用 — 我们仍按行处理，只是过滤围栏内行
    next_section_line=$(awk -v start="$begin_line" '
        BEGIN { in_code = 0 }
        NR > start {
            # v1.2.2 防御性升级：识别缩进 fence（4 空格 / tab）+ 可选语言标识符
            # 例如 `    ```bash `、` ```markdown ` 都正确识别为围栏切换
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
echo -e "${BOLD}🌐 Step 5: 注入全局红线规则 (7 工具 × 7 红线)...${RESET}"
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
# 至少 8 个 skills 目录应包含 SKILL.md（v1.2.2 加严；9 工具允许 1 个失败）
SKILL_OK_COUNT=0
for entry in "${TOOL_ROOT_DIRS[@]}"; do
    IFS='|' read -r label root_dir <<< "$entry"
    if [ -d "$root_dir/orch" ] || [ -d "$root_dir/loop" ]; then
        SKILL_OK_COUNT=$((SKILL_OK_COUNT + 1))
    fi
done
if [ "$SKILL_OK_COUNT" -ge 8 ]; then
    echo -e "  ${GREEN}✅${RESET} 至少 8 个工具的 skills 目录已部署（实际 $SKILL_OK_COUNT/9）"
    CHECK_PASS=$((CHECK_PASS + 1))
else
    echo -e "  ${RED}❌${RESET} skills 目录部署不足：$SKILL_OK_COUNT/9 (< 8)"
    CHECK_FAIL=$((CHECK_FAIL + 1))
fi
# manifest 渲染目录应至少含 7 个 JSON（v1.2.2 加严：5 plugin.json + 1 gemini-extension + 1 marketplace）
RENDERED_COUNT=$(find "$RENDERED_DIR" -name "*.json" 2>/dev/null | wc -l)
if [ "$RENDERED_COUNT" -ge 7 ]; then
    echo -e "  ${GREEN}✅${RESET} 渲染 manifest 数: $RENDERED_COUNT (>=7)"
    CHECK_PASS=$((CHECK_PASS + 1))
else
    echo -e "  ${RED}❌${RESET} 渲染 manifest 数: $RENDERED_COUNT (<7)"
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

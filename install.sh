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

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║  LoopEngine — 一键安装 (curl 一条龙)            ║${RESET}"
echo -e "${BOLD}${CYAN}║  把全部技能直接塞到 AI 工具目录                  ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Step 1: 拉最新源码 ────────────────────────────────────
WORK="${TMPDIR:-/tmp}/loopengine-install-$$"
trap "rm -rf '$WORK'" EXIT
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
write_zcode_desktop_config() {
    local cfg="$HOME/.zcode/cli/config.json"

    # 探测三个 MCP exe 实际路径（Windows 优先 .exe / .cmd）
    local jcode_exe="" head_exe="" repo_exe=""

    # jcodemunch-mcp: PATH → pip user Scripts → npm
    for c in jcodemunch-mcp jcodemunch-mcp.exe; do
        if command -v "$c" >/dev/null 2>&1; then jcode_exe=$(command -v "$c"); break; fi
    done
    [ -z "$jcode_exe" ] && [ -f "$HOME/AppData/Roaming/Python/Python314/Scripts/jcodemunch-mcp.exe" ] && \
        jcode_exe="$HOME/AppData/Roaming/Python/Python314/Scripts/jcodemunch-mcp.exe"

    # headroom
    for c in headroom headroom.exe; do
        if command -v "$c" >/dev/null 2>&1; then head_exe=$(command -v "$c"); break; fi
    done
    [ -z "$head_exe" ] && [ -f "$HOME/AppData/Roaming/Python/Python314/Scripts/headroom.exe" ] && \
        head_exe="$HOME/AppData/Roaming/Python/Python314/Scripts/headroom.exe"

    # repomix: .cmd 在 Windows 上 spawn 必需
    for c in repomix.cmd repomix; do
        if command -v "$c" >/dev/null 2>&1; then repo_exe=$(command -v "$c"); break; fi
    done
    [ -z "$repo_exe" ] && [ -f "$HOME/AppData/Roaming/npm/repomix.cmd" ] && \
        repo_exe="$HOME/AppData/Roaming/npm/repomix.cmd"

    # Windows 路径统一转正斜杠（JSON 推荐，且 Python 在 win 上两种都吃）
    jcode_exe=$(echo "$jcode_exe" | sed 's|\\|/|g')
    head_exe=$(echo "$head_exe"  | sed 's|\\|/|g')
    repo_exe=$(echo "$repo_exe"  | sed 's|\\|/|g')

    if [ -z "$jcode_exe" ] || [ -z "$head_exe" ] || [ -z "$repo_exe" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  三个 MCP 工具未全部找到，跳过桌面版配置写入"
        echo -e "  ${YELLOW}⚠${RESET}  手动重装: pip install --user jcodemunch-mcp headroom && npm i -g repomix"
        return 0
    fi

    mkdir -p "$(dirname "$cfg")"

    # Python merge（保留用户其他顶层字段，如 provider/model/自定义设置）
    python - "$cfg" "$jcode_exe" "$head_exe" "$repo_exe" <<'PYEOF'
import json, os, sys
cfg, jcode, head, repo = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = {}
if os.path.isfile(cfg):
    try:
        with open(cfg, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}
data.setdefault('mcp', {}).setdefault('servers', {})
# 桌面版 ZCode 用 type="stdio" + command + args（不是 .mcp.json 的 mcpServers）
data['mcp']['servers']['jcodemunch'] = {'type': 'stdio', 'command': jcode, 'args': ['serve']}
data['mcp']['servers']['repomix']    = {'type': 'stdio', 'command': repo,  'args': ['--mcp']}
data['mcp']['servers']['headroom']   = {'type': 'stdio', 'command': head,  'args': ['mcp', 'serve']}
with open(cfg, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"  ✅ {cfg}")
PYEOF
    if [ -f "$cfg" ]; then
        echo -e "  ${GREEN}✅${RESET} [ZCode 桌面版 MCP] $cfg"
        TARGETS+=("ZCode 桌面版 MCP:$cfg")
    fi
}

echo ""
echo -e "${BOLD}⚙️  Step 4: 配置 ZCode 桌面版 MCP (~/.zcode/cli/config.json)...${RESET}"
write_zcode_desktop_config

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
echo -e "  ${CYAN}\"告诉我 LoopEngine 的核心价值，并列出 skill-hub 调度的 5 类复合任务\"${RESET}"
echo ""

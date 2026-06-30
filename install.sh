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

# ── Step 5: 注入全局用户交互红线规则 ─────────────────────────────
# 把 AGENTS.md 中的"用户交互红线"章节注入到所有 AI 工具的**用户级**规则文件。
# 关键设计：sentinel markers（HTML 注释）+ Python 合并，保证：
#   1. 幂等性 —— 重复执行不重复插入（找到旧块则替换）
#   2. 用户保留 —— 用户在文件其他章节的自定义内容**不会被覆盖**
#   3. 自动更新 —— 项目升级（update.sh → install.sh）时，规则自动同步
#   4. 全局生效 —— 用户级 (~/.xxx/...) 而非项目级，新会话立即生效
install_interaction_rules() {
    local src="$WORK/AGENTS.md"
    [ ! -f "$src" ] && { echo -e "  ${YELLOW}⚠${RESET}  $src 不存在，跳过"; return 0; }

    # 提取"用户交互红线"章节的精确行号范围
    # 注意：使用 awk 而非 grep —— Git Bash Windows 下 grep 处理 `^## 🔴`（4 字节 UTF-8 emoji + ^ 锚点）失败
    local begin_line
    begin_line=$(awk '/^## 🔴 用户交互红线/ { print NR; exit }' "$src")
    if [ -z "$begin_line" ]; then
        echo -e "  ${YELLOW}⚠${RESET}  AGENTS.md 中未找到'用户交互红线'章节，跳过"
        return 0
    fi
    # 下一个 ## 章节开始行号
    local next_section_line
    next_section_line=$(awk -v start="$begin_line" 'NR > start && /^## / { print NR; exit }' "$src")
    local end_line
    if [ -n "$next_section_line" ]; then
        end_line=$((next_section_line - 1))
    else
        end_line=$(wc -l < "$src")
    fi

    # 用 awk 而非 sed 提取行范围（更跨平台、避免 sed 在 Windows 下的转义问题）
    local managed_block
    managed_block=$(awk -v start="$begin_line" -v end="$end_line" 'NR>=start && NR<=end' "$src")
    local wrapped_block
    wrapped_block=$(printf '<!-- BEGIN LOOPENGINE-MANAGED INTERACTION-RULES -->\n%s\n<!-- END LOOPENGINE-MANAGED INTERACTION-RULES -->' "$managed_block")

    # 目标：(标签 | 用户级规则文件路径)
    # 注意：路径是用户级 (~/.xxx/...)，与项目级 (./AGENTS.md) 不同，确保**全局生效**
    local targets=(
        "ZCode|$HOME/.zcode/AGENTS.md"
        "Claude Code|$HOME/.claude/CLAUDE.md"
        "Gemini CLI|$HOME/.gemini/GEMINI.md"
        "Codex|$HOME/.codex/AGENTS.md"
        "Cursor|$HOME/.cursor/rules/loopengine-interaction.mdc"
        "Copilot CLI|$HOME/.copilot/AGENTS.md"
        "Pi|$HOME/.pi/AGENTS.md"
    )

    for entry in "${targets[@]}"; do
        local label="${entry%%|*}"
        local target="${entry##*|}"
        mkdir -p "$(dirname "$target")"

        # Python 合并：找到旧块则替换，否则追加
        python - "$target" "$wrapped_block" <<'PYEOF'
import sys, os, re
target = sys.argv[1]
new_block = sys.argv[2]
begin_marker = "<!-- BEGIN LOOPENGINE-MANAGED INTERACTION-RULES -->"
end_marker = "<!-- END LOOPENGINE-MANAGED INTERACTION-RULES -->"

content = ""
if os.path.isfile(target):
    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

pattern = re.compile(re.escape(begin_marker) + r".*?" + re.escape(end_marker), re.DOTALL)

if pattern.search(content):
    new_content = pattern.sub(new_block, content)
    action = "UPDATED"
else:
    if content and not content.endswith("\n"):
        content += "\n"
    if content and not content.endswith("\n\n"):
        content += "\n"
    new_content = content + new_block + "\n"
    action = "APPENDED"

with open(target, 'w', encoding='utf-8') as f:
    f.write(new_content)
print(f"  {action}")
PYEOF

        echo -e "  ${GREEN}✅${RESET} [$label 交互红线] $target"
        TARGETS+=("$label 交互红线:$target")
    done
}

echo ""
echo -e "${BOLD}🌐 Step 5: 注入全局用户交互红线规则（7 个 AI 工具用户级文件）...${RESET}"
install_interaction_rules

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

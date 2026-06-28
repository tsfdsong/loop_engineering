#!/usr/bin/env bash
# LoopEngine 一键安装/更新脚本
# 自动检测 AI 编程工具并执行对应安装命令
#
# 用法:
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash          # 新安装
#   curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash -s -- --update  # 更新
#   或
#   bash install.sh              # 新安装
#   bash install.sh --update     # 更新已安装的插件

set -euo pipefail

REPO_URL="https://github.com/tsfdsong/loop_engineering"
BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║       LoopEngine — 循环工程全家桶 安装脚本       ║${RESET}"
echo -e "${BOLD}${CYAN}║    loop闭环 + go编排 + skill-hub 53技能调度      ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

# Detect available tools
DETECTED=()

detect_tool() {
    local name="$1"
    local cmd="$2"
    if command -v "$cmd" &> /dev/null || (command -v which &> /dev/null && which "$cmd" &> /dev/null 2>/dev/null); then
        DETECTED+=("$name")
        return 0
    fi
    return 1
}

echo -e "${BOLD}🔍 检测已安装的 AI 编程工具...${RESET}"
echo ""

detect_tool "Claude Code" "claude" && echo -e "  ${GREEN}✅${RESET} Claude Code 已检测到"
detect_tool "Codex" "codex" && echo -e "  ${GREEN}✅${RESET} Codex 已检测到"
detect_tool "Gemini CLI" "gemini" && echo -e "  ${GREEN}✅${RESET} Gemini CLI 已检测到"
detect_tool "GitHub Copilot" "copilot" && echo -e "  ${GREEN}✅${RESET} GitHub Copilot CLI 已检测到"
detect_tool "Pi" "pi" && echo -e "  ${GREEN}✅${RESET} Pi 已检测到"

echo ""

# ── 检查是否为更新模式 ─────────────────────────────────────
IS_UPDATE=false
if [ "${1:-}" = "--update" ] || [ "${1:-}" = "-u" ]; then
    IS_UPDATE=true
    echo -e "${BOLD}🔄 更新模式：将更新已安装的插件到最新版本${RESET}"
    echo ""
fi

if [ ${#DETECTED[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  未检测到已知的 AI 编程工具。${RESET}"
    echo ""
    echo "手动安装方式："
    echo "  git clone $REPO_URL ~/.loopengine"
    echo "  然后参考: $REPO_URL#readme"
    exit 0
fi

if $IS_UPDATE; then
    echo -e "${BOLD}📦 开始更新 LoopEngine...${RESET}"
else
    echo -e "${BOLD}📦 开始安装 LoopEngine...${RESET}"
fi
echo ""

INSTALLED=0
FAILED=0

# ═══════════════════════════════════════════════════════════
# MCP 三件套依赖检查与安装
# ───────────────────────────────────────────────────────────
# jCodeMunch (Python, pip) — 符号级代码检索，省 95% token
# Repomix    (Node.js, npm) — 代码库打包压缩，省 70% token
# Headroom   (Python, pip) — 上下文压缩，省 60-95% token
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}🔌 检查 MCP 三件套依赖...${RESET}"
MCP_INSTALLED=0
MCP_MISSING=()
MCP_PATH_FIXED=false

# 检测平台（用于 PATH 修复）
detect_os() {
    case "$OSTYPE" in
        msys*|cygwin*|mingw*|win32*) echo "windows" ;;
        darwin*)                     echo "macos"   ;;
        linux-gnu*|linux*)           echo "linux"   ;;
        *)                           echo "unknown" ;;
    esac
}
CURRENT_OS=$(detect_os)

# ── Python 用户目录检测（pip install --user 的 Scripts 路径）
detect_python_scripts_dir() {
    if command -v python &> /dev/null; then
        python -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts' if os.name == 'nt' else 'bin'))" 2>/dev/null
    fi
}
PYTHON_SCRIPTS_DIR=$(detect_python_scripts_dir || echo "")

# ── PATH 修复：把 pip --user / npm global 加入 PATH（仅当前会话 + 当前用户的 rc 文件）
fix_python_path() {
    if [ -z "$PYTHON_SCRIPTS_DIR" ] || [ ! -d "$PYTHON_SCRIPTS_DIR" ]; then
        return 1
    fi
    case ":$PATH:" in
        *":$PYTHON_SCRIPTS_DIR:"*) return 0 ;;  # 已在 PATH 中
    esac
    export PATH="$PYTHON_SCRIPTS_DIR:$PATH"
    # 持久化到用户 rc 文件（Linux/macOS）
    if [ "$CURRENT_OS" = "linux" ] || [ "$CURRENT_OS" = "macos" ]; then
        for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
            if [ -f "$rc" ] && ! grep -q "PYTHON_SCRIPTS_DIR" "$rc" 2>/dev/null; then
                echo "" >> "$rc"
                echo "# LoopEngine MCP: Python Scripts in PATH" >> "$rc"
                echo "export PATH=\"$PYTHON_SCRIPTS_DIR:\$PATH\"" >> "$rc"
            fi
        done
    fi
    # Windows: 用 setx 持久化到用户 PATH（提示用户重启 shell 生效）
    if [ "$CURRENT_OS" = "windows" ] && command -v setx &> /dev/null; then
        # 把 POSIX 路径转 Windows 路径
        WIN_PATH=$(echo "$PYTHON_SCRIPTS_DIR" | sed 's|^/\([a-z]\)/|\1:/|')
        CURRENT_USER_PATH=$(reg query "HKCU\Environment" /v PATH 2>/dev/null | grep -oP '(?<=REG_SZ\s+).*' || echo "")
        case ";$CURRENT_USER_PATH;" in
            *";$WIN_PATH;"*) ;;  # 已存在
            *) setx PATH "$WIN_PATH;%PATH%" >/dev/null 2>&1 ;;
        esac
    fi
    MCP_PATH_FIXED=true
    return 0
}

# 检查 Node.js（repomix 与部分 MCP server 的运行依赖）
if ! command -v node &> /dev/null; then
    echo -e "  ${RED}❌${RESET} Node.js 未安装（repomix 运行依赖）"
    MCP_MISSING+=("node")
else
    NODE_VER=$(node -v 2>&1)
    echo -e "  ${GREEN}✅${RESET} Node.js ${NODE_VER}"
fi

# 检查 repomix（Node.js 包，通过 npm 全局安装）
if command -v repomix &> /dev/null || command -v repomix.cmd &> /dev/null; then
    REPOMIX_VER=$(repomix --version 2>/dev/null || echo "已安装")
    echo -e "  ${GREEN}✅${RESET} repomix ${REPOMIX_VER} (代码打包压缩，省 70% token)"
else
    echo -e "  ${YELLOW}⚠️${RESET}  repomix 未安装"
    MCP_MISSING+=("repomix")
fi

# 检查 jcodemunch-mcp（Python 包，通过 pip 安装）
# 注意：实际包名是 jcodemunch-mcp（pip），命令名是 jcodemunch-mcp（exe）
# jcodemunch 是 npm 包名（不存在的别名），不能用 npm 安装
if command -v jcodemunch-mcp &> /dev/null || command -v jcodemunch-mcp.exe &> /dev/null || \
   [ -f "$PYTHON_SCRIPTS_DIR/jcodemunch-mcp.exe" ] || [ -f "$PYTHON_SCRIPTS_DIR/jcodemunch-mcp" ]; then
    JCODE_VER=$(jcodemunch-mcp --version 2>/dev/null || echo "已安装")
    echo -e "  ${GREEN}✅${RESET} jcodemunch-mcp ${JCODE_VER} (符号级代码检索，省 95% token)"
else
    echo -e "  ${YELLOW}⚠️${RESET}  jcodemunch-mcp 未安装（Python pip 包）"
    MCP_MISSING+=("jcodemunch-mcp")
fi

# 检查 headroom（Python 包，通过 pip 安装）
if command -v headroom &> /dev/null || command -v headroom.exe &> /dev/null || \
   [ -f "$PYTHON_SCRIPTS_DIR/headroom.exe" ] || [ -f "$PYTHON_SCRIPTS_DIR/headroom" ]; then
    HEADROOM_VER=$(headroom --version 2>/dev/null || echo "已安装")
    echo -e "  ${GREEN}✅${RESET} headroom ${HEADROOM_VER} (上下文压缩，省 60-95% token)"
else
    echo -e "  ${YELLOW}⚠️${RESET}  headroom 未安装（Python pip 包）"
    MCP_MISSING+=("headroom")
fi

# 检查 MCP server 配置
MCP_CONFIG_EXISTS=false
[ -f "$HOME/.codex/config.toml" ] && MCP_CONFIG_EXISTS=true
[ -f "$HOME/.zcode/config.json" ] && MCP_CONFIG_EXISTS=true
[ -f "$HOME/.zcode/cli/mcp-servers.json" ] && MCP_CONFIG_EXISTS=true
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$SCRIPT_DIR/.mcp.json" ] && MCP_CONFIG_EXISTS=true
if ${MCP_CONFIG_EXISTS}; then
    echo -e "  ${GREEN}✅${RESET} MCP server 配置文件存在"
else
    echo -e "  ${YELLOW}⚠️${RESET}  未找到 MCP server 配置"
    MCP_MISSING+=("mcp-config")
fi

# ── 自动安装缺失的 MCP 依赖 ─────────────────────────────────
if [ ${#MCP_MISSING[@]} -gt 0 ]; then
    echo ""
    echo -e "${CYAN}▶  自动安装 MCP 三件套依赖...${RESET}"

    # 在执行安装前先尝试修复 PATH（避免 pip --user 安装后命令找不到）
    fix_python_path || true

    for dep in "${MCP_MISSING[@]}"; do
        case "$dep" in
            node)
                echo -e "  ${RED}⏭${RESET}  跳过: 请手动安装 Node.js https://nodejs.org/"
                ;;
            repomix)
                # repomix 是 Node.js 包，用 npm 全局安装
                if command -v npm &> /dev/null; then
                    echo -e "  📦 npm install -g repomix ..."
                    if npm install -g repomix 2>&1 | tail -5; then
                        echo -e "  ${GREEN}✅${RESET} repomix 安装成功"
                        ((MCP_INSTALLED++)) || true
                    else
                        echo -e "  ${RED}❌${RESET} repomix 安装失败"
                    fi
                else
                    echo -e "  ${YELLOW}⚠️${RESET}  npm 未安装，跳过 repomix（需先安装 Node.js）"
                fi
                ;;
            jcodemunch-mcp)
                # jcodemunch-mcp 是 Python 包，用 pip 安装
                if command -v pip &> /dev/null || command -v pip3 &> /dev/null || command -v python &> /dev/null; then
                    echo -e "  📦 pip install --upgrade jcodemunch-mcp ..."
                    PIP_CMD=$(command -v pip || command -v pip3 || echo "python -m pip")
                    if $PIP_CMD install --upgrade jcodemunch-mcp 2>&1 | tail -5; then
                        echo -e "  ${GREEN}✅${RESET} jcodemunch-mcp 安装成功"
                        ((MCP_INSTALLED++)) || true
                        # 重新检测 Python Scripts（pip 可能写到 --user 目录）
                        PYTHON_SCRIPTS_DIR=$(detect_python_scripts_dir || echo "")
                        fix_python_path || true
                    else
                        echo -e "  ${RED}❌${RESET} jcodemunch-mcp 安装失败"
                    fi
                else
                    echo -e "  ${YELLOW}⚠️${RESET}  pip 未安装，跳过 jcodemunch-mcp（需先安装 Python）"
                fi
                ;;
            headroom)
                # headroom 是 Python 包，用 pip 安装
                if command -v pip &> /dev/null || command -v pip3 &> /dev/null || command -v python &> /dev/null; then
                    echo -e "  📦 pip install --upgrade headroom-ai ..."
                    PIP_CMD=$(command -v pip || command -v pip3 || echo "python -m pip")
                    if $PIP_CMD install --upgrade headroom-ai 2>&1 | tail -5; then
                        echo -e "  ${GREEN}✅${RESET} headroom-ai 安装成功"
                        ((MCP_INSTALLED++)) || true
                        PYTHON_SCRIPTS_DIR=$(detect_python_scripts_dir || echo "")
                        fix_python_path || true
                    else
                        echo -e "  ${RED}❌${RESET} headroom-ai 安装失败"
                    fi
                else
                    echo -e "  ${YELLOW}⚠️${RESET}  pip 未安装，跳过 headroom（需先安装 Python）"
                fi
                ;;
            mcp-config)
                # 写入项目根 .mcp.json（LoopEngine 推荐方式）
                if [ -f "$SCRIPT_DIR/.mcp.json" ]; then
                    echo -e "  ${GREEN}✅${RESET} 项目根 .mcp.json 已存在"
                else
                    cat > "$SCRIPT_DIR/.mcp.json" <<'MCPEOF'
{
  "mcpServers": {
    "jcodemunch": {
      "command": "jcodemunch-mcp",
      "args": ["serve"],
      "cwd": "${workspaceFolder}"
    },
    "repomix": {
      "command": "repomix",
      "args": ["--mcp"],
      "cwd": "${workspaceFolder}"
    },
    "headroom": {
      "command": "headroom",
      "args": ["mcp", "serve"],
      "cwd": "${workspaceFolder}"
    }
  }
}
MCPEOF
                    echo -e "  ${GREEN}✅${RESET} 项目根 .mcp.json 已生成: $SCRIPT_DIR/.mcp.json"
                    ((MCP_INSTALLED++)) || true
                fi
                # 同时写一份到 ZCode CLI 缓存（兼容老版本）
                ZCODE_CLI_DIR="$HOME/.zcode/cli"
                mkdir -p "$ZCODE_CLI_DIR"
                if [ ! -f "$ZCODE_CLI_DIR/mcp-servers.json" ]; then
                    cat > "$ZCODE_CLI_DIR/mcp-servers.json" <<'MCPEOF'
{
  "mcpServers": {
    "jcodemunch": {"command": "jcodemunch-mcp", "args": ["serve"]},
    "repomix":    {"command": "repomix",         "args": ["--mcp"]},
    "headroom":   {"command": "headroom",        "args": ["mcp", "serve"]}
  }
}
MCPEOF
                    echo -e "  ${GREEN}✅${RESET} ZCode CLI 缓存 mcp-servers.json 已生成"
                fi
                ;;
        esac
    done
    if [ $MCP_INSTALLED -gt 0 ]; then
        echo -e "  ${GREEN}✅${RESET} 自动安装了 ${MCP_INSTALLED} 个 MCP 三件套依赖"
    fi
    if ${MCP_PATH_FIXED}; then
        echo -e "  ${CYAN}ℹ️${RESET}  Python Scripts 已加入 PATH，新开终端生效"
    fi
fi
echo ""

# ═══════════════════════════════════════════════════════════
# ZCode 桌面版完整同步（包含 marketplace 注册 + 端到端测试）
# ═══════════════════════════════════════════════════════════
ZCODE_PKG=""
if [ -d "$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
    ZCODE_PKG="$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin"
elif [ -d "$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
    ZCODE_PKG="$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin"
fi
ZCODE_CACHE_BASE="$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
# 从本地 plugin.json 读版本号（不依赖 GitHub 网络）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.claude-plugin/plugin.json" ]; then
    ZCODE_VERSION=$(grep '"version"' "$SCRIPT_DIR/.claude-plugin/plugin.json" | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
fi
[ -z "$ZCODE_VERSION" ] && ZCODE_VERSION="1.0.1"
ZCODE_CACHE_DIR="$ZCODE_CACHE_BASE/$ZCODE_VERSION"

if [ -n "$ZCODE_PKG" ] || [ -d "$ZCODE_CACHE_DIR" ]; then
    echo -e "${CYAN}▶  同步到 ZCode 桌面版...${RESET}"

    # Step 1: 更新内置包目录
    if [ -n "$ZCODE_PKG" ] && [ -d "$ZCODE_PKG" ]; then
        echo -e "  📦 更新内置包目录..."
        if command -v git &> /dev/null && [ -d "$ZCODE_PKG/.git" ]; then
            (cd "$ZCODE_PKG" && git pull 2>/dev/null) && \
                echo -e "  ${GREEN}✅${RESET} 内置包目录已更新 (git pull)" || \
                echo -e "  ${YELLOW}⚠️${RESET} git pull 失败，将以 cp 同步"
        else
            echo -e "  ${YELLOW}ℹ️${RESET}  内置包不是 git 仓库，将以 cp 同步"
        fi
    fi

    # Step 2: 完整同步到 CLI 缓存（项目源 → cache 1.x.y）
    echo -e "  🔄 完整同步项目到 CLI 缓存 v${ZCODE_VERSION}..."
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    mkdir -p "$ZCODE_CACHE_DIR"
    # 先清空旧 cache 避免残留文件
    rm -rf "$ZCODE_CACHE_DIR"/* 2>/dev/null
    if command -v rsync &> /dev/null; then
        rsync -a \
            --exclude='.git' --exclude='.idea' --exclude='.opencode' \
            --exclude='hooks' --exclude='.claude-plugin' \
            --exclude='.cursor-plugin' --exclude='.codex-plugin' \
            --exclude='.kimi-plugin' --exclude='.pi' --exclude='.zcode-plugin' \
            --exclude='test-page' --exclude='.go' \
            "$SCRIPT_DIR/" "$ZCODE_CACHE_DIR/" 2>/dev/null && \
            echo -e "  ${GREEN}✅${RESET} CLI 缓存已同步 (rsync)" || \
            echo -e "  ${YELLOW}⚠️${RESET} rsync 失败，回退 tar"
    fi
    # 回退方案：用 tar 排除 .git 等运行时目录（避免 cp 复制 .git 时权限问题）
    if [ ! -d "$ZCODE_CACHE_DIR/skills" ] && command -v tar &> /dev/null; then
        (cd "$SCRIPT_DIR" && tar --exclude='.git' --exclude='.idea' --exclude='.opencode' \
            --exclude='hooks' --exclude='.claude-plugin' \
            --exclude='.cursor-plugin' --exclude='.codex-plugin' \
            --exclude='.kimi-plugin' --exclude='.pi' --exclude='.zcode-plugin' \
            --exclude='test-page' --exclude='.go' \
            -cf - .) | tar -xf - -C "$ZCODE_CACHE_DIR/" 2>/dev/null && \
            echo -e "  ${GREEN}✅${RESET} CLI 缓存已同步 (tar)" || \
            echo -e "  ${YELLOW}⚠️${RESET} tar 同步失败"
    fi

    # Step 3: 验证技能数量（端到端测试 1：技能完整性）
    SKILL_COUNT=$(ls -1 "$ZCODE_CACHE_DIR/skills/" 2>/dev/null | wc -l)
    echo -e "  📊 技能数量: ${GREEN}${SKILL_COUNT}${RESET}"

    # Step 4: 验证关键技能存在（端到端测试 2：关键技能可达）
    MISSING_SKILLS=()
    for critical in "skill-hub" "go" "loop" "system-review" "using-loopengine"; do
        if [ ! -d "$ZCODE_CACHE_DIR/skills/$critical" ]; then
            MISSING_SKILLS+=("$critical")
        fi
    done
    if [ ${#MISSING_SKILLS[@]} -eq 0 ]; then
        echo -e "  ${GREEN}✅${RESET} 关键技能全部存在 (skill-hub/go/loop/system-review/using-loopengine)"
    else
        echo -e "  ${RED}❌${RESET} 缺失关键技能: ${MISSING_SKILLS[*]}"
    fi

    # Step 5: 验证 SKILL.md 格式（端到端测试 3：可被 Skill 工具加载）
    INVALID_SKILLS=()
    for skill_dir in "$ZCODE_CACHE_DIR/skills/"*/; do
        if [ ! -f "$skill_dir/SKILL.md" ]; then
            INVALID_SKILLS+=("$(basename "$skill_dir")")
        fi
    done
    if [ ${#INVALID_SKILLS[@]} -eq 0 ]; then
        echo -e "  ${GREEN}✅${RESET} 所有技能 SKILL.md 格式有效"
    else
        echo -e "  ${RED}❌${RESET} 无效技能: ${INVALID_SKILLS[*]}"
    fi

    # Step 6: 自动注册到 zcode-plugins-official marketplace
    ZCODE_MARKET="$HOME/.zcode/cli/plugins/marketplaces/zcode-plugins-official/marketplace.json"
    # 把 mingw 路径 /c/Users/... 转成 Python 可识别的 C:/Users/...
    ZCODE_MARKET_PY=$(echo "$ZCODE_MARKET" | sed 's|^/\([a-z]\)/|\1:/|')
    ZCODE_CACHE_DIR_PY=$(echo "$ZCODE_CACHE_DIR" | sed 's|^/\([a-z]\)/|\1:/|')
    if [ -f "$ZCODE_MARKET" ] && command -v python &> /dev/null; then
        echo -e "  📝 检查 marketplace 注册..."
        if ! grep -q '"name": "loopengine"' "$ZCODE_MARKET" 2>/dev/null; then
            python -c "
import json, os, sys
path = r'$ZCODE_MARKET_PY'
cache_path = r'$ZCODE_CACHE_DIR_PY'
try:
    with open(path, 'r') as f:
        data = json.load(f)
    already = any(p.get('name') == 'loopengine' for p in data.get('plugins', []))
    if not already:
        data['plugins'].append({
            'cachePath': cache_path,
            'name': 'loopengine',
            'source': 'filesystem',
            'version': r'$ZCODE_VERSION'
        })
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print('  ${GREEN}✅${RESET} loopengine 已注册到 marketplace')
    else:
        print('  ${GREEN}✅${RESET} loopengine 已在 marketplace')
except Exception as e:
    print(f'  ${YELLOW}⚠️${RESET}  marketplace 注册失败: {e}', file=sys.stderr)
" 2>&1
        else
            echo -e "  ${GREEN}✅${RESET} loopengine 已在 marketplace"
        fi
    fi

    # Step 7: 确保 enabledPlugins 中启用 loopengine
    ZCODE_CFG="$HOME/.zcode/cli/config.json"
    # 把 mingw 路径 /c/Users/... 转成 Python 可识别的 C:/Users/...
    ZCODE_CFG_PY=$(echo "$ZCODE_CFG" | sed 's|^/\([a-z]\)/|\1:/|')
    if [ -f "$ZCODE_CFG" ] && command -v python &> /dev/null; then
        python -c "
import json
path = r'$ZCODE_CFG_PY'
try:
    with open(path, 'r') as f:
        cfg = json.load(f)
    cfg.setdefault('enabledPlugins', {})['loopengine@zcode-plugins-official'] = True
    with open(path, 'w') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print('  ${GREEN}✅${RESET} enabledPlugins 已确认 loopengine=true')
except Exception as e:
    print(f'  ${YELLOW}⚠️${RESET}  enabledPlugins 更新失败: {e}')
" 2>&1
    fi

    # Step 8: 确保 data 目录存在
    ZCODE_DATA_DIR="$HOME/.zcode/cli/plugins/data/loopengine@zcode-plugins-official"
    if [ ! -d "$ZCODE_DATA_DIR" ]; then
        mkdir -p "$ZCODE_DATA_DIR"
        echo -e "  📁 data 目录已创建"
    fi

    # Step 9: 调用 MCP 自愈脚本（保证 ZCode 重启后 MCP 不丢失）
    # 根因：ZCode 启动时会重写 marketplace.json 并优先从 CLI 缓存 plugin.json 加载 MCP
    #       如果 plugin.json 没有 mcpServers 字段 → MCP 工具不显示
    ENSURE_SCRIPT="$SCRIPT_DIR/scripts/zcode-mcp-ensure.sh"
    if [ -f "$ENSURE_SCRIPT" ]; then
        echo -e "  ${CYAN}▶  MCP 自愈（修复 plugin.json mcpServers 绝对路径 + marketplace 注册）...${RESET}"
        if bash "$ENSURE_SCRIPT" --quiet; then
            echo -e "  ${GREEN}✅${RESET} MCP 自愈完成"
        else
            echo -e "  ${YELLOW}⚠️${RESET}  MCP 自愈未完全通过，可手动执行: bash $ENSURE_SCRIPT"
        fi
    else
        echo -e "  ${YELLOW}ℹ️${RESET}  未找到 scripts/zcode-mcp-ensure.sh，跳过 MCP 自愈"
    fi

    echo -e "  ${GREEN}✅${RESET} ZCode 桌面版同步完成"
    echo -e "  ${YELLOW}⚠️${RESET} 请重启 ZCode 桌面版使更新生效"
    echo -e "  ${YELLOW}💡${RESET}  重启后若 MCP 工具仍消失，跑: bash $SCRIPT_DIR/scripts/zcode-mcp-ensure.sh"
    ((INSTALLED++)) || true
    echo ""
fi

# ── Claude Code ──────────────────────────────────────────
# 验证通过的流程: marketplace add → plugin install
if echo "${DETECTED[@]}" | grep -q "Claude Code"; then
    echo -e "${CYAN}▶  安装到 Claude Code...${RESET}"
    
    # Step 1: 添加 marketplace（支持 GitHub URL 和本地路径）
    if claude plugin marketplace add "$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} marketplace 已添加"
    else
        # GitHub 不可用时尝试本地路径
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        if [ -f "$SCRIPT_DIR/.claude-plugin/marketplace.json" ]; then
            claude plugin marketplace add "$SCRIPT_DIR" 2>/dev/null && \
                echo -e "  ${GREEN}✅${RESET} marketplace 已添加（本地路径）" || \
                echo -e "  ${YELLOW}⚠️${RESET} marketplace 添加失败"
        fi
    fi
    
    # Step 2: 安装插件
    if claude plugin install loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Claude Code 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行:"
        echo -e "    claude plugin marketplace add $REPO_URL"
        echo -e "    claude plugin install loopengine"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── Codex ────────────────────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "Codex"; then
    echo -e "${CYAN}▶  安装到 Codex...${RESET}"
    if codex plugin install "$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Codex 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请在 Codex 插件市场中搜索 'loopengine' 安装"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── Gemini CLI ───────────────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "Gemini CLI"; then
    echo -e "${CYAN}▶  安装到 Gemini CLI...${RESET}"
    if gemini extensions install "$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Gemini CLI 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行: gemini extensions install $REPO_URL"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── GitHub Copilot CLI ───────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "GitHub Copilot"; then
    echo -e "${CYAN}▶  安装到 GitHub Copilot CLI...${RESET}"
    # Copilot 使用 marketplace 机制，类似 Claude Code
    if copilot plugin marketplace add "$REPO_URL" 2>/dev/null && \
       copilot plugin install loopengine 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} GitHub Copilot CLI 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行: copilot plugin install loopengine@tsfdsong"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── Pi ───────────────────────────────────────────────────
if echo "${DETECTED[@]}" | grep -q "Pi"; then
    echo -e "${CYAN}▶  安装到 Pi...${RESET}"
    if pi install "git:$REPO_URL" 2>/dev/null; then
        echo -e "  ${GREEN}✅${RESET} Pi 安装完成"
        ((INSTALLED++)) || true
    else
        echo -e "  ${YELLOW}⚠️${RESET}  请手动执行: pi install git:$REPO_URL"
        ((FAILED++)) || true
    fi
    echo ""
fi

# ── 手动引导平台（首次安装） ─────────────────────────────
if ! $IS_UPDATE; then
echo -e "${CYAN}▶  Cursor IDE${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  在 Cursor 中执行: /add-plugin tsfdsong/loop_engineering"
echo ""

echo -e "${CYAN}▶  ZCode 桌面版 (手动安装)${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  ZCode 桌面版 v3.1.8+ 需手动安装到内置包目录:"
echo ""
echo -e "  ${BOLD}PowerShell (管理员)${RESET}:"
echo -e "  git clone $REPO_URL \"\$env:LOCALAPPDATA\\Programs\\ZCode\\resources\\glm\\packages\\loopengine-plugin\""
echo -e "  mkdir -p \"\$env:USERPROFILE\\.zcode\\cli\\plugins\\cache\\zcode-plugins-official\\loopengine\\1.0.1\""
echo -e "  xcopy \"\$env:LOCALAPPDATA\\Programs\\ZCode\\resources\\glm\\packages\\loopengine-plugin\\*\" \"\$env:USERPROFILE\\.zcode\\cli\\plugins\\cache\\zcode-plugins-official\\loopengine\\1.0.1\\\" /E /I /Y"
echo -e "  mkdir \"\$env:USERPROFILE\\.zcode\\cli\\plugins\\data\\loopengine@zcode-plugins-official\""
echo ""
echo -e "  ${BOLD}然后编辑两个配置文件${RESET}:"
echo -e "  1. marketplace.json: 在 zcode-plugins-official 市场中添加 loopengine 条目"
echo -e "  2. config.json: 在 enabledPlugins 中添加 \"loopengine@zcode-plugins-official\": true"
echo -e "  ${BOLD}重启 ZCode 桌面版${RESET}"
echo -e "  详见: $REPO_URL/blob/main/docs/zcode-install-guide.md"
echo ""

echo -e "${CYAN}▶  OpenCode${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  在 opencode.json 的 plugin 数组中添加:"
echo -e "  ${YELLOW}ℹ️${RESET}  \"loopengine@git+$REPO_URL.git\""
echo ""

echo -e "${CYAN}▶  Kimi Code${RESET}"
echo -e "  ${YELLOW}ℹ️${RESET}  执行: /plugins install $REPO_URL"
echo ""
fi

# ── 总结 ─────────────────────────────────────────────────
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
if $IS_UPDATE; then
    echo -e "${BOLD}📊 更新总结${RESET}"
else
    echo -e "${BOLD}📊 安装总结${RESET}"
fi
echo -e "  自动安装: ${GREEN}$INSTALLED${RESET} 个平台成功"
if [ $FAILED -gt 0 ]; then
    echo -e "  需手动安装: ${YELLOW}$FAILED${RESET} 个平台"
fi
echo ""

if $IS_UPDATE; then
    echo -e "${BOLD}🎉 LoopEngine 更新完成！${RESET}"
    echo ""
    echo -e "${BOLD}📋 本次更新内容${RESET}:"
    echo -e "  🔴 ${BOLD}新增 MCP 红线规则${RESET} — 任何理解代码的操作必须先用 MCP 工具"
    echo -e "  📝 适用范围从\"修改代码前\"扩展为\"所有理解代码的操作\""
    echo -e "  ⚡ 标准流程: get_repo_map → get_file_outline → search_symbols → Read(仅精确行)"
    echo -e "  🚨 违规判定: 连续 3 次直接 Read 全文件未用 MCP = 红线事故"
    echo ""
    echo -e "${YELLOW}⚠️  重要提醒${RESET}:"
    echo -e "  • ZCode 桌面版用户: 请${BOLD}重启${RESET} ZCode 使更新生效"
    echo -e "  • 其他平台: 新会话自动生效"
else
    echo -e "${BOLD}🎉 LoopEngine 安装完成！${RESET}"
fi
echo ""
echo -e "  验证安装: 打开新的 AI 会话，发送:"
echo -e "  ${CYAN}\"Tell me about LoopEngine\"${RESET}"
echo -e "  或直接使用:"
echo -e "  ${CYAN}\"/loop 帮我实现一个功能\"${RESET}"
echo -e "  ${CYAN}\"/go 全自动开发一个项目\"${RESET}"
echo ""

#!/usr/bin/env bash
# LoopEngine ZCode MCP 自愈脚本 v1.1
# ────────────────────────────────────────────────────────────
# 用途：保证 ZCode 桌面版重启后 MCP 三件套（jcodemunch/repomix/headroom）不丢失
#
# 根因（2026-06-30 实测发现 — v1.1 更新）：
#   ZCode 桌面版 MCP 的真正入口不是 plugin.json，也不是 marketplace.json，
#   而是用户级配置文件：
#       ~/.zcode/cli/config.json       （结构：mcp.servers.<name>）
#   手动在桌面 UI 配置三次才成功，就是反复试错这个文件的位置和 schema。
#   install.sh 不写它，桌面版就找不到 MCP。
#
# 本脚本做的事（5 步）：
#   1. 探测 jcodemunch-mcp / headroom / repomix 三个可执行文件绝对路径
#   2. 写入 ~/.zcode/cli/config.json 的 mcp.servers（桌面版真正入口）【v1.1 新增】
#   3. 兼容写入 plugin.json 缓存位置（v1.0 旧路径，部分版本仍读）
#   4. 兼容写入 marketplace.json（部分版本仍依赖）
#   5. stdIO 握手验证三个 server
#
# 用法：
#   bash scripts/zcode-mcp-ensure.sh
#   bash scripts/zcode-mcp-ensure.sh --quiet   # 静默模式（仅输出错误）
#
# 由 install.sh / update.sh 自动调用，也可手动运行
# ────────────────────────────────────────────────────────────

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

QUIET=false
[ "${1:-}" = "--quiet" ] && QUIET=true

log()  { $QUIET || echo -e "$@"; }
ok()   { log "${GREEN}✅${RESET} $1"; }
warn() { log "${YELLOW}⚠️ ${RESET} $1"; }
err()  { log "${RED}❌${RESET} $1"; }
info() { log "${CYAN}ℹ️ ${RESET} $1"; }

log ""
log "${BOLD}${CYAN}═══ LoopEngine ZCode MCP 自愈脚本 v1.1 ═══${RESET}"
log ""

# ── Step 1: 探测三个 MCP 工具的绝对路径 ──
log "${BOLD}🔍 Step 1: 探测 MCP 工具可执行文件...${RESET}"

# 探测函数：在 PATH / Python Scripts / npm 全局目录中查找
detect_exe() {
    local name="$1"
    local found=""
    # 1) PATH 优先
    if command -v "$name" &>/dev/null; then
        found=$(command -v "$name")
        echo "$found"
        return 0
    fi
    # 2) Python Scripts (Windows: %APPDATA%\Python\Python3xx\Scripts)
    if [ -n "${PYTHON_SCRIPTS_DIR:-}" ] && [ -f "${PYTHON_SCRIPTS_DIR}/${name}.exe" ]; then
        echo "${PYTHON_SCRIPTS_DIR}/${name}.exe"
        return 0
    fi
    # 3) Windows 用户级 Python Scripts 默认路径
    local py_scripts="$HOME/AppData/Roaming/Python/Python314/Scripts"
    if [ -f "${py_scripts}/${name}.exe" ]; then
        echo "${py_scripts}/${name}.exe"
        return 0
    fi
    # 4) npm 全局 (Windows: %APPDATA%\npm)
    if [ -f "$HOME/AppData/Roaming/npm/${name}.cmd" ]; then
        echo "$HOME/AppData/Roaming/npm/${name}.cmd"
        return 0
    fi
    if [ -f "$HOME/AppData/Roaming/npm/${name}" ]; then
        echo "$HOME/AppData/Roaming/npm/${name}"
        return 0
    fi
    return 1
}

PYTHON_SCRIPTS_DIR=""
# 尝试从 pip user site 推导
if command -v python &>/dev/null; then
    PY_USER_BASE=$(python -c "import site; print(site.getuserbase())" 2>/dev/null || echo "")
    if [ -n "$PY_USER_BASE" ] && [ -d "${PY_USER_BASE}/Scripts" ]; then
        PYTHON_SCRIPTS_DIR="${PY_USER_BASE}/Scripts"
    fi
fi

JCODE_EXE=$(detect_exe "jcodemunch-mcp" || echo "")
HEAD_EXE=$(detect_exe "headroom" || echo "")
REPO_EXE=$(detect_exe "repomix" || echo "")

if [ -n "$JCODE_EXE" ]; then
    ok "jcodemunch-mcp → $JCODE_EXE"
else
    err "jcodemunch-mcp 未找到（pip install --user jcodemunch-mcp）"
fi
if [ -n "$HEAD_EXE" ]; then
    ok "headroom       → $HEAD_EXE"
else
    err "headroom 未找到（pip install --user headroom-ai）"
fi
if [ -n "$REPO_EXE" ]; then
    ok "repomix        → $REPO_EXE"
else
    err "repomix 未找到（npm install -g repomix）"
fi

# 任何一个缺失就中止（避免写入残缺配置）
if [ -z "$JCODE_EXE" ] || [ -z "$HEAD_EXE" ] || [ -z "$REPO_EXE" ]; then
    err "三个 MCP 工具必须全部可用，跳过插件配置修复"
    err "请先运行 install.sh 安装依赖，或手动安装后重试"
    exit 1
fi

# 把路径统一转成正斜杠（Windows JSON 推荐）
JCODE_EXE_FWD=$(echo "$JCODE_EXE" | sed 's|\\|/|g')
HEAD_EXE_FWD=$(echo "$HEAD_EXE" | sed 's|\\|/|g')
REPO_EXE_FWD=$(echo "$REPO_EXE" | sed 's|\\|/|g')
log ""

# ── Step 2: 注入 mcpServers 到所有 loopengine plugin.json 缓存位置 ──
log "${BOLD}🔧 Step 2: 注入 mcpServers 到 loopengine 缓存...${RESET}"

# 找到所有 loopengine 的 plugin.json 缓存位置
PLUGIN_JSONS=()

# 1) zcode-plugins-official 市场下的所有版本
ZCACHE_OFFICIAL="$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine"
if [ -d "$ZCACHE_OFFICIAL" ]; then
    for ver_dir in "$ZCACHE_OFFICIAL"/*/; do
        [ -d "$ver_dir" ] || continue
        for pj in "$ver_dir/.zcode-plugin/plugin.json" "$ver_dir/plugin.json"; do
            [ -f "$pj" ] && PLUGIN_JSONS+=("$pj")
        done
    done
fi

# 2) loopengine-local 市场下的所有版本
ZCACHE_LOCAL="$HOME/.zcode/cli/plugins/cache/loopengine-local/loopengine"
if [ -d "$ZCACHE_LOCAL" ]; then
    for ver_dir in "$ZCACHE_LOCAL"/*/; do
        [ -d "$ver_dir" ] || continue
        for pj in "$ver_dir/.zcode-plugin/plugin.json" "$ver_dir/plugin.json"; do
            [ -f "$pj" ] && PLUGIN_JSONS+=("$pj")
        done
    done
fi

# 3) ZCode 桌面版内置包目录（保证源也是好的）
if [ -n "${LOCALAPPDATA:-}" ] && [ -d "$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
    ZCODE_PKG="$LOCALAPPDATA/Programs/ZCode/resources/glm/packages/loopengine-plugin"
    for pj in "$ZCODE_PKG/.zcode-plugin/plugin.json" "$ZCODE_PKG/package.json"; do
        [ -f "$pj" ] && PLUGIN_JSONS+=("$pj")
    done
elif [ -d "$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin" ]; then
    ZCODE_PKG="$HOME/AppData/Local/Programs/ZCode/resources/glm/packages/loopengine-plugin"
    for pj in "$ZCODE_PKG/.zcode-plugin/plugin.json" "$ZCODE_PKG/package.json"; do
        [ -f "$pj" ] && PLUGIN_JSONS+=("$pj")
    done
fi

# 4) 当前项目源（开发时使用）
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
for pj in "$SCRIPT_DIR/.zcode-plugin/plugin.json" "$SCRIPT_DIR/.mcp.json"; do
    [ -f "$pj" ] && PLUGIN_JSONS+=("$pj")
done

if [ ${#PLUGIN_JSONS[@]} -eq 0 ]; then
    err "未找到任何 loopengine plugin.json，请先安装 LoopEngine"
    exit 1
fi

# 注入函数（用 Python 改 JSON，保留中文字段）
inject_mcp_servers() {
    local pj="$1"
    local pj_py=$(echo "$pj" | sed 's|^/\([a-z]\)/|\1:/|; s|/|\\|g')
    python - "$pj_py" "$JCODE_EXE_FWD" "$HEAD_EXE_FWD" "$REPO_EXE_FWD" <<'PYEOF' 2>&1
import json, sys, os
pj, jcode, head, repo = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
if not os.path.isfile(pj):
    print(f"  [skip] {pj}: 不存在"); sys.exit(0)
try:
    with open(pj, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"  [error] {pj}: JSON 解析失败 {e}"); sys.exit(1)

# 项目根 .mcp.json 与 plugin.json 结构不同，分开处理
if pj.endswith('.mcp.json'):
    data['mcpServers'] = {
        'jcodemunch': {'command': jcode, 'args': ['serve']},
        'repomix':    {'command': repo,  'args': ['--mcp']},
        'headroom':   {'command': head,  'args': ['mcp', 'serve']}
    }
else:
    data['mcpServers'] = {
        'jcodemunch': {'command': jcode, 'args': ['serve']},
        'repomix':    {'command': repo,  'args': ['--mcp']},
        'headroom':   {'command': head,  'args': ['mcp', 'serve']}
    }

with open(pj, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"  [ok] {pj}")
PYEOF
}

INJECTED=0
for pj in "${PLUGIN_JSONS[@]}"; do
    if inject_mcp_servers "$pj"; then
        INJECTED=$((INJECTED + 1))
    fi
done
ok "已注入 mcpServers 到 ${INJECTED} 个 plugin.json 缓存"
log ""

# ── Step 3: 在 marketplace.json 中加回 loopengine 注册 ──
log "${BOLD}📝 Step 3: 注册 loopengine 到 marketplace...${RESET}"

MARKETPLACES=(
    "$HOME/.zcode/cli/plugins/marketplaces/zcode-plugins-official/marketplace.json"
    "$HOME/.zcode/cli/plugins/marketplaces/loopengine-local/marketplace.json"
)

# 从 plugin.json 读版本号
PLUGIN_VERSION=$(grep -m1 '"version"' "${PLUGIN_JSONS[0]}" 2>/dev/null | sed 's/.*"\([0-9.]*\)".*/\1/' || echo "1.0.1")
[ -z "$PLUGIN_VERSION" ] && PLUGIN_VERSION="1.0.1"
log "  插件版本: ${PLUGIN_VERSION}"

register_to_marketplace() {
    local mp="$1"
    local ver="$2"
    [ -f "$mp" ] || return 0
    local mp_py=$(echo "$mp" | sed 's|^/\([a-z]\)/|\1:/|; s|/|\\|g')
    python - "$mp_py" "$ver" <<'PYEOF' 2>&1
import json, sys, os
mp, ver = sys.argv[1], sys.argv[2]
if not os.path.isfile(mp):
    print(f"  [skip] {mp}: 不存在"); sys.exit(0)
try:
    with open(mp, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"  [error] {mp}: 解析失败 {e}"); sys.exit(1)

# 已经注册？
if any(p.get('name') == 'loopengine' for p in data.get('plugins', [])):
    print(f"  [exists] {mp}"); sys.exit(0)

# 推断 cachePath
mkt = data.get('name', '')
if 'local' in mkt:
    cache_path = f"C:\\\\Users\\\\{os.environ.get('USERNAME', 'admin')}\\\\.zcode\\\\cli\\\\plugins\\\\cache\\\\loopengine-local\\\\loopengine\\\\{ver}"
else:
    cache_path = f"C:\\\\Users\\\\{os.environ.get('USERNAME', 'admin')}\\\\.zcode\\\\cli\\\\plugins\\\\cache\\\\zcode-plugins-official\\\\loopengine\\\\{ver}"

data.setdefault('plugins', []).append({
    'cachePath': cache_path,
    'name': 'loopengine',
    'source': 'filesystem',
    'version': ver
})
with open(mp, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"  [registered] {mp}")
PYEOF
}

for mp in "${MARKETPLACES[@]}"; do
    register_to_marketplace "$mp" "$PLUGIN_VERSION"
done
ok "marketplace 注册完成"
log ""

# ── Step 4: 写入 ZCode 桌面版真正配置 ~/.zcode/cli/config.json（v1.1 核心） ──
# 这是桌面版 MCP 的真正入口！手动 UI 配置也是写到这里。
log "${BOLD}📝 Step 4: 写入 ZCode 桌面版 MCP 真正入口 (~/.zcode/cli/config.json)...${RESET}"
ZCODE_CFG="$HOME/.zcode/cli/config.json"
mkdir -p "$(dirname "$ZCODE_CFG")"

# Windows 路径 → Python 路径（/c/Users → C:/Users，避免 Python 解析混乱）
to_py_path() {
    echo "$1" | sed 's|^/\([a-z]\)/|\1:/|'
}
ZCODE_CFG_PY=$(to_py_path "$ZCODE_CFG")

python - "$ZCODE_CFG_PY" "$JCODE_EXE_FWD" "$HEAD_EXE_FWD" "$REPO_EXE_FWD" <<'PYEOF'
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
ok "已写: $ZCODE_CFG"
log ""

# 同时保留旧 mcp-servers.json 作为向下兼容（部分 ZCode 版本会读）
ZCODE_MCP="$HOME/.zcode/cli/mcp-servers.json"
cat > "$ZCODE_MCP" <<EOF
{
  "mcpServers": {
    "jcodemunch": {"command": "$JCODE_EXE_FWD", "args": ["serve"]},
    "repomix":    {"command": "$REPO_EXE_FWD",  "args": ["--mcp"]},
    "headroom":   {"command": "$HEAD_EXE_FWD",  "args": ["mcp", "serve"]}
  }
}
EOF
info "兼容文件 (老版本): $ZCODE_MCP"
log ""

# ── Step 5: 验证三个 MCP 工具 stdio 握手 ──
log "${BOLD}🧪 Step 5: 验证 MCP 三件套 stdio 握手...${RESET}"
PASS=0
FAIL=0

verify_mcp() {
    local name="$1"
    local cmd="$2"
    local args="$3"
    # 发送 JSON-RPC initialize 请求；任何合法 JSON-RPC 响应（成功或参数错误）都证明 stdio 通了
    local out
    out=$(echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"verify","version":"1.0"}},"id":1}' \
          | timeout 5 "$cmd" $args 2>/dev/null | head -c 1000 || true)
    # 判定：含 jsonrpc 字段（顶层或 result 内部），或含 serverInfo（MCP 协议标识）
    if echo "$out" | grep -qE '"jsonrpc"|"serverInfo".*"mcp-server"|"serverInfo".*"MCP Server"'; then
        # 提取 serverInfo.name 作为成功标志
        local srv=$(echo "$out" | grep -oE '"serverInfo"[^}]*"name":"[^"]*"' | head -1 | sed 's/.*"name":"\([^"]*\)".*/\1/')
        if [ -n "$srv" ]; then
            ok "$name 握手通过（服务端: $srv）"
        else
            ok "$name 握手通过（返回 JSON-RPC 响应）"
        fi
        PASS=$((PASS + 1))
    elif [ -n "$out" ]; then
        warn "$name 启动了但响应非 JSON-RPC（首 200 字节: ${out:0:200}）"
        FAIL=$((FAIL + 1))
    else
        warn "$name 启动失败（5 秒内无输出）"
        FAIL=$((FAIL + 1))
    fi
}

# jcodemunch-mcp serve
verify_mcp "jcodemunch-mcp" "$JCODE_EXE" "serve"
# repomix --mcp
verify_mcp "repomix" "$REPO_EXE" "--mcp"
# headroom mcp serve
verify_mcp "headroom" "$HEAD_EXE" "mcp serve"

log ""
if [ $FAIL -eq 0 ]; then
    ok "全部 $PASS 个 MCP 工具握手通过"
    log ""
    log "${GREEN}${BOLD}🎉 自愈完成 — ZCode 桌面版重启后 MCP 工具将自动加载${RESET}"
    log ""
    exit 0
else
    err "$PASS 个通过 / $FAIL 个失败，请检查 PATH 与可执行文件"
    log ""
    exit 1
fi

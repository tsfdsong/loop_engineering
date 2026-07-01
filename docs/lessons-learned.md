# 事故教训库 (Lessons Learned)

> **单一真源**：本项目所有事故修复 + 教训的累积记录。
> **触发条件**：任何 v1.x.y 修复 PR 涉及"实际跑过 + 失败过"才能写一条。
> **写入规范**：每条事故 = 现象 + 根因 + 修复 + 教训，4 段不可少。

---

## 📚 L#001 · 2026-07-01 · v1.2.2 → v1.2.3 macOS 跨平台安装事故

### 现象
在 macOS（Homebrew Python 3.14）上跑 `curl -fsSL .../install.sh | bash -s -- --force` 后：
1. Step 3 报 `⚠ jcodemunch-mcp 安装失败` + `⚠ headroom 安装失败`
2. Step 4 报 `⚠ 三个 MCP 工具未全部找到，跳过桌面版配置写入`
3. 桌面版 ZCode MCP 配置未写入（用户手动 UI 配置三次才成功的历史问题再现）

### 根因（4 层）
1. **macOS 没有 `pip` 命令**：Homebrew Python 3.14 只装 `pip3`，install.sh 用 `command -v pip` 检测永远 false
2. **PEP 668 externally-managed-environment**：macOS Homebrew Python 是受保护环境，`pip3 install --user` 也被阻止
3. **Step 4 detect_mcp_exe 硬编码 Windows 路径**：fallback 只指向 `~/AppData/Roaming/Python/...` 和 `~/AppData/Roaming/npm/`，macOS 上根本不存在
4. **headroom 不是 MCP server**：包元数据 `entry_points` 为空、无 `__main__.py`，但 `merge_zcode_config.py` 把 headroom 当 CLI 配成 `command + ['mcp', 'serve']`，结果写入空 command 字段的坏配置

### 修复（4 处精准修复 + 1 处辅助）
- **install.sh `install_pkg()`**：
  - 加 `detect_pip_cmd()` 优先 `pip3`、fallback `pip`
  - 加 `--break-system-packages` fallback（解决 PEP 668）
- **install.sh `MCP_PACKAGES`**：加 `is_mcp_server` 第 3 列；`headroom=false`（标识非 MCP server）
- **install.sh `write_zcode_desktop_config()`**：
  - `detect_mcp_exe` 主动扫 PATH 外目录（`~/Library/Python/3.*/bin/`、`~/.local/bin/`）
  - 删 headroom 桌面配置（包无 MCP server 接口）
- **`scripts/merge_zcode_config.py`**：
  - 签名 4 参数 → 3 参数（删 head_exe）
  - 加 `data['mcp']['servers'].pop('headroom', None)` 兼容清理
- **install.sh `LOCAL_SRC_DIR` 辅助**：BASH_SOURCE 有值时用本地 `scripts/` 覆盖 `$WORK/scripts/`，便于开发测试本地修改立即生效

### 教训（5 条）
1. **macOS Python 用户脚本目录不是 `~/.local/bin/`**——Homebrew 默认装到 `~/Library/Python/<ver>/bin/`，必须主动扫这个目录
2. **PEP 668 不止影响 system pip**——`--user` 也被阻止，必须 `--break-system-packages`（家用机器可接受；生产环境应改用 venv/pipx）
3. **不要假设 Python 包一定有 CLI**——`pip show <pkg>` + PyPI `entry_points` 双重验证
4. **install.sh 的 `git clone` 远端覆盖风险**——本地修复需用 `LOCAL_SRC_DIR` 机制覆盖；否则改了本地但 `curl | bash` 仍拉远端旧版
5. **设计单一真源 ≠ 跨平台一成不变**——install.sh 应在 Step 0 加 `uname -s` 分发（macOS / Linux / Windows 三条路径），而不是全部硬编码 Windows 路径

### 验证（5 项必查）
| # | 检查 | 结果 |
|---|------|------|
| 1 | `~/.loopengine/.installed_version` = 1.2.3 | ✅ |
| 2 | `which jcodemunch-mcp` 或 `~/Library/Python/3.14/bin/jcodemunch-mcp --version` 正常 | ✅ |
| 3 | `~/.zcode/cli/config.json` mcp.servers 含 `jcodemunch` + `repomix`，无 headroom | ✅ |
| 4 | 7 工具红线文件各含 14 markers（7 BEGIN + 7 END） | ✅ |
| 5 | 9 工具 skills 目录各含 33 个 SKILL.md | ✅ |

---

<!-- BEGIN LOOPENGINE-MANAGED EVIDENCE-RULES -->
（待补：2026-06-29 v5.4 兼容性胡乱分析事故记录，详见 AGENTS.md §2）
<!-- END LOOPENGINE-MANAGED EVIDENCE-RULES -->
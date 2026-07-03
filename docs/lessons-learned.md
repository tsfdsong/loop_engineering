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
4. **headroom v0.x 早期版本无 MCP server 接口**（v1.2.2 当时）：包元数据 `entry_points` 为空、无 `__main__.py`，`merge_zcode_config.py` 配成空 command 字段的坏配置。**v1.3.1 修订**：headroom-ai ≥ v0.20 已提供 `headroom mcp serve` MCP server 命令，install.sh 可正常注入 `~/.cursor/mcp.json`（详见 merge_mcp_config.py cursor schema）

### 修复（4 处精准修复 + 1 处辅助）
- **install.sh `install_pkg()`**：
  - 加 `detect_pip_cmd()` 优先 `pip3`、fallback `pip`
  - 加 `--break-system-packages` fallback（解决 PEP 668）
- **install.sh `MCP_PACKAGES`**：加 `is_mcp_server` 第 3 列；`headroom=false`（**v1.2.2 当时**标识非 MCP server；v1.3.1 修订：headroom-ai ≥ v0.20 已提供 `headroom mcp serve`，但 ZCode 桌面版仍只注 jcodemunch+repomix）
- **install.sh `write_zcode_desktop_config()`**：
  - `detect_mcp_exe` 主动扫 PATH 外目录（`~/Library/Python/3.*/bin/`、`~/.local/bin/`）
  - 删 headroom 桌面配置（**v1.2.2 当时**包无 MCP server 接口）
- **`scripts/merge_zcode_config.py`**（**v1.3.1 已被 `merge_mcp_config.py zcode` 取代**）：
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
| 3 | `~/.zcode/cli/config.json` mcp.servers 含 `jcodemunch` + `repomix`，无 headroom（**v1.2.2 当时**；v1.3.1 仍成立 — ZCode 桌面版 schema 保持 2 server）| ✅ |
| 4 | 7 工具红线文件各含 14 markers（7 BEGIN + 7 END） | ✅ |
| 5 | 9 工具 skills 目录各含 33 个 SKILL.md | ✅ |

---

## 📚 L#002 · 2026-07-03 · v1.3.2 specs 卡死事故（安装时 `git pull` 永不退出）

### 现象
用户跑 `irm .../install.ps1 | iex` 后卡住不返回。后台实际有 **1 个 powershell.exe + 7 个 git.exe 子进程**（1 个主 + `git-remote-https` + `git-credential-helper` + 4 个 helper），CPU 不高但完全无响应，**永不退出**。`git pull` 反复重试 TCP/认证，从不报错。

### 根因（3 层叠加）
1. **specs 仓库根本不存在**：`https://github.com/tsfdsong/loop_engineering_specs.git` → `Repository not found`（`git ls-remote` 实证）
2. **本地脏 specs 目录**：`~/.loopengine/specs/.git` 已存在，origin 指向不存在的 URL，`git pull` 永远在该脏仓库上重试
3. **install 脚本的"失败不阻塞"逻辑只挡同步失败，不挡挂起**：
   - `bash install.sh`：`if (cd ... && git pull --ff-only 2>&1); then ... else git pull 失败（继续，不阻塞）` — 错误地假设 pull 失败会返回非 0
   - `install.ps1`：`& git ... pull --ff-only 2>&1 | Out-Null` — `2>&1 | Out-Null` 吞掉错误输出但**吞不掉挂起**

**核心混淆**：`git pull` 在远端不存在时**不是 fail** 而是 **hang**（反复重试 TCP/认证/HTTP 401）。这是 L#001 未触及的新故障类。

### 修复（5 处）
- **install.sh** (`1f0556e`)：删 `SPECS_MODE/SOURCE/TARGET_DIR` 常量 + 3 个 case 参数（`--skip-specs`/`--with-specs`/`--specs-source`）+ 整段 `install_specs()` 函数 + help 段相关行
- **install.ps1** (`5b76938`)：删 `Clone-Specs` 函数 + 3 个 env 常量（`$SkipSpecs/$WithSpecs/$SpecsSource`）+ `DefaultSpecsSource/SpecsTargetDir` 常量 + 主流程调用
- **本机清理**：杀掉 8 个 stuck 进程（`taskkill /F /IM git.exe; taskkill /F /IM powershell.exe`） + `rm -rf ~/.loopengine/specs` 删脏目录
- **3 文档**（`5b76938`）：删 README specs 徽章 + "设计文档外部化"段 + AGENTS.md 顶部 specs 行 + INSTALL.md env 表的 `LE_SKIP_SPECS` 行
- **设计层决定**：specs 功能**彻底删除**（不是默认跳过），避免任何"如果依赖不存在会怎样"的隐患

### 教训（5 条 → 已在 AGENTS.md §1.10 落地为硬规则）
1. **黄金路径测试纪律**：每个 release 必跑**用户最小命令**（零 flag）端到端至少 1 次。开发期 `--force` / `--skip-specs` 等 flag 是便利**不是替代**。
2. **区分 fail vs hang**：失败（sync fail，返回非 0）能用 `if ! cmd` 捕获；挂起（hang，永不返回）需要 `timeout N` 主动设上限。`2>/dev/null`/`2>&1 | Out-Null` **只吞错误信息，不终止挂起**。
3. **测试时禁用开发期 flag**：若加 flag 才"测试通过"，要立刻怀疑"用户裸跑会怎样"。`--skip-specs` 是开发便利，生产默认不应依赖。
4. **脏状态 = 测试失败**：本地有遗留 `~/.loopengine/specs/.git`（脏）时跑 `git pull` 100% 触发 hang。**测试前清环境**应成为肌肉记忆（`rm -rf ~/.loopengine/specs` 模拟首次安装）。
5. **加新功能时 red team 自己的设计**：specs 外部化是 5 轮前加的，当时没人问"如果 `loop_engineering_specs` 不存在会怎样"。**AI 加 feature 时要主动质疑"依赖不存在/慢/被墙"等降级路径**——任何一个没设计降级的依赖都是定时炸弹。

### 验证（5 项必查）
| # | 检查 | 结果 |
|---|------|------|
| 1 | `grep -c spec` install.sh / install.ps1 / docs/INSTALL.md = 0（除历史注释） | ✅ |
| 2 | `ls ~/.loopengine/` 仅含 `.installed_version`（无 specs/） | ✅ |
| 3 | `bash install.sh --force` 端到端跑完，无 `Step 1.5 specs` 段，无卡死 | ✅ |
| 4 | `irm -OutFile + &` 端到端从 GitHub raw 跑远端新版（`1f0556e`），无 `Step 1.5 specs` 段 | ✅ |
| 5 | `tasklist | grep git` 安装期间无 stuck 进程残留 | ✅ |

---

<!-- BEGIN LOOPENGINE-MANAGED EVIDENCE-RULES -->
（待补：2026-06-29 v5.4 兼容性胡乱分析事故记录，详见 AGENTS.md §2）
<!-- END LOOPENGINE-MANAGED EVIDENCE-RULES -->
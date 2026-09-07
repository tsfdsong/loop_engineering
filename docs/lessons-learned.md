# 事故教训库

> 写事故时必含：现象 · 根因 · 修复 · 教训。  
> hooks 会读本文件的 `## 📚 L#NNN` 标题注入会话。

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

## 📚 L#003 · 2026-07-03 · v1.3.2 piped-mode BASH_SOURCE 误解析事故（`/dev/scripts/install/_common.sh`）

### 现象
在 WSL / Git Bash 跑 `curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash` 立即报错并退出：

```
bash: line 61: /dev/scripts/install/_common.sh: No such file or directory
```

报错路径 `/dev/scripts/install/_common.sh` 明显不合理（`/dev` 是设备目录），但 install.sh 直接退出，`curl | bash` 这种"一行安装"的卖点完全失效。

### 根因（2 层）
1. **`install.sh:59` 的"防御性" fallback 反成 bug**：
   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-/dev/null}")" 2>/dev/null && pwd || echo "")"
   ```
   设计意图：BASH_SOURCE[0] 为空时 fallback 到 `/dev/null` 防止 unset 报错。
   实际效果：piped stdin 模式下 BASH_SOURCE[0] 确实为空 → fallback 命中 → `dirname /dev/null` 返回 `/dev` → SCRIPT_DIR 变成 `/dev` → `source /dev/scripts/install/_common.sh` 失败。
2. **引入时机为 v1.2.4 跨平台分层重构**（commit `e0c64a5`, 2026-07-01）：install.sh 从单体脚本改为"调度器 + _common.sh"分层，arch 同步加了 `:-/dev/null` 防止 `set -u` 在 piped 模式 unset BASH_SOURCE[0] 时报错，但 fallback 路径选错。**未跑过"用户最小命令"端到端测试**就发布了（违反 §1.10 第 1 条黄金路径测试纪律）。

### 修复（1 处精准修复 + R3.5 全仓扫描）
- **install.sh** (`b18b872`)：
  ```bash
  if [ -z "$SCRIPT_DIR" ] || [ "$SCRIPT_DIR" = "/dev" ]; then
      _COMMON_URL="https://github.com/tsfdsong/loop_engineering/raw/main/scripts/install/_common.sh"
      _COMMON_TMP="$(mktemp -t loopengine-common.XXXXXX.sh)"
      if ! curl -fsSL --max-time 30 "$_COMMON_URL" -o "$_COMMON_TMP"; then
          echo "❌ 无法下载 _common.sh: $_COMMON_URL" >&2
          rm -f "$_COMMON_TMP"
          exit 1
      fi
      source "$_COMMON_TMP"
      rm -f "$_COMMON_TMP"
  else
      source "$SCRIPT_DIR/scripts/install/_common.sh"
  fi
  ```
- **R3.5 同根扫描**：全仓 4 个 BASH_SOURCE 用法，仅 `install.sh:59` 用了 `:-/dev/null` 形式（其他处如 `hooks/_lib.sh` 用简单 `${BASH_SOURCE[0]}`，file-based 调用，不踩坑）。历史路径曾含 `skills/orch/hooks/*` / `skills/go/hooks/*`（已删除；会话 hook 统一走仓库根 `hooks/`）。
- **关键设计点**：不用 `source <(curl ...)` 是因为 bash process-substitution 怪癖 — curl 失败时 process substitution 的 fd 仍"open"，让 `source` 返回 0，导致 `||` 错误处理失效（静默吞错）。改用 `mktemp + if ! curl` 显式校验退出码。

### 教训（3 条）
1. **"防御性 fallback" 可能反成 bug**：用 `${VAR:-fallback}` 模式时，fallback 值必须经过 `dirname`/`source` 等"路径解释"工具的语义验证。`/dev/null` 在 `dirname` 视角下变成 `/dev`，不是"无害"路径。**经验法则**：fallback 应该 fallback 到"已知存在的路径"（如 `$(pwd)`），而不是"已知语义无害的伪路径"。
2. **跨模式端到端测试是 release 前置条件**（补强 §1.10）：install.sh 同时支持 file-based（`bash install.sh`）和 pipe-based（`curl | bash`）两种调用方式，但 v1.2.4 重构时只测了 file-based 一种模式，piped 模式从未被覆盖。**重构 install/deploy 类脚本时，必须同时跑 file-based + pipe-based 两种端到端测试**。
3. **`source <(curl ...)` 的 bash 怪癖是常见陷阱**：`source <(...)` 不会传播 `<(...)` 内命令的退出码，错误处理（`||` / `set -e`）全部失效。**改用临时文件 + 显式 `if ! curl` 校验退出码**，是更可靠的模式（即使文件略大也值得）。

### 验证（4 项必查）
| # | 检查 | 结果 |
|---|------|------|
| 1 | `cat install.sh \| bash`（本地 mock _common.sh）→ `COMMON_VERSION=1.3.1-mock` | ✅ |
| 2 | `bash install.sh`（file 模式）→ `COMMON_VERSION=1.3.1-mock`（无回归） | ✅ |
| 3 | `cat install.sh \| bash` + 不可达 URL → exit 1, elapsed 2s（fail-fast，未 hang） | ✅ |
| 4 | `bash -n install.sh` 语法检查通过 | ✅ |

---

## 📚 L#004 · 2026-07-03 · v1.3.2 PS 5.1 RemoteException 截断事故（4 处 `❌ …Traceback` 无具体内容）

### 现象
Windows PowerShell 5.1 用户跑 `irm … | & $le` 装 v1.3.2，Step 4 / Step 5 / Step 5.5 全部报：
```
❌ 合并 C:\Users\admin\.zcode\cli\config.json 失败：Traceback (most recent call last):
❌ [ZCode 红线] 失败：Traceback (most recent call last):
❌ [Cursor MCP] 失败：Traceback (most recent call last):
```
异常信息**只到 "Traceback (most recent call last):" 就截断**，完全没有 traceback 后续的 `File`、`line 42`、`TypeError` 等定位信息。`install_managed_rules()` 同步红线步骤全军覆没（7/7 targets fail），但安装脚本"假装"完成（"部署到 34 个路径"），用户无法判断是真错还是可忽略。

### 根因（3 层叠加）
1. **PS 5.1 RemoteException 的 `.Message` 只含 stderr 第一行**：当 PowerShell 5.1 启动 python 子进程，子进程向 stderr 写完 multi-line 异常后退出，PS 5.1 会把 stderr 包装成 `RemoteException` ErrorRecord，但 `.Message` 字段只保留**第一行**（即 "Traceback (most recent call last):"），完整堆栈在 `.ScriptStackTrace`、`.Exception.ErrorRecord.Exception.Message`、被 `2>&1` 捕获的 `$out` 等其他位置。
2. **旧 install.ps1 在 4 个 catch 块都用 `$_.Exception.Message`**（commit `1ed3a82` / `c8862f0` v1.3.2 修复时引入）：`try { & python ... 2>&1 } catch { Write-Err "失败：$($_.Exception.Message)" }` —— `.Message` 在 PS 5.1 下就是"Traceback..."那一行，所以错误输出形如"失败：Traceback (most recent call last):"（仅前缀 + 第一行，无任何定位信息）。
3. **R3.5 同根扫描缺失**：v1.3.2 提交时只测了"happy path"（$LASTEXITCODE != 0 时的 `Write-Err "失败（exit N）: $out"`），**未测 catch 分支**（PS 5.1 RemoteException 路径），所以"错误信息被截断"这个 bug 一直没被暴露。**违反 §1.10 第 1 条黄金路径测试纪律**：只测了 success 路径，未测 error 路径。

### 修复（新增 `Format-PSError` 辅助 + 4 处替换）
- **install.ps1 新增 `Format-PSError($e)` 辅助函数**（line 93-117，~25 行）：
  ```powershell
  # 输出格式：5 行缩进对齐，保留 ❌ 前缀给 Write-Err，完整堆栈给 Write-Host
  function Format-PSError($e) {
      $indent = "     "
      $sb = New-Object System.Text.StringBuilder
      [void]$sb.AppendLine("$indent$($e.Exception.GetType().FullName)")
      $msg = ($e.Exception.Message -split "`r?`n" | ForEach-Object { "$indent$($_)" }) -join "`n"
      [void]$sb.AppendLine($msg.TrimEnd())
      if ($e.ScriptStackTrace) {
          $st = ($e.ScriptStackTrace -split "`r?`n" | Select-Object -First 5 | ForEach-Object { "$indent$($_)" }) -join "`n"
          [void]$sb.AppendLine($st)
      }
      if ($e.Exception.ErrorRecord -and $e.Exception.ErrorRecord.Exception) {
          $inner = $e.Exception.ErrorRecord.Exception
          [void]$sb.AppendLine("$indent--- inner ---")
          [void]$sb.AppendLine("$indent$($inner.GetType().FullName): $($inner.Message)")
      }
      return $sb.ToString().TrimEnd()
  }
  ```
- **4 处 catch 块替换**（`render_plugins` Step 2a / `merge_mcp_config` Step 4 / `inject_rules` Step 5 / `merge_mcp_config` Step 5.5）：
  ```powershell
  } catch {
      Write-Err "合并 $cfg 失败（PS 5.1 RemoteException）"   # 之前是 "...失败：$($_.Exception.Message)"
      Write-Host (Format-PSError $_) -ForegroundColor Red   # 新增：完整堆栈
      return
  }
  ```
- **关键设计点**：
  1. **`$e.Exception.Message -split "`r?`n"`** 是关键：即使 PS 5.1 把 Message 截断到第一行，至少保留换行后的尾部；未截断时（`$LASTEXITCODE` 路径）能完整展示。
  2. **不只依赖 `.Message`**，并行展示 `ScriptStackTrace`（PowerShell 调用栈）和 `.ErrorRecord.Exception`（嵌套 inner exception），三个数据源互补，最大化恢复概率。
  3. **保留 `Write-Err` 单行 ❌ 前缀**（用户熟悉的格式），把多行堆栈**追加到下一行**用 `Write-Host -ForegroundColor Red`（不被 `Write-Err` 截断/重格式化），最不容易破坏现有日志/正则。
- **R3.5 同根扫描**：全 install.ps1 4 个 catch 块（`render_plugins` / `merge_mcp_config zcode` / `inject_rules` / `merge_mcp_config cursor`）4/4 全部替换；`render_plugins.py` 自身不变（它是 Python 子进程，不是 PS 错误处理点）。
- **install.sh 不修**：bash 直接 `2>&1` 捕获 stderr 到 `$out`，无 RemoteException 概念，原生 multi-line 完整。`grep "失败" install.sh` 0 hits，证明 bash 路径无此问题。

### 教训（4 条）
1. **PS 5.1 错误处理铁律**："**永远不要在 catch 块只读 `$_.Exception.Message`**"。完整信息散落在 4 个字段：`.Message`（可能截断）、`.ScriptStackTrace`（PS 调用栈）、`.Exception.ErrorRecord.Exception.Message`（嵌套 inner）、被 `2>&1` 捕获到 `$out`（子进程原始输出）。**用 helper 函数聚合**才能稳定恢复（本次 `Format-PSError`）。
2. **R3.5 全仓扫描的"同根"判别标准 = 错误模式相同**（不是文件位置相同）。4 个 catch 块分布在 install.ps1 不同函数（Step 2a / Step 4 / Step 5 / Step 5.5），但**错误模式都是 "PS 5.1 RemoteException + `.Exception.Message`"**，同根变体必须一次性全修。
3. **黄金路径测试必须含 error 路径**（补强 §1.10 第 1 条）：v1.3.2 之前的 PR 只在 happy path 跑通就发版，但**错误处理的回归测试比 happy path 更重要**（happy path 出错会立刻被用户看到；error path 出错会被静默吞掉，半年后才被用户挖出）。**新加测试纪律**："任何 catch 块至少配 1 个 negative test，强制触发该 catch 并断言输出含关键定位信息"。
4. **unit test 必须真实触发目标 bug，不能用合成 exception 蒙混**（debug 教训）：第一次写 Test 3 用 `RuntimeException("Traceback: ...")` 合成，意外发现 `RuntimeException` 不会触发 PS 5.1 的截断行为（截断只发生在**子进程 stderr**），导致 Test 3 假设错误。**改用模拟的"first-line-only" message**（传 `"Traceback (most recent call last):"` 给 ErrorRecord）来忠实模拟真实 PS 5.1 RemoteException 行为。**经验法则**：bug 在哪一层触发，test 必须在那一层模拟。

### 验证（5 项必查）
| # | 检查 | 结果 |
|---|------|------|
| 1 | `tests/test-format-pserror.ps1` 3/3 测试通过（multi-line Message / single-line regression / truncated-message recovery） | ✅ |
| 2 | `Parser::ParseFile(install.ps1)` 语法检查通过（4020 tokens） | ✅ |
| 3 | 4 处 catch 块 `grep "Exception.Message"` 仅剩 2 处（1 处在 Format-PSError 内部正确用法，1 处在 helper 顶部 bug 背景注释，均非 catch 块） | ✅ |
| 4 | install.sh 无 `失败` 关键字（bash 路径不受影响） | ✅ |
| 5 | 全 install.ps1 4/4 catch 块都用 `Format-PSError $_`（R3.5 同根扫描） | ✅ |

---

## 📚 L#005 · 2026-07-03 · v1.3.2 PS 5.1 UTF-8 无 BOM 文件解析事故（test 文件 with Chinese fails to parse）

### 现象
写 `tests/test-format-pserror.ps1` 时加了带中文的 `<# ... #>` block 注释（"验证 PS 5.1 RemoteException 下能暴露完整 Python 堆栈"），运行测试报：
```
Get-Content : 无法将参数绑定到参数"Path"，因为该参数是空值。
所在位置 C:\tsfdsong\python-project\loop_engineering\tests\test-format-pserror.ps1:13 字符: 22
+ $lines = Get-Content $installPs1
+                      ~~~~~~~~~~~
```
行 13 是 `$installPs1 = Join-Path $projectRoot 'install.ps1'`，但 PowerShell 报错的源码行（"line 13"）显示的是 `$lines = Get-Content $installPs1`（行 14）—— **整个文件解析被 block 注释里的中文污染**，导致 `$installPs1` 变量没被赋值就跳到下一行。

### 根因（2 层）
1. **PS 5.1 默认按系统 ANSI 代码页（Windows-1252 / GBK）解析 `.ps1` 文件**，不识别 UTF-8 多字节序列。`install.ps1` 顶部有 UTF-8 BOM（`ef bb bf`），PS 5.1 看到 BOM 才切换到 UTF-8 解码模式；`tests/test-format-pserror.ps1` 是 `Write` 工具默认输出（无 BOM），PS 5.1 按 ANSI 解码时把 `e9 aa 8c`（验）等 3 字节 UTF-8 序列当成 3 个单字节字符，**后续的 ASCII 也因 decoder state 错位而错位**，直到下一个换行才重置—— 导致 `$installPs1 = ...` 这行被错误地"吞掉"，变量没赋值。
2. **`Write` 工具不主动加 BOM**：BOM 在 cross-platform 场景有争议（PS 7+ 仍认 BOM，bash 不认），多数编辑器/工具默认不写 BOM。**这是 PS 5.1 的 historic 包袱**，PS 6+ 已切到 UTF-8 默认，但 PS 5.1 是 Windows 默认 shell（用户群最大），无法绕过。

### 修复（2 处决策）
- **本次 test 文件**：去掉所有中文（`# ...` inline 注释 + `<# ... #>` block 注释 + 字符串字面量），保持 ENGLISH-ONLY + 顶部加注释说明 "PS 5.1 编码陷阱"。test 不是交付件，不影响产品。
- **未来 `.ps1` 模板（如 `install.ps1` 副本 / new test 模板）**：在 PS 5.1 兼容期内（5+ 年），所有 .ps1 文件**默认带 UTF-8 BOM**。`install.ps1` 现有 BOM 不动（验证过 `head -c 5 install.ps1 | xxd` 是 `ef bb bf 23 20`），`render_plugins.py` / `merge_mcp_config.py` / `inject_rules.py` 等 Python 文件**不受影响**（Python 3 默认 UTF-8）。

### 教训（3 条）
1. **PS 5.1 文件编码铁律**：**.ps1 文件含非 ASCII 字符 → 必须有 UTF-8 BOM**（`ef bb bf` 头 3 字节）。无 BOM 的 .ps1 在 PS 5.1 下，block 注释里的中文会把整个文件解析搞坏（变量赋值失效、错误行号偏移 ±1）。**新 PS 模板的最低验收标准**：`head -c 5 file.ps1 | xxd` 必须以 `efbbbf` 开头（如果含中文/emoji）。
2. **错误行号偏移 = 文件解析损坏的早期信号**：本次错误报"line 13"但实际错误在 line 14，且 `$installPs1` 显示 null —— 这是 PS 5.1 文件解析的典型症状。**遇到"line N 报错但代码看着对"**，第一反应是检查文件 BOM（`head -c 5 file.ps1 | xxd`），而不是怀疑逻辑。
3. **测试文件不是交付件，可妥协**：交付件（install.ps1、_common.sh）必须支持中英文用户（带 BOM + 中文 OK）；**test 文件只需在 PS 5.1 + 开发者本地能跑**，可以 ENGLISH-ONLY（不损失可读性，省 BOM 复杂度）。**判别标准**：test 是开发者工具，install 是用户契约 —— 同样 1 个中文字符，处理方式可不同。

### 验证（4 项必查）
| # | 检查 | 结果 |
|---|------|------|
| 1 | `head -c 5 install.ps1 \| xxd` → `efbbbf`（UTF-8 BOM 存在） | ✅ |
| 2 | `head -c 5 tests/test-format-pserror.ps1 \| xxd` → `23727171`（`#requ`，无 BOM，但全 ENGLISH 无中文可接受） | ✅ |
| 3 | 去掉中文后 `powershell -File tests/test-format-pserror.ps1` 3/3 PASS | ✅ |
| 4 | `Parser::ParseFile(install.ps1)` 4020 tokens 无 syntax error | ✅ |

---

<!-- BEGIN LOOPENGINE-MANAGED EVIDENCE-RULES -->
（待补：2026-06-29 v5.4 兼容性胡乱分析事故记录，详见 AGENTS.md §2）
<!-- END LOOPENGINE-MANAGED EVIDENCE-RULES -->## 📚 L#006 · 2026-09-07 · skill-creator 描述优化 · 评测基线全零伪影（`claude -p` 认证失败被计为"不触发"）

### 现象
对 grilling 技能跑 skill-creator 描述优化的触发评测，20 条查询 × 3 次全部返回"不触发"：10 条正样本 recall=0%（0/30），一度得出"**grilling 严重欠触发，TRIGGER 三段式格式可能全仓失效**"的重大结论，险些据此改动 34 个技能的 description 格式。

### 根因（3 层叠加）
1. **`claude -p` 认证失败的行为伪装**：OAuth 过期时进程 `exit=1` 但错误文本（`Failed to authenticate: OAuth session expired...`）走 **stdout**——评测器把它当"模型的回答"去解析触发标记。
2. **评测器的默认值语义**：`run_eval.py` 解析不到触发标记时默认返回 `triggered=False`——依赖故障被静默转译为"模型选择了不触发"，产生**系统性偏差**（60/60 调用全失败 = 60/60 "不触发"，正负样本恰好"符合"一半预期，更具迷惑性）。
3. **诊断复现的管道陷阱**：主代理首次复现用 `claude -p ... 2>&1 | head -5; echo $?`——zsh 中 `$?` 取的是 **head 的退出码（0）**，得出"exit=0 静默失败"的错误判断，把诊断引向"评测器吞错"的错误方向。

**确证方式**：干净复现 `env -u CLAUDECODE claude -p "Reply ok"` → 错误文本 + `exit=1`，退出码与错误通道还原真相。

### 修复（3 处）
- **结论撤回**：recall=0% 判定为认证伪影，"TRIGGER 格式失效"假说降级为未验证假设，禁止据此改格式
- **评测资产保全**：4 技能 × 20 条评测集归档 `~/.loopengine/eval-archive/desc-opt/`（/tmp 易失），认证恢复后重测
- **定时续跑**：限额重置后自动重跑（CronCreate），重测前先冒烟验证认证

### 教训（4 条）
1. **外部 CLI 评测前先冒烟**：跑任何依赖外部模型 CLI 的评测循环前，先手工调 1 次并**检查输出是模型语言而非错误文本**——区分"模型说 NO"与"根本没问成"。
2. **全零结果是环境故障信号**：真实模型行为总有方差，30 次调用 0 触发（连"拷问""审讯"这种显式词都不触发）应先怀疑评测链路故障，再怀疑被测对象。
3. **管道后取退出码用 `pipestatus`**（zsh）/`${PIPESTATUS[0]}`（bash），或干脆不用管道——`echo $?` 取的是管道**最后一个命令**的退出码。
4. **审视评测器的默认值语义**：`default=False` 在依赖故障时会变成系统性偏差源；评测器应在输出异常时区分"模型回答"与"调用失败"。
5. **（2026-09-07 补充）评测机制本身也要对照验证**：限额恢复后真实重测，grilling 仍 recall=0%——但对照组实验（skill-creator 官方英文 description）同样 0/3 触发，确诊为**机制伪影**：skill-creator 的触发评测（伪装 `.claude/commands` 斜杠命令 + `claude -p` 非交互）在此模式下不触发任何技能。教训：**评测给出极端结果时，先用已知优质的对照组校准评测机制本身**，再解读被测对象；跨环境评测工具（为 Claude 设计）在 ZCode/GLM 生产环境的结论不可直接迁移。

---

## 📚 L#007 · 2026-09-06~07 · ZCode 官方 registry 周期性冲掉本地插件注册（marketplace 条目 4 次丢失 + 已删目录被重建）

### 现象
- `install.py install` 成功写入 loopengine 的 marketplace 条目后，**39 秒内**被冲掉（时间戳实证），验证期间累计复发 4 次
- skill-creator（Anthropic 官方版）升级到 `0.2.0-anthropic.85cce0381e` 并删除 `0.1.0` 目录后：**旧目录被应用重建**，registry 条目被冲回 `0.1.0`
- 审计 `audit_tools.py` 的 G 维度随之间歇性报红（`marketplace.json 缺 loopengine 条目`），一度被误判为安装器 bug

### 根因（2 层）
1. **ZCode CLI 周期性从官方远端同步 registry**：重写 `~/.zcode/cli/plugins/marketplaces/zcode-plugins-official/marketplace.json`，只保留远端 manifest 存在的 8 个官方插件——loopengine（本地注入）与 skill-creator（已从远端下架）的条目必然被抹，重装频率无关。
2. **应用缓存同步会重建已删除的旧版本目录**：删除 `skill-creator/0.1.0` 后被再次创建——"删除旧版"不是终态操作。

### 修复（1 处 · 结构性）
`hooks/zcode-marketplace-selfheal.sh`（SessionStart hook）：
- 守护 loopengine（seed 文件）+ skill-creator（扫描缓存目录取最高版本）双条目
- 幂等：健康时静默 no-op（不重写文件）；被冲时从本地缓存事实重建
- 安全边界：不动官方远端条目、官方文件损坏时保护性跳过、任何失败不阻塞会话启动
- 9 个 pytest 场景（heal/no-op/过期更新/损坏保护/seed 缺失/双插件/最高版本选择）
- 接线 `hooks/hooks.json` SessionStart（与 verify-state-init 并列）

**备选方案否决记录**：独立 `loopengine-local` marketplace 方案曾实施后废弃——zcode UI 会浮现第二个关闭态的 `loopengine@loopengine-local` 条目（`adapters/zcode.py` L292 注释存档）。

### 教训（3 条）
1. **注入外部应用管辖的注册表 = 假设会被覆盖**：任何写入非本项目管辖文件（应用的 registry/缓存/配置）的操作，都要回答"应用刷新后怎么办"——一次性写入不是终态。
2. **自愈优于锁文件**：无法真正锁住应用管辖的文件（chflag/权限会破坏应用自身功能）；会话启动幂等重注入（自愈）与"每次用时校验"（审计）双管齐下更稳。
3. **间歇性报红先查时间戳**：`marketplace.json` 的 mtime 与安装完成时间的差值（39 秒）是判定"谁改了文件"的关键证据——先取时间线再怀疑自己的安装器。

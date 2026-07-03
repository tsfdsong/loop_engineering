# ════════════════════════════════════════════════════════════
# LoopEngine 一键安装 v1.3.2 — Windows PowerShell 版（纯 PS，无需 Git Bash）
# ════════════════════════════════════════════════════════════
# 设计：单模式（强制）。每次执行都覆盖所有文件，无 dry-run/无版本等待。
#
# 一行安装（PowerShell）:
#   $le = "$env:TEMP\le.ps1"
#   irm https://github.com/tsfdsong/loop_engineering/raw/main/install.ps1 -OutFile $le
#   & $le; Remove-Item $le
#
# 本地执行:  .\install.ps1
#
# 可选环境变量（控制部署范围）:
#   $env:LE_ALL=1; .\install.ps1           # 强制全量（9+ 工具）
#   $env:LE_ONLY="zcode,cursor"; .\install.ps1
#   $env:LE_SKIP_SPECS=1; .\install.ps1    # 跳过设计文档 clone
#
# 注意：本脚本不使用 param() 块（irm|iex 模式下 iex 把脚本当表达式执行，
#       param() 会报"意外的属性 CmdletBinding"）。参数全部通过环境变量传入。
#
# 兄弟脚本: install.sh（macOS/Linux/Git Bash）。两者共用 3 个 Python helper:
#   scripts/render_plugins.py / scripts/inject_rules.py / scripts/merge_mcp_config.py
# 行为契约对齐 _common.sh（行号见各函数注释）。未来 bash 版改动需手动同步本文件。
#
# v1.3.2 关键设计（避免重蹈 bash 版 3 个 bug）:
#   • $AgentList 原生空格分隔（bash 版 detect 用换行 → filter 误拒，已修）
#   • Cursor skills 扁平 ~/.cursor/skills/<name>/（bash 版多两层，已修）
#   • headroom 可选不阻断 Cursor MCP（bash 版强制 3 个全找到，已修）
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# 参数：通过环境变量传入（兼容 irm | iex 模式，iex 不支持 param()/${args}）
# ════════════════════════════════════════════════════════════
# 设计原则：单模式（强制）。每次执行都强制覆盖文件，无 dry-run / 无版本等待，简单高效。
#
# 用法：
#   一行安装:  irm https://.../install.ps1 -OutFile $le; & $le; Remove-Item $le
#   本地执行:  .\install.ps1
#
# 环境变量（可选，控制部署范围）:
#   LE_ALL=1             强制全量部署（绕过 detect，所有 9+ 工具）
#   LE_ONLY="zcode,cursor"  指定 agent id（逗号或空格分隔）
$All        = [bool]$env:LE_ALL
$Only       = $env:LE_ONLY

# 强制 UTF-8 输出（避免 emoji 🔴 乱码）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

# 强制 TLS 1.2（PowerShell 5.1 默认 TLS 1.0 会被 GitHub raw 拒绝 → "连接被意外关闭"）
# 注意：这一行只对脚本内的 git/python 网络操作生效；
#       用户跑 `irm | iex` 那一行命令本身的 TLS 必须在命令前设置（见 README/INSTALL 文档）
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {
    # PowerShell Core (7+) 默认已 TLS 1.2+，设置可能多余，忽略错误
}

# ── 常量（与 _common.sh L25-31 / install.sh L70-71 同源）─────────
$script:Repo = "https://github.com/tsfdsong/loop_engineering"
$script:Version = "1.3.2"
$script:VersionFile = Join-Path $env:USERPROFILE ".loopengine\.installed_version"

# ── 全局状态 ──────────────────────────────────────────────
$script:Work = ""                  # clone 出来的代码根（Step 1 后赋值）
$script:ScriptDir = ""             # 引用 scripts/*.py 的根
$script:RenderedDir = ""           # 渲染后的 manifest 目录
$script:Targets = [System.Collections.ArrayList]::new()  # 已部署路径
$script:LocalSrcDir = $PSScriptRoot  # 本地仓库根（irm|iex 时为空）

# label → agent id 映射（_common.sh L37-46）
$script:LabelToId = @{
    "ZCode"          = "zcode"
    "Claude Code"    = "claude-code"
    "Codex"          = "codex"
    "Gemini CLI"     = "gemini-cli"
    "GitHub Copilot" = "github-copilot"
    "Pi"             = "pi"
    "Cursor"         = "cursor"
    "ZCode 内置包"   = "zcode-bundled"
    "ZCode CLI 缓存" = "zcode-cli-cache"
}
$script:AllAgentIds = "zcode claude-code codex gemini-cli github-copilot pi cursor zcode-bundled zcode-cli-cache"

# ── 颜色输出 ──────────────────────────────────────────────
function Write-Info($msg)  { Write-Host "  ℹ  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "  ⚠  $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "  ❌ $msg" -ForegroundColor Red }
function Write-Step($msg)  { Write-Host ""; Write-Host $msg -ForegroundColor White }

# ── 错误格式化（PS 5.1 RemoteException 兼容）─────────────
# 背景：v1.3.2 教训 L#004 — `$_.Exception.Message` 在 PS 5.1 RemoteException 下
#       只截取 Python 异常第一行（"Traceback (most recent call last):"），
#       完整堆栈在 ScriptStackTrace / ErrorRecord / $out 中。本函数拼成多行
#       缩进对齐的字符串，保留 ❌ 前缀给 Write-Err 用，完整堆栈给 Write-Host。
# 用法：Write-Host "  ❌ 上下文"; Write-Host (Format-PSError $_)
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

# ════════════════════════════════════════════════════════════
# Step 0.5: Detect-Agents（对齐 _common.sh:134-170）
# ════════════════════════════════════════════════════════════
function Detect-Agents {
    $found = [System.Collections.ArrayList]::new()
    # 注意：$home 是 PowerShell 只读自动变量，必须改用 $homeDir
    $homeDir = $env:USERPROFILE

    # zcode
    if (Test-Path (Join-Path $homeDir ".zcode")) { [void]$found.Add("zcode") }
    # claude-code: env CLAUDE_CONFIG_DIR 优先
    $ccd = [Environment]::GetEnvironmentVariable("CLAUDE_CONFIG_DIR")
    if ($ccd -and (Test-Path $ccd)) { [void]$found.Add("claude-code") }
    elseif (Test-Path (Join-Path $homeDir ".claude")) { [void]$found.Add("claude-code") }
    # codex: env CODEX_HOME 优先
    $ch = [Environment]::GetEnvironmentVariable("CODEX_HOME")
    if ($ch -and (Test-Path $ch)) { [void]$found.Add("codex") }
    elseif (Test-Path (Join-Path $homeDir ".codex")) { [void]$found.Add("codex") }
    # 其余 5 个
    if (Test-Path (Join-Path $homeDir ".gemini"))  { [void]$found.Add("gemini-cli") }
    if (Test-Path (Join-Path $homeDir ".copilot")) { [void]$found.Add("github-copilot") }
    if (Test-Path (Join-Path $homeDir ".pi"))      { [void]$found.Add("pi") }
    if (Test-Path (Join-Path $homeDir ".cursor"))  { [void]$found.Add("cursor") }

    # 返回空格分隔字符串（原生正确，不重蹈 bash 换行 bug）
    return ($found -join ' ')
}

# ════════════════════════════════════════════════════════════
# Step 0: Show-Status（打印当前状态，强制模式不等待）
# ════════════════════════════════════════════════════════════
function Show-Status {
    $installed = ""
    if (Test-Path $script:VersionFile) {
        $installed = (Get-Content $script:VersionFile -Raw -ErrorAction SilentlyContinue).Trim()
    }
    if (-not $installed) {
        Write-Ok "首次安装 v$($script:Version)"
    } elseif ($installed -eq $script:Version) {
        Write-Ok "已装 v${installed}（同版，强制覆盖）"
    } else {
        Write-Ok "检测到 v${installed}，覆盖到 v$($script:Version)"
    }
}

# ════════════════════════════════════════════════════════════
# Step 1: Clone-Repo + 本地覆盖（对齐 _common.sh:458-495）
# ════════════════════════════════════════════════════════════
function Clone-Repo {
    $script:Work = Join-Path $env:TEMP "loopengine-install-$PID"
    if (Test-Path $script:Work) { Remove-Item $script:Work -Recurse -Force }
    Write-Step "📥 Step 1: 拉取最新源码..."

    & git clone --depth 1 --quiet $script:Repo $script:Work 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "无法 clone 仓库，请检查网络 / VPN"
        exit 1
    }
    $script:ScriptDir = $script:Work

    # 本地优先覆盖（仅当 $PSScriptRoot 非空且含 scripts/，即本地仓库执行）
    # irm | iex 时 $PSScriptRoot 为空，自然不触发（对齐 bash BASH_SOURCE 行为）
    if ($script:LocalSrcDir -and (Test-Path (Join-Path $script:LocalSrcDir "scripts"))) {
        # scripts/*.py
        Get-ChildItem (Join-Path $script:LocalSrcDir "scripts\*.py") -ErrorAction SilentlyContinue |
            ForEach-Object { Copy-Item $_.FullName (Join-Path $script:Work "scripts\") -Force }
        # 6 个 *-plugin/plugin.json（注意：无 .gemini-plugin）
        foreach ($p in @(".zcode-plugin",".claude-plugin",".codex-plugin",".cursor-plugin",".copilot-plugin",".pi-plugin")) {
            $src = Join-Path $script:LocalSrcDir "$p\plugin.json"
            if (Test-Path $src) {
                $dstDir = Join-Path $script:Work $p
                New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
                Copy-Item $src $dstDir -Force
            }
        }
        # gemini-extension.json
        $ge = Join-Path $script:LocalSrcDir "gemini-extension.json"
        if (Test-Path $ge) { Copy-Item $ge $script:Work -Force }
        Write-Info "本地 scripts/ + plugin manifest 已覆盖 clone 副本（开发模式）"
    }

    $skillCount = (Get-ChildItem (Join-Path $script:Work "skills") -Directory -ErrorAction SilentlyContinue).Count
    Write-Ok "已克隆到 $($script:Work) · $skillCount 个技能目录"
}

# ════════════════════════════════════════════════════════════
# tool-root-dirs（对齐 _common.sh:204-231 Windows 分支 9 行）
# ════════════════════════════════════════════════════════════
function Get-ToolRootDirs {
    $h = $env:USERPROFILE
    # base 7 行（跨平台共享）
    $base = @(
        @{Label="ZCode";          Path=(Join-Path $h ".zcode\skills\loopengine")}
        @{Label="Claude Code";    Path=(Join-Path $h ".claude\skills\loopengine")}
        @{Label="Codex";          Path=(Join-Path $h ".codex\skills\loopengine")}
        @{Label="Gemini CLI";     Path=(Join-Path $h ".gemini\extensions\loopengine")}
        @{Label="GitHub Copilot"; Path=(Join-Path $h ".copilot\skills\loopengine")}
        @{Label="Pi";             Path=(Join-Path $h ".pi\skills\loopengine")}
        @{Label="Cursor";         Path=(Join-Path $h ".cursor\skills\loopengine")}
    )
    # Windows 追加 2 行
    $bundled = @{Label="ZCode 内置包";   Path=(Join-Path $h "AppData\Local\Programs\ZCode\resources\glm\packages\loopengine-plugin")}
    $cliCache = @{Label="ZCode CLI 缓存"; Path=(Join-Path $h ".zcode\cli\plugins\cache\zcode-plugins-official\loopengine")}
    return @($base + $bundled + $cliCache)
}

function Filter-ToolRootDirs($entries, $wantIds) {
    $want = " $wantIds ".Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
    $result = @()
    foreach ($e in $entries) {
        $id = $script:LabelToId[$e.Label]
        if (-not $id -or ($want -contains $id)) { $result += $e }
    }
    return $result
}

# ════════════════════════════════════════════════════════════
# Step 2a: Render-Plugins（对齐 _common.sh:497-507）
# ════════════════════════════════════════════════════════════
function Render-Plugins {
    Write-Step "Step 2a: 渲染 7 个 plugin manifest..."
    $script:RenderedDir = Join-Path $script:Work ".rendered-manifests"
    # PS 5.1：python 抛异常时 stderr 转 RemoteException，$LASTEXITCODE 可能为 0
    try {
        $out = & python (Join-Path $script:ScriptDir "scripts\render_plugins.py") $script:Work $script:RenderedDir 2>&1
    } catch {
        Write-Err "manifest 渲染失败（PS 5.1 RemoteException）"
        Write-Host (Format-PSError $_) -ForegroundColor Red
        exit 1
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Err "manifest 渲染失败（exit ${LASTEXITCODE}）"
        Write-Err "python 输出: $out"
        exit 1
    }
    Write-Ok "manifest 渲染完成: $($script:RenderedDir)"
}

# ════════════════════════════════════════════════════════════
# Step 2b-pre: Cleanup-TargetTopLevel（对齐 _common.sh:566-586 · 13 项白名单 1:1）
# ════════════════════════════════════════════════════════════
function Cleanup-TargetTopLevel($label, $rootDir) {
    if (-not (Test-Path $rootDir -PathType Container)) { return }
    $whitelist = @(
        "hooks","skills",".zcode-plugin",".claude-plugin",".codex-plugin",
        ".cursor-plugin",".copilot-plugin",".pi-plugin","AGENTS.md","README.md",
        "package.json","marketplace.json","gemini-extension.json"
    )
    Get-ChildItem -Path $rootDir -Force -ErrorAction SilentlyContinue |
        Where-Object { $whitelist -notcontains $_.Name } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Ok "[$label] 顶层清理完成: $rootDir"
}

# ════════════════════════════════════════════════════════════
# Step 2b: Copy-Skills（标准 plugin 中间层 + Cursor 扁平特殊处理）
# 对齐 _common.sh:576-617（v1.3.2 修复后的 Cursor 扁平逻辑）
# ════════════════════════════════════════════════════════════
function Copy-Tree($label, $src, $dst) {
    if (-not (Test-Path $src -PathType Container)) {
        Write-Warn "[$label] 源不存在: ${src}（跳过）"
        return
    }
    New-Item -ItemType Directory -Path $dst -Force | Out-Null
    # 清空 dst 再复制（标准 plugin 隔离目录，安全）
    Get-ChildItem $dst -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $src "*") $dst -Recurse -Force -ErrorAction SilentlyContinue
    [void]$script:Targets.Add("$label skills`:$dst")
    Write-Ok "[$label] $dst"
}

function Copy-Skills($label, $rootDir, $skillsDir) {
    # Cursor: 扁平平铺到 ~/.cursor/skills/，逐 skill 覆盖（绝不清空公共目录）
    if ($label -eq "Cursor") {
        $skillDst = Split-Path $rootDir -Parent  # ~/.cursor/skills
        if (-not (Test-Path $skillsDir)) {
            Write-Warn "[Cursor skills] 源不存在: ${skillsDir}（跳过）"
            return
        }
        New-Item -ItemType Directory -Path $skillDst -Force | Out-Null
        $count = 0
        foreach ($sub in (Get-ChildItem $skillsDir -Directory)) {
            $name = $sub.Name
            $target = Join-Path $skillDst $name
            if (Test-Path $target) { Remove-Item $target -Recurse -Force -ErrorAction SilentlyContinue }
            Copy-Item $sub.FullName $target -Recurse -Force -ErrorAction SilentlyContinue
            $count++
        }
        [void]$script:Targets.Add("Cursor skills`:$skillDst")
        Write-Ok "[Cursor skills] $count 个 → ${skillDst}（扁平）"
        return
    }
    # 其他 harness: 标准 plugin 中间层 $rootDir/skills
    Copy-Tree "$label skills" $skillsDir (Join-Path $rootDir "skills")
}

# ════════════════════════════════════════════════════════════
# Step 2c: Copy-Hooks
# ════════════════════════════════════════════════════════════
function Copy-Hooks($label, $rootDir, $hooksDir) {
    Copy-Tree "$label hooks" $hooksDir (Join-Path $rootDir "hooks")
}

# ════════════════════════════════════════════════════════════
# Step 2d: Deploy-Manifest（对齐 _common.sh:637-660 · 7 label 分发）
# ════════════════════════════════════════════════════════════
function Copy-OneFile($label, $src, $dst) {
    if (-not (Test-Path $src)) { Write-Warn "[$label] 源不存在: ${src}（跳过）"; return }
    $dstDir = Split-Path $dst -Parent
    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    Copy-Item $src $dst -Force
    [void]$script:Targets.Add("$label`:$dst")
    Write-Ok "[$label] $dst"
}

function Deploy-Manifest($label, $rootDir) {
    $r = $script:RenderedDir
    switch ($label) {
        { $_ -in @("ZCode","ZCode 内置包","ZCode CLI 缓存") } {
            Copy-OneFile "$label plugin.json" (Join-Path $r "zcode-plugin\plugin.json") (Join-Path $rootDir ".zcode-plugin\plugin.json")
        }
        "Claude Code" {
            Copy-OneFile "$label plugin.json" (Join-Path $r "claude-plugin\plugin.json") (Join-Path $rootDir ".claude-plugin\plugin.json")
            Copy-OneFile "$label marketplace.json" (Join-Path $r "claude-plugin\marketplace.json") (Join-Path $rootDir ".claude-plugin\marketplace.json")
        }
        "Codex" {
            Copy-OneFile "$label plugin.json" (Join-Path $r "codex-plugin\plugin.json") (Join-Path $rootDir ".codex-plugin\plugin.json")
        }
        "Cursor" {
            Copy-OneFile "$label plugin.json" (Join-Path $r "cursor-plugin\plugin.json") (Join-Path $rootDir ".cursor-plugin\plugin.json")
        }
        "Gemini CLI" {
            Copy-OneFile "$label gemini-extension.json" (Join-Path $r "gemini-extension.json") (Join-Path $rootDir "gemini-extension.json")
        }
        { $_ -in @("GitHub Copilot","Pi") } {
            # 不通过 manifest 部署
        }
    }
}

# ════════════════════════════════════════════════════════════
# Step 2e: Copy-RootDocs
# ════════════════════════════════════════════════════════════
function Copy-RootDocs($label, $rootDir, $agentsMd, $readmeMd) {
    Copy-OneFile "$label AGENTS.md" $agentsMd (Join-Path $rootDir "AGENTS.md")
    Copy-OneFile "$label README.md" $readmeMd (Join-Path $rootDir "README.md")
}

# ════════════════════════════════════════════════════════════
# Step 2: Deploy-ToTargets（对齐 _common.sh:509-545 主驱动）
# ════════════════════════════════════════════════════════════
function Deploy-ToTargets {
    $skillsDir = Join-Path $script:Work "skills"
    $hooksDir = Join-Path $script:Work "hooks"
    $agentsMd = Join-Path $script:Work "AGENTS.md"
    $readmeMd = Join-Path $script:Work "README.md"

    $want = if ($All) { $script:AllAgentIds } elseif ($Only) { ($Only -split '[ ,]+' | Where-Object { $_ }) -join ' ' } else { $script:AgentList }
    $entries = Get-ToolRootDirs
    $entries = Filter-ToolRootDirs $entries $want
    if ($entries.Count -eq 0) { Write-Warn "按 agent filter 后无目标可部署"; return }

    Write-Step "Step 2b-pre: 清理目标 plugin 顶层散落的旧平铺技能目录..."
    foreach ($e in $entries) { Cleanup-TargetTopLevel $e.Label $e.Path }

    Write-Step "Step 2b: 复制 skills/ 到目标 skills/ 子目录..."
    foreach ($e in $entries) { Copy-Skills $e.Label $e.Path $skillsDir }

    Write-Step "Step 2c: 复制 hooks/ 到目标..."
    foreach ($e in $entries) { Copy-Hooks $e.Label $e.Path $hooksDir }

    Write-Step "Step 2d: 部署 plugin manifest..."
    foreach ($e in $entries) { Deploy-Manifest $e.Label $e.Path }

    Write-Step "Step 2e: 复制项目根文档 (AGENTS.md / README.md)..."
    foreach ($e in $entries) { Copy-RootDocs $e.Label $e.Path $agentsMd $readmeMd }
}

# ════════════════════════════════════════════════════════════
# Step 3: Install-McpPackages（对齐 _common.sh:300-372）
# ════════════════════════════════════════════════════════════
function Detect-McpExe($cmdName) {
    # Windows: 优先查 .exe / .cmd / 裸名（PATH）
    foreach ($ext in @(".exe",".cmd","")) {
        $c = if ($ext) { "$cmdName$ext" } else { $cmdName }
        $found = Get-Command $c -ErrorAction SilentlyContinue
        if ($found) { return $found.Source }
    }
    # fallback 目录（对齐 _common.sh:54-62 COMMON_MCP_FALLBACK_PATHS_WINDOWS）
    $appdata = if ($env:APPDATA) { $env:APPDATA } else { Join-Path $env:USERPROFILE "AppData\Roaming" }
    $fallbacks = @(
        "Python\Python39\Scripts","Python\Python310\Scripts","Python\Python311\Scripts",
        "Python\Python312\Scripts","Python\Python313\Scripts","Python\Python314\Scripts"
    ) | ForEach-Object { Join-Path $appdata $_ }
    $fallbacks += (Join-Path $appdata "npm")
    foreach ($p in $fallbacks) {
        foreach ($ext in @(".exe",".cmd","")) {
            $f = Join-Path $p "$cmdName$ext"
            if (Test-Path $f) { return $f }
        }
    }
    return $null
}

function Install-McpPackages {
    Write-Step "🔌 Step 3: 安装 MCP 三件套（Windows）..."
    # pip 命令探测：py -m pip > pip3 > pip
    $pipCmd = $null
    if (Get-Command py -ErrorAction SilentlyContinue) { $pipCmd = "py -m pip" }
    elseif (Get-Command pip3 -ErrorAction SilentlyContinue) { $pipCmd = "pip3" }
    elseif (Get-Command pip -ErrorAction SilentlyContinue) { $pipCmd = "pip" }

    $pkgs = @(
        @{Pkg="jcodemunch-mcp"; Cmd="jcodemunch-mcp"; IsMcp=$true}
        @{Pkg="headroom";        Cmd="headroom";        IsMcp=$false}
        @{Pkg="repomix";         Cmd="repomix";         IsMcp=$true}
    )
    foreach ($p in $pkgs) {
        # 已装检查
        $installed = $false
        foreach ($ext in @(".exe",".cmd","")) {
            if (Get-Command "$($p.Cmd)$ext" -ErrorAction SilentlyContinue) { $installed = $true; break }
        }
        if ($installed) { Write-Ok "$($p.Cmd) 已装"; continue }

        # repomix 走 npm
        if ($p.Pkg -like "*repomix*") {
            if (Get-Command npm -ErrorAction SilentlyContinue) {
                & npm install -g $p.Pkg 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) { Write-Ok "$($p.Pkg) (npm)" }
                else { Write-Warn "$($p.Pkg) npm 安装失败" }
            } else { Write-Warn "npm 未装 — 手动: npm i -g $($p.Pkg)" }
            continue
        }
        # 其余走 pip
        if (-not $pipCmd) { Write-Warn "pip 未找到，跳过 $($p.Pkg)"; continue }
        $cmdArgs = ($pipCmd -split ' ') + @("install","--user",$p.Pkg)
        & $cmdArgs[0] $cmdArgs[1..($cmdArgs.Length-1)] 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Ok "$($p.Pkg) ($pipCmd --user)" }
        else { Write-Warn "$($p.Pkg) 安装失败 — 手动: $pipCmd install --user $($p.Pkg)" }
    }
}

# ════════════════════════════════════════════════════════════
# Windows 路径 \ → /（ZCode/Cursor JSON 要求）
# ════════════════════════════════════════════════════════════
function Convert-ToForwardSlashes($p) { return ($p -replace '\\','/') }

# ════════════════════════════════════════════════════════════
# Step 4: Write-ZCodeDesktopConfig（对齐 _common.sh:376-404）
# ════════════════════════════════════════════════════════════
function Write-ZCodeDesktopConfig {
    Write-Step "⚙️  Step 4: 配置 ZCode 桌面版 MCP (~/.zcode/cli/config.json)..."
    $jcode = Detect-McpExe "jcodemunch-mcp"
    $repo = Detect-McpExe "repomix"
    if (-not $jcode -or -not $repo) {
        Write-Warn "jcodemunch/repomix 未全部找到，跳过桌面版配置写入"
        return
    }
    $jcode = Convert-ToForwardSlashes $jcode
    $repo = Convert-ToForwardSlashes $repo
    $cfg = Join-Path $env:USERPROFILE ".zcode\cli\config.json"
    New-Item -ItemType Directory -Path (Split-Path $cfg) -Force | Out-Null
    # PS 5.1 bug：python 抛异常时，stderr 被转成 RemoteException ErrorRecord，
    # `$LASTEXITCODE` 仍可能是 0。改用 try/catch 捕获 ErrorRecord。
    try {
        $out = & python (Join-Path $script:ScriptDir "scripts\merge_mcp_config.py") zcode $cfg $jcode $repo 2>&1
    } catch {
        Write-Err "合并 $cfg 失败（PS 5.1 RemoteException）"
        Write-Host (Format-PSError $_) -ForegroundColor Red
        return
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "[ZCode 桌面版 MCP] $cfg"
        [void]$script:Targets.Add("ZCode 桌面版 MCP`:$cfg")
    } else {
        Write-Err "合并 $cfg 失败（exit ${LASTEXITCODE}）: $out"
    }
}

# ════════════════════════════════════════════════════════════
# Step 5: Inject-RedLines（对齐 _common.sh:753-849）
# 9 条红线 × 7 目标文件，调 inject_rules.py 幂等合并
# ════════════════════════════════════════════════════════════
function Extract-RuleBlock($srcLines, $title, $marker) {
    # 找 begin: ^## .*🔴.*<title>
    $beginIdx = -1
    for ($i = 0; $i -lt $srcLines.Count; $i++) {
        if ($srcLines[$i] -match "^## .*🔴.*$([regex]::Escape($title))") { $beginIdx = $i; break }
    }
    if ($beginIdx -lt 0) { return $null }

    # 找 next section: 跳过 ``` 代码块（含带语言标识如 ```bash ```markdown），找下一个 ^## (两个#)
    $inCode = $false
    $nextIdx = $srcLines.Count
    for ($i = $beginIdx + 1; $i -lt $srcLines.Count; $i++) {
        if ($srcLines[$i] -match '^\s*```[a-zA-Z0-9]*\s*(<[^>]*>)?\s*$') { $inCode = -not $inCode; continue }
        if (-not $inCode -and $srcLines[$i] -match '^## ') { $nextIdx = $i; break }
    }
    $block = $srcLines[$beginIdx..($nextIdx - 1)] -join "`n"
    $wrapped = "<!-- BEGIN LOOPENGINE-MANAGED $marker -->`n$block`n<!-- END LOOPENGINE-MANAGED $marker -->"
    return $wrapped
}

function Inject-RedLines {
    Write-Step "🌐 Step 5: 注入全局红线规则..."
    $src = Join-Path $script:Work "AGENTS.md"
    if (-not (Test-Path $src)) { Write-Warn "$src 不存在，跳过"; return }

    # 9 条红线 title:marker（对齐 _common.sh:758-768）
    $rules = @(
        @{Title="用户交互红线";    Marker="INTERACTION-RULES"}
        @{Title="MCP 红线规则";    Marker="MCP-RULES"}
        @{Title="事实优先硬规则";  Marker="EVIDENCE-RULES"}
        @{Title="摘要输出红线";    Marker="SUMMARY-RULES"}
        @{Title="完成前验证红线";  Marker="VERIFICATION-RULES"}
        @{Title="进度汇报红线";    Marker="PROGRESS-RULES"}
        @{Title="Subagent 边界红线"; Marker="SUBAGENT-RULES"}
        @{Title="一致性核对红线";  Marker="CONSISTENCY-RULES"}
        @{Title="工程实践红线";    Marker="ENGINEERING-RULES"}
    )
    # 7 个目标文件（对齐 _common.sh:769-777，无 filter 全注入）
    $targets = @(
        @{Label="ZCode";          Path=(Join-Path $env:USERPROFILE ".zcode\AGENTS.md")}
        @{Label="Claude Code";    Path=(Join-Path $env:USERPROFILE ".claude\CLAUDE.md")}
        @{Label="Gemini CLI";     Path=(Join-Path $env:USERPROFILE ".gemini\GEMINI.md")}
        @{Label="Codex";          Path=(Join-Path $env:USERPROFILE ".codex\AGENTS.md")}
        @{Label="Cursor";         Path=(Join-Path $env:USERPROFILE ".cursor\rules\loopengine-interaction.mdc")}
        @{Label="GitHub Copilot"; Path=(Join-Path $env:USERPROFILE ".copilot\AGENTS.md")}
        @{Label="Pi";             Path=(Join-Path $env:USERPROFILE ".pi\AGENTS.md")}
    )

    # 读源（UTF-8 保 emoji）
    $srcLines = Get-Content $src -Encoding UTF8
    $blockDir = Join-Path $env:TEMP "loopengine-blocks-$PID"
    if (Test-Path $blockDir) { Remove-Item $blockDir -Recurse -Force }
    New-Item -ItemType Directory -Path $blockDir | Out-Null

    $extracted = 0
    foreach ($r in $rules) {
        $wrapped = Extract-RuleBlock $srcLines $r.Title $r.Marker
        if ($wrapped) {
            # UTF-8 无 BOM 写入（inject_rules.py 用 UTF-8 读）
            [System.IO.File]::WriteAllText((Join-Path $blockDir $r.Marker), $wrapped + "`n", (New-Object System.Text.UTF8Encoding $false))
            $extracted++
            Write-Ok "提取: $($r.Title) → $($r.Marker)"
        } else {
            Write-Warn "AGENTS.md 中未找到 '$($r.Title)' 章节，跳过"
        }
    }
    if ($extracted -eq 0) { Write-Err "未提取到任何规则章节，退出"; return }

    foreach ($t in $targets) {
        New-Item -ItemType Directory -Path (Split-Path $t.Path) -Force | Out-Null
        # PS 5.1：python 抛异常时 stderr 转 RemoteException，$LASTEXITCODE 可能为 0
        try {
            $out = & python (Join-Path $script:ScriptDir "scripts\inject_rules.py") $t.Path $blockDir 2>&1
        } catch {
            Write-Err "[$($t.Label) 红线] 失败（PS 5.1 RemoteException）"
            Write-Host (Format-PSError $_) -ForegroundColor Red
            continue
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "[$($t.Label) 红线] $($t.Path)"
            [void]$script:Targets.Add("$($t.Label) 红线`:$($t.Path)")
        } else {
            Write-Err "[$($t.Label) 红线] 失败（exit ${LASTEXITCODE}）: $out"
        }
    }
    Remove-Item $blockDir -Recurse -Force -ErrorAction SilentlyContinue
}

# ════════════════════════════════════════════════════════════
# Step 5.5: Deploy-CursorMcp（对齐 _common.sh:703-748 · headroom 可选）
# ════════════════════════════════════════════════════════════
function Deploy-CursorMcp {
    if ($script:AgentList -notlike "*cursor*") {
        Write-Info "跳过 Cursor MCP（detect 结果不含 cursor）"
        return
    }
    Write-Step "🎯 Step 5.5: 配置 Cursor MCP (~/.cursor/mcp.json)..."
    $jcode = Detect-McpExe "jcodemunch-mcp"
    $repo = Detect-McpExe "repomix"
    $hdrm = Detect-McpExe "headroom"

    if (-not $jcode -or -not $repo) {
        Write-Warn "jcodemunch/repomix 未找到，跳过 ~/.cursor/mcp.json 写入"
        return
    }
    if (-not $hdrm) { Write-Warn "headroom 未找到（可选）— Cursor mcp.json 将不写 headroom entry"; $hdrm = "" }

    $jcode = Convert-ToForwardSlashes $jcode
    $repo = Convert-ToForwardSlashes $repo
    if ($hdrm) { $hdrm = Convert-ToForwardSlashes $hdrm }

    $cfg = Join-Path $env:USERPROFILE ".cursor\mcp.json"
    New-Item -ItemType Directory -Path (Split-Path $cfg) -Force | Out-Null
    # PS 5.1：python 抛异常时 stderr 转 RemoteException，$LASTEXITCODE 可能为 0
    try {
        $out = & python (Join-Path $script:ScriptDir "scripts\merge_mcp_config.py") cursor $cfg $jcode $repo $hdrm 2>&1
    } catch {
        Write-Err "[Cursor MCP] 失败（PS 5.1 RemoteException）"
        Write-Host (Format-PSError $_) -ForegroundColor Red
        return
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "[Cursor MCP] $cfg"
        [void]$script:Targets.Add("Cursor MCP`:$cfg")
    } else { Write-Err "合并 $cfg 失败（exit ${LASTEXITCODE}）: $out" }
}

# ════════════════════════════════════════════════════════════
# Step 6: Deployment-Check（对齐 _common.sh:811-870）
# ════════════════════════════════════════════════════════════
function Deployment-Check {
    Write-Step "🔬 Step 6: 部署自检..."
    $skillsTotal = ($script:Targets | Where-Object { $_ -match "skills:" }).Count
    $ok1 = $skillsTotal -ge 5
    if ($ok1) { Write-Ok "至少 5 个目标的 skills 目录已部署（实际 ${skillsTotal}）" }
    else { Write-Warn "skills 目标数偏少: $skillsTotal" }

    $manifestCount = ($script:Targets | Where-Object { $_ -match "plugin\.json|marketplace\.json|gemini-extension" }).Count
    # 实际 manifest 文件数：ZCode/Claude(双)/Codex/Cursor/Gemini = 6（ZCode 内置包/CLI 缓存目录若不存在则跳过）
    $ok2 = $manifestCount -ge 6
    if ($ok2) { Write-Ok "渲染 manifest 数: $manifestCount (>=6)" }
    else { Write-Warn "manifest 数偏少: $manifestCount" }

    New-Item -ItemType Directory -Path (Split-Path $script:VersionFile) -Force | Out-Null
    [System.IO.File]::WriteAllText($script:VersionFile, $script:Version, (New-Object System.Text.UTF8Encoding $false))
    Write-Ok "写入版本号文件: $($script:VersionFile)"

    if ($ok1 -and $ok2) { Write-Ok "自检: 2 项全部通过" }
    else { Write-Warn "自检: 有项目未通过，请检查上方输出" }
}

# ════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  LoopEngine v$($script:Version) — Windows PowerShell 一键安装   ║" -ForegroundColor Cyan
Write-Host "║  自动检测平台 · skills/AGENTS.md/hooks/MCP/9 红线 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
if ($All)     { Write-Info "LE_ALL=1：强制全量部署" }
Write-Host ""

# Step 0.5: 自动感知
Write-Host "🔍 Step 0.5: AI Agent 自动感知..." -ForegroundColor White
$detected = Detect-Agents
$detectedList = if ($detected) { $detected.Split(' ') } else { @() }
if ($All) {
    $script:AgentList = $script:AllAgentIds
    Write-Info "LE_ALL=1：强制全量部署 ($script:AllAgentIds)"
} elseif ($Only) {
    $script:AgentList = ($Only -split '[ ,]+' | Where-Object { $_ }) -join ' '
    Write-Info "LE_ONLY=${Only}：指定部署 ($($script:AgentList))"
} elseif ($detectedList.Count -eq 0) {
    Write-Err "未检测到任何 AI Agent — 至少安装其中一个"
    Write-Info "推荐：$env:LE_ALL=1; .\install.ps1  强制全量部署"
    exit 1
} else {
    $script:AgentList = $detected
    Write-Ok "自动感知到 $($detectedList.Count) 个 AI Agent："
    foreach ($a in $detectedList) { Write-Host "       • $a" -ForegroundColor Cyan }
}
Write-Host ""

# Step 0: 状态显示（强制模式不等待）
Write-Host "🔍 Step 0: 状态检查..." -ForegroundColor White
Show-Status

# Step 1: clone
Clone-Repo

# Step 2: 部署
Write-Step "📦 Step 2: 部署到 AI 工具约定目录..."
Render-Plugins
Deploy-ToTargets

# Step 3-5.5: 平台步骤
Install-McpPackages
Write-ZCodeDesktopConfig
Inject-RedLines
Deploy-CursorMcp

# Step 6: 自检
Deployment-Check

# 总结
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ LoopEngine v$($script:Version) 安装完成 · 平台: windows · 部署到 $($script:Targets.Count) 个路径" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
foreach ($t in $script:Targets) {
    $parts = $t -split ':', 2
    Write-Host "  • $($parts[0]): $($parts[1])" -ForegroundColor Cyan
}

# 清理临时目录
if ($script:Work -and (Test-Path $script:Work)) {
    Remove-Item $script:Work -Recurse -Force -ErrorAction SilentlyContinue
}

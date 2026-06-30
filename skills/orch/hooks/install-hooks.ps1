# skills/orch/hooks/install-hooks.ps1
# 注册 orch session-start hook 到 Claude Code / ZCode (Windows)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginRoot = Resolve-Path (Join-Path $ScriptDir "..\..\")
$HookCmd = "`"$PluginRoot\skills\orch\hooks\orch-bootstrap.cmd`""

Write-Host "=== Installing orch v1.0.0 session-start hook (Windows) ===" -ForegroundColor Cyan

# Claude Code
$ClaudeSettings = Join-Path $env:USERPROFILE ".claude\settings.json"
if (Test-Path (Join-Path $env:USERPROFILE ".claude")) {
    if (Test-Path $ClaudeSettings) {
        Copy-Item $ClaudeSettings "$ClaudeSettings.bak.$(Get-Date -Format yyyyMMdd)"
    }

    $settings = @{
        hooks = @{
            SessionStart = @(@{
                matcher = "startup|clear|compact"
                hooks = @(@{
                    type = "command"
                    command = $HookCmd
                    async = $false
                })
            })
        }
    } | ConvertTo-Json -Depth 10

    Set-Content -Path $ClaudeSettings -Value $settings
    Write-Host "Claude Code hook registered: $ClaudeSettings" -ForegroundColor Green
} else {
    Write-Host "WARN: ~/.claude/ not found. Skipping." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Cyan
Write-Host "Restart your agent to activate orch v1.0.0."
#requires -Version 5.1
<#
  Unit test for Format-PSError helper in install.ps1
  Verifies full Python stack trace is exposed (not just first line)
  Note: keep this file ENGLISH-ONLY and no UTF-8 BOM to avoid PS 5.1
  encoding gotcha. PowerShell 5.1 misreads multi-byte UTF-8 sequences
  as Windows-1252 without BOM, corrupting the parse.
#>

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot

# 1. Extract Format-PSError function from install.ps1 (line scan)
$installPs1 = Join-Path $projectRoot 'install.ps1'
$lines = Get-Content $installPs1

$startIdx = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^function Format-PSError') { $startIdx = $i; break }
}
if ($startIdx -lt 0) {
    Write-Host "FAIL: cannot find Format-PSError in install.ps1" -ForegroundColor Red
    exit 1
}

$endIdx = $startIdx + 1
while ($endIdx -lt $lines.Count) {
    $line = $lines[$endIdx]
    if ($line -match '^function ' -and $endIdx -gt $startIdx) { break }
    if ($line -match '^# ' -and $endIdx -gt $startIdx + 1) { break }
    $endIdx++
}
$funcSrc = $lines[$startIdx..($endIdx - 1)] -join "`n"
Invoke-Expression $funcSrc

# Test 1: multi-line Message (Python traceback style)
Write-Host "Test 1: multi-line Message (Python traceback)..." -ForegroundColor Cyan
$pythonLikeMsg = "Traceback (most recent call last):`n  File ""scripts\merge_mcp_config.py"", line 42, in <module>`n    main()`nTypeError: expected str, got NoneType"
$syntheticError = New-Object System.Management.Automation.RuntimeException($pythonLikeMsg)
$rec = New-Object System.Management.Automation.ErrorRecord($syntheticError, 'PythonHelperFailed', 'NotSpecified', $null)
$rec = $rec | Add-Member -Force -NotePropertyName ScriptStackTrace -NotePropertyValue "at <ScriptBlock>, C:\install.ps1: line 460" -PassThru

$result = Format-PSError $rec

Write-Host "--- output ---"
Write-Host $result
Write-Host "--- end ---"

$failures = @()
if ($result -notmatch "Traceback") { $failures += "missing 'Traceback'" }
if ($result -notmatch "TypeError") { $failures += "missing 'TypeError'" }
if ($result -notmatch "line 42") { $failures += "missing 'line 42'" }
if ($result -notmatch "RuntimeException") { $failures += "missing ExceptionType" }
if (-not ($result -match "ScriptStackTrace" -or $result -match "line 460")) { $failures += "missing ScriptStackTrace" }

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "FAIL: Test 1" -ForegroundColor Red
    foreach ($f in $failures) { Write-Host "  - $f" -ForegroundColor Red }
    exit 1
}
Write-Host "PASS: Test 1 - full traceback exposed" -ForegroundColor Green

# Test 2: single-line Message (regression)
Write-Host ""
Write-Host "Test 2: single-line Message (regression)..." -ForegroundColor Cyan
$simpleError = New-Object System.Management.Automation.RuntimeException("File not found: C:\missing.json")
$rec2 = New-Object System.Management.Automation.ErrorRecord($simpleError, 'IO', 'NotSpecified', $null)
$result2 = Format-PSError $rec2
if ($result2 -notmatch "File not found") {
    Write-Host "FAIL: single-line message lost" -ForegroundColor Red
    exit 1
}
Write-Host "PASS: Test 2 - single-line preserved" -ForegroundColor Green

# Test 3: contrast old behavior — simulate PS 5.1 RemoteException truncation
# Real PS 5.1 RemoteException only exposes the FIRST LINE of stderr as `.Message`.
# Simulate that by passing a single-line message that matches what user reported.
Write-Host ""
Write-Host "Test 3: simulate PS 5.1 RemoteException (first-line-only Message)..." -ForegroundColor Cyan
$truncatedMsg = "Traceback (most recent call last):"  # exactly what the user saw in the log
$truncError = New-Object System.Management.Automation.RuntimeException($truncatedMsg)
$rec3 = New-Object System.Management.Automation.ErrorRecord($truncError, 'PythonHelperFailed', 'NotSpecified', $null)
$rec3 = $rec3 | Add-Member -Force -NotePropertyName ScriptStackTrace -NotePropertyValue "at Install-McpConfig, C:\install.ps1: line 460`nat <ScriptBlock>, C:\install.ps1: line 460" -PassThru

# Old behavior would have shown ONLY the truncated Message
$oldBehavior = $rec3.Exception.Message
Write-Host "  old output (only Message): '$oldBehavior'"

# New behavior: Format-PSError should still recover info from ScriptStackTrace
$newBehavior = Format-PSError $rec3
Write-Host "  new output (Format-PSError):"
Write-Host $newBehavior
if (-not ($newBehavior -match "at Install-McpConfig" -or $newBehavior -match "line 460")) {
    Write-Host "FAIL: Format-PSError did not expose script stack info" -ForegroundColor Red
    exit 1
}
Write-Host "PASS: Test 3 - new format recovers info even when Message is truncated" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "ALL TESTS PASSED - Format-PSError v1.3.2 fix verified" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

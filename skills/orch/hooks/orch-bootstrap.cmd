@echo off
REM skills/orch/hooks/orch-bootstrap.cmd
REM session-start bootstrap - Windows 版本（兼容 CMD）

setlocal enabledelayedexpansion

REM 定位插件根目录
set SCRIPT_DIR=%~dp0
set PLUGIN_ROOT=%SCRIPT_DIR%..\..

REM 读取 orch/SKILL.md
set SKILL_FILE=%PLUGIN_ROOT%\skills\orch\SKILL.md
if not exist "%SKILL_FILE%" (
  echo ERROR: orch/SKILL.md not found at %SKILL_FILE% 1>&2
  exit /b 1
)

REM 简化为顶层 additionalContext（兼容各平台）
echo {"additionalContext": "orch v1.0.0 installed (multi-skill orchestrator). See skills/orch/SKILL.md. For single-skill tasks, native description matching handles it. For multi-skill tasks, user must explicitly type /orch."}

exit /b 0
@echo off
REM skills/skill-hub/hooks/skillhub-bootstrap.cmd
REM v6.7 session-start bootstrap - Windows 版本（兼容 CMD）

setlocal enabledelayedexpansion

REM 定位插件根目录
set SCRIPT_DIR=%~dp0
set PLUGIN_ROOT=%SCRIPT_DIR%..\..

REM 读取 skill-hub/SKILL.md
set SKILL_FILE=%PLUGIN_ROOT%\skills\skill-hub\SKILL.md
if not exist "%SKILL_FILE%" (
  echo ERROR: skill-hub/SKILL.md not found at %SKILL_FILE% 1>&2
  exit /b 1
)

REM 简化为顶层 additionalContext（兼容各平台）
echo {"additionalContext": "skill-hub v6.7.0-alpha installed. See skills/skill-hub/SKILL.md for routing protocol."}

exit /b 0

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
echo {"additionalContext": "orch v2 installed. It is a natural-language-first, family-first, rule-first multi-skill orchestrator. Use native description matching for single-skill tasks; use orch when the goal clearly spans multiple complementary skills."}

exit /b 0
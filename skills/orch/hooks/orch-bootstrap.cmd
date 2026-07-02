@echo off
REM skills/orch/hooks/orch-bootstrap.cmd
REM session-start bootstrap - Windows 版本（兼容 CMD）

setlocal enabledelayedexpansion

REM 定位插件根目录
set SCRIPT_DIR=%~dp0
set PLUGIN_ROOT=%SCRIPT_DIR%..\..

REM 运行时注入提示（Windows 版本保留简化摘要）
echo {"additionalContext": "orch v2 installed. Runtime references live under skills/orch/references (intent schema, capability registry, dag rules, executor contracts). Use native description matching for single-skill tasks; use orch when the goal clearly spans multiple complementary skills."}

exit /b 0
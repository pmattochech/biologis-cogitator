@echo off
REM biologis-cogitator on Windows
REM   Default: native Python + Textual (recommended)
REM   WSL:     run.cmd --wsl [args...]   (full Linux / GTK path)
REM            or set BIOLOGIS_USE_WSL=1
setlocal EnableExtensions
set "DIR=%~dp0"

if /I "%~1"=="--wsl" (
  set "BIOLOGIS_USE_WSL=1"
  shift
)
if /I "%BIOLOGIS_USE_WSL%"=="1" goto :wsl

where py >nul 2>&1
if %ERRORLEVEL%==0 goto :native
where python >nul 2>&1
if %ERRORLEVEL%==0 goto :native

echo Python not found on PATH — trying WSL...
goto :wsl

:native
call "%DIR%bin\biologis-cogitator.cmd" %*
exit /b %ERRORLEVEL%

:wsl
REM PowerShell helper: any drive letter + full argv (no 9-arg cap)
powershell -NoProfile -ExecutionPolicy Bypass -File "%DIR%scripts\wsl-launch.ps1" %*
exit /b %ERRORLEVEL%

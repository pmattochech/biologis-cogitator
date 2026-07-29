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
set "WSLDIR=%DIR:\=/%"
set "WSLDIR=/mnt/c%WSLDIR:~2%"
wsl -e bash -lc "cd '%WSLDIR%' && chmod +x run bin/cli.py bin/biologis-cogitator 2>/dev/null; ./bin/biologis-cogitator %1 %2 %3 %4 %5 %6 %7 %8 %9"
exit /b %ERRORLEVEL%

@echo off
REM Force WSL for biologis-cogitator on Windows
setlocal
set "DIR=%~dp0"
set "DIR=%DIR:\=/%"
set "DIR=/mnt/c%DIR:~2%"
wsl -e bash -lc "cd '%DIR%' && chmod +x run bin/cli.py 2>/dev/null; ./run %*"

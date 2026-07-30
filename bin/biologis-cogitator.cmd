@echo off
REM Native Windows entry for biologis-cogitator (Textual TUI / CLI).
REM GTK host window is Linux-only; this always runs in the terminal.
setlocal EnableExtensions
set "BIOLOGIS_NO_WINDOW=1"

set "HERE=%~dp0"
REM Launcher lives in bin\ — repo root is parent
for %%I in ("%HERE%..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo error: Python 3 not found. Install from https://www.python.org/downloads/
    echo        Enable "Add python.exe to PATH" during setup.
    exit /b 1
  )
  set "PY=python"
)

REM Pull latest from origin before launching (clean install checkouts only).
REM If BIOLOGIS_REF is unset, honor local config git_ref for this update step
REM so older env-only updaters still follow the Build channel preference.
%PY% -c "import os,sys; sys.path.insert(0,r'%ROOT%');\
cfg=os.path.join(os.environ.get('APPDATA',''),'biologis-cogitator','config.yaml');\
ref=os.environ.get('BIOLOGIS_REF','').strip();\
\
def _cfg_ref(p):\
  try:\
   import yaml;\
   d=yaml.safe_load(open(p,encoding='utf-8')) or {};\
   return str(d.get('git_ref') or '').strip()\
  except Exception:\
   return ''\
\
ref=ref or (_cfg_ref(cfg) if cfg and os.path.isfile(cfg) else '');\
\
if ref: os.environ['BIOLOGIS_REF']=ref;\
from lib.update import apply_startup_update, update_ref, ref_source;\
print(f'[biologis-cogitator] tracking {update_ref()} ({ref_source()})', flush=True);\
apply_startup_update(verbose=True)"

if "%~1"=="" goto :default
if /I "%~1"=="setup" goto :setup
if /I "%~1"=="wizard" goto :wizard
if /I "%~1"=="window" (
  echo note: GTK window is not available on native Windows.
  echo       Use Windows Terminal, or WSL: run.cmd --wsl
  shift
  goto :wizard_args
)

%PY% "%ROOT%\bin\cli.py" %*
exit /b %ERRORLEVEL%

:setup
%PY% "%ROOT%\bin\cli.py" setup
exit /b %ERRORLEVEL%

:wizard
shift
:wizard_args
call :ensure_setup
if errorlevel 1 exit /b 1
%PY% "%ROOT%\bin\cli.py" wizard %*
exit /b %ERRORLEVEL%

:default
call :ensure_setup
if errorlevel 1 exit /b 1
%PY% "%ROOT%\bin\cli.py" wizard
exit /b %ERRORLEVEL%

:ensure_setup
%PY% -c "import sys; sys.path.insert(0, r'%ROOT%'); from lib.config import is_configured; raise SystemExit(0 if is_configured() else 1)"
if errorlevel 1 (
  echo First run: opening setup to choose results and scratch folders...
  %PY% "%ROOT%\bin\cli.py" setup
  if errorlevel 1 (
    echo error: setup did not complete; re-run: biologis-cogitator setup
    exit /b 1
  )
)
exit /b 0

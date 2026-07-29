#Requires -Version 5.1
<#
.SYNOPSIS
  Install Biologis Cogitator on Windows (native Python + Textual TUI).

.DESCRIPTION
  Checks Python/pip, installs requirements, puts launchers on the user PATH,
  optionally runs first-run setup. The GTK Mechanicus window is Linux/WSL only;
  on Windows the cogitator runs in Windows Terminal / console.

.PARAMETER Yes
  Install missing pip packages without prompting.

.PARAMETER SkipSetup
  Do not open the folder-picker setup at the end.
#>
[CmdletBinding()]
param(
    [switch]$Yes,
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path (Join-Path $Root "bin\cli.py"))) {
    throw "Cannot find repo root next to install.ps1 ($Root)"
}

Write-Host "==> Biologis Cogitator installer (Windows)"
Write-Host ""

function Find-Python {
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { return @("py", "-3") }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return @("python") }
    $cmd = Get-Command python3 -ErrorAction SilentlyContinue
    if ($cmd) { return @("python3") }
    return $null
}

function Invoke-Python {
    param(
        [Parameter(Mandatory)][string[]]$Py,
        [Parameter(Mandatory)][string[]]$PyArgs
    )
    if ($Py.Count -gt 1) {
        & $Py[0] @($Py[1..($Py.Count - 1)] + $PyArgs)
    } else {
        & $Py[0] @PyArgs
    }
}

Write-Host "==> Checking dependencies..."
$Py = Find-Python
if (-not $Py) {
    Write-Host "  FAIL  Python 3 not found on PATH"
    Write-Host "        Install from https://www.python.org/downloads/"
    Write-Host "        Enable 'Add python.exe to PATH', then re-open this terminal."
    exit 1
}
$ver = if ($Py.Count -gt 1) {
    & $Py[0] @($Py[1..($Py.Count - 1)] + @("--version")) 2>&1
} else {
    & $Py[0] --version 2>&1
}
Write-Host "  OK    $ver"

try {
    Invoke-Python -Py $Py -PyArgs @("-m", "pip", "--version") | Out-Null
    Write-Host "  OK    pip"
} catch {
    Write-Host "  FAIL  pip not available (python -m pip)"
    exit 1
}

$missing = @()
foreach ($mod in @("yaml", "textual")) {
    $code = "import $mod"
    if ($mod -eq "yaml") { $code = "import yaml" }
    try {
        Invoke-Python -Py $Py -PyArgs @("-c", $code) | Out-Null
        Write-Host "  OK    $mod"
    } catch {
        Write-Host "  MISS  $mod"
        $missing += $mod
    }
}

try {
    Invoke-Python -Py $Py -PyArgs @("-c", "import tkinter") | Out-Null
    Write-Host "  OK    tkinter"
} catch {
    Write-Host "  WARN  tkinter missing (folder picker needs it; setup can use CLI prompts)"
}

if ($missing.Count -gt 0) {
    $req = Join-Path $Root "requirements.txt"
    Write-Host ""
    Write-Host "Missing Python packages. Installing from requirements.txt..."
    if (-not $Yes) {
        $ans = Read-Host "Install now with pip? [Y/n]"
        if ($ans -and $ans -notmatch '^[Yy]') {
            Write-Host "Aborted."
            exit 1
        }
    }
    Invoke-Python -Py $Py -PyArgs @("-m", "pip", "install", "-r", $req)
    try {
        Invoke-Python -Py $Py -PyArgs @("-c", "import yaml, textual") | Out-Null
    } catch {
        Write-Host "FAIL: PyYAML/textual still missing after pip install"
        exit 1
    }
    Write-Host "  OK    PyYAML + textual (installed)"
}

Write-Host ""
$Bin = Join-Path $env:LOCALAPPDATA "biologis-cogitator\bin"
New-Item -ItemType Directory -Force -Path $Bin | Out-Null

$launcher = Join-Path $Root "bin\biologis-cogitator.cmd"
foreach ($name in @("biologis-cogitator.cmd", "cogitator.cmd", "init-cogitator.cmd")) {
    $dest = Join-Path $Bin $name
    # Thin wrapper so PATH entries survive repo moves only if re-installed;
    # bake absolute path to the real launcher.
    @"
@echo off
call "$launcher" %*
"@ | Set-Content -Path $dest -Encoding ASCII
    Write-Host "  linked $dest"
}

# Ensure user PATH contains Bin
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }
$parts = $userPath -split ";" | Where-Object { $_ -and $_.Trim() -ne "" }
if ($parts -notcontains $Bin) {
    $newPath = if ($userPath.Trim().EndsWith(";") -or -not $userPath.Trim()) {
        "$userPath$Bin"
    } else {
        "$userPath;$Bin"
    }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$Bin;$env:Path"
    Write-Host "==> Added to user PATH: $Bin"
    Write-Host "    Open a new terminal for PATH changes to apply everywhere."
} else {
    Write-Host "==> PATH already includes $Bin"
    if ($env:Path -notlike "*$Bin*") {
        $env:Path = "$Bin;$env:Path"
    }
}

# Optional Start Menu shortcut
try {
    $programs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
    New-Item -ItemType Directory -Force -Path $programs | Out-Null
    $lnkPath = Join-Path $programs "Biologis Cogitator.lnk"
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($lnkPath)
    $sc.TargetPath = "cmd.exe"
    $sc.Arguments = "/k `"$launcher`""
    $sc.WorkingDirectory = $Root
    $sc.WindowStyle = 1
    $sc.Description = "Biologis Cogitator — Magos mesh workshop"
    $icon = Join-Path $Root "assets\app-icon.ico"
    if (-not (Test-Path $icon)) {
        $icon = Join-Path $Root "assets\app-icon.png"
    }
    if (Test-Path $icon) { $sc.IconLocation = $icon }
    $sc.Save()
    Write-Host "==> Start Menu shortcut → $lnkPath"
} catch {
    Write-Host "  (skip Start Menu shortcut: $_)"
}

Write-Host ""
if ($SkipSetup) {
    Write-Host "Skipping setup (-SkipSetup). Run later: biologis-cogitator setup"
} else {
    Write-Host "==> Opening setup (choose results + scratch folders)..."
    try {
        Invoke-Python -Py $Py -PyArgs @((Join-Path $Root "bin\cli.py"), "setup")
    } catch {
        Write-Host "Setup was cancelled or failed. You can re-run: biologis-cogitator setup"
    }
}

Write-Host ""
Write-Host "Ready."
Write-Host "  Terminal:  biologis-cogitator"
Write-Host "  Also:      cogitator / init-cogitator"
Write-Host "  Reconfigure folders: biologis-cogitator setup"
Write-Host "  Note: GTK Mechanicus window is Linux/WSL only; Windows uses the console TUI."
Write-Host "  Tip: run inside Windows Terminal for best Textual colors."

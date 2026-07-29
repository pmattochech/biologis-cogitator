#Requires -Version 5.1
<#
.SYNOPSIS
  One-shot public install on Windows — clone (or update) then run install.ps1.

.EXAMPLE
  irm https://raw.githubusercontent.com/pmattochech/biologis-cogitator/master/scripts/remote-install.ps1 | iex

.EXAMPLE
  $env:BIOLOGIS_HOME = "$env:USERPROFILE\src\biologis-cogitator"
  irm https://raw.githubusercontent.com/pmattochech/biologis-cogitator/master/scripts/remote-install.ps1 | iex
#>
$ErrorActionPreference = "Stop"

$Repo = if ($env:BIOLOGIS_REPO) { $env:BIOLOGIS_REPO } else { "https://github.com/pmattochech/biologis-cogitator.git" }
$Ref = if ($env:BIOLOGIS_REF) { $env:BIOLOGIS_REF } else { "master" }
$Dest = if ($env:BIOLOGIS_HOME) {
    $env:BIOLOGIS_HOME
} else {
    Join-Path $env:LOCALAPPDATA "biologis-cogitator\src"
}

Write-Host "==> Biologis Cogitator — remote install (Windows)"
Write-Host "    repo: $Repo"
Write-Host "    ref:  $Ref"
Write-Host "    dest: $Dest"
Write-Host ""

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required. Install Git for Windows: https://git-scm.com/download/win"
}

$parent = Split-Path -Parent $Dest
New-Item -ItemType Directory -Force -Path $parent | Out-Null

if (Test-Path (Join-Path $Dest ".git")) {
    Write-Host "==> Updating existing checkout..."
    Push-Location $Dest
    try {
        git remote set-url origin $Repo 2>$null
        git fetch --depth 1 origin $Ref
        git checkout -f -B "install-$Ref" FETCH_HEAD
    } finally {
        Pop-Location
    }
} elseif (Test-Path $Dest) {
    throw "$Dest exists but is not a git checkout. Move it aside or set BIOLOGIS_HOME."
} else {
    Write-Host "==> Cloning..."
    git clone --depth 1 --branch $Ref $Repo $Dest
}

$install = Join-Path $Dest "install.ps1"
if (-not (Test-Path $install)) {
    throw "install.ps1 missing in $Dest — is BIOLOGIS_REF correct?"
}

$args = @("-Yes")
if ($env:BIOLOGIS_NO_SETUP -eq "1") { $args += "-SkipSetup" }

& $install @args

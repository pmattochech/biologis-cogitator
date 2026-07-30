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
$AssumeYes = ($env:BIOLOGIS_ASSUME_YES -eq "1")

Write-Host "==> Biologis Cogitator — remote install (Windows)"
Write-Host "    repo: $Repo"
Write-Host "    ref:  $Ref"
Write-Host "    dest: $Dest"
Write-Host ""
Write-Host "WARNING: This installer downloads and executes code from the network,"
Write-Host "         then may run pip install. Prefer a verified clone when you can:"
Write-Host "           git clone $Repo"
Write-Host "           cd biologis-cogitator; .\install.ps1"
Write-Host "         Pin a release tag with `$env:BIOLOGIS_REF='<tag>' when available."
Write-Host ""

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required. Install Git for Windows: https://git-scm.com/download/win"
}

$parent = Split-Path -Parent $Dest
New-Item -ItemType Directory -Force -Path $parent | Out-Null

$isUpdate = $false
if (Test-Path (Join-Path $Dest ".git")) {
    $isUpdate = $true
    Write-Host "==> Updating existing checkout..."
    Push-Location $Dest
    try {
        $old = (git rev-parse --short HEAD 2>$null)
        git remote set-url origin $Repo 2>$null
        git fetch --depth 1 origin $Ref
        $new = (git rev-parse --short FETCH_HEAD 2>$null)
        Write-Host "    current: $old"
        Write-Host "    fetch:   $new ($Ref)"
        if (-not $AssumeYes) {
            $ans = Read-Host "Continue update and re-run installer? [y/N]"
            if ($ans -notmatch '^[Yy]') {
                Write-Host "Aborted."
                exit 1
            }
        }
        # Local tracking branch cannot contain '/'; sanitize for feature branches.
        $localBranch = "install-" + ($Ref -replace '/', '-')
        git checkout -f -B $localBranch FETCH_HEAD
    } finally {
        Pop-Location
    }
} elseif (Test-Path $Dest) {
    throw "$Dest exists but is not a git checkout. Move it aside or set BIOLOGIS_HOME."
} else {
    Write-Host "==> Cloning..."
    git clone --depth 1 --branch $Ref $Repo $Dest
    $head = git -C $Dest rev-parse --short HEAD 2>$null
    Write-Host "    HEAD: $head"
}

$install = Join-Path $Dest "install.ps1"
if (-not (Test-Path $install)) {
    throw "install.ps1 missing in $Dest — is BIOLOGIS_REF correct?"
}

$installArgs = @()
if ((-not $isUpdate) -or $AssumeYes) {
    $installArgs += "-Yes"
}
if ($env:BIOLOGIS_NO_SETUP -eq "1") { $installArgs += "-SkipSetup" }

Write-Host "==> Running install.ps1 $($installArgs -join ' ')"
& $install @installArgs

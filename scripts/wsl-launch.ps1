# Launch biologis-cogitator inside WSL from a Windows checkout (any drive letter).
# Called by run.cmd --wsl. Forwards all remaining arguments intact.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$LaunchArgs
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $Root "bin\biologis-cogitator"))) {
    throw "biologis-cogitator root not found near scripts\wsl-launch.ps1"
}

function ConvertTo-BashSingleQuoted([string]$s) {
    return "'" + ($s -replace "'", "'\''") + "'"
}

# Prefer wsl --cd with the Windows path (works for D:, E:, etc. on modern WSL).
$quotedArgs = @($LaunchArgs | ForEach-Object { ConvertTo-BashSingleQuoted $_ }) -join " "
$inner = "chmod +x run bin/cli.py bin/biologis-cogitator 2>/dev/null; exec ./bin/biologis-cogitator $quotedArgs"

$wslArgs = @(
    "--cd", $Root,
    "-e", "bash", "-lc", $inner
)
& wsl @wslArgs
exit $LASTEXITCODE

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepackerDir = Split-Path -Parent $ScriptDir
$Repacker = Join-Path $RepackerDir "repacker.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $Repacker --interactive
    Read-Host "Press Enter to close"
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $Repacker --interactive
    Read-Host "Press Enter to close"
    exit $LASTEXITCODE
}

Write-Host "Python 3 is required. Install it from https://www.python.org/downloads/windows/"
Read-Host "Press Enter to close"
exit 1

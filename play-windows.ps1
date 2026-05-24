$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $ScriptDir "dawert-launcher.conf"

function Get-SavedLanguage {
    if (Test-Path $ConfigFile) {
        foreach ($Line in Get-Content $ConfigFile) {
            if ($Line -match "^language=(.+)$") {
                return $Matches[1].Trim()
            }
        }
    }
    return ""
}

function Save-Language {
    param([string]$Language)
    Set-Content -Path $ConfigFile -Value "language=$Language" -Encoding ASCII
}

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    return $null
}

function Test-GameDir {
    param([string]$Path)
    return (
        $Path -and
        (Test-Path (Join-Path $Path "Data")) -and
        (Test-Path (Join-Path $Path "Launcher.exe")) -and
        (Test-Path (Join-Path $Path "MP_x64\London2038_dx9_x64.exe"))
    )
}

function Find-GameDir {
    $Candidates = @()
    if ($env:GAME_DIR) { $Candidates += $env:GAME_DIR }
    if ($env:HELLGATE_DIR) { $Candidates += $env:HELLGATE_DIR }
    $Candidates += @(
        (Join-Path $ScriptDir "Hellgate London"),
        (Join-Path $ScriptDir "London2038"),
        (Join-Path (Split-Path -Parent $ScriptDir) "Hellgate London"),
        (Join-Path (Split-Path -Parent $ScriptDir) "London2038"),
        "C:\Program Files\Flagship Studios\Hellgate London",
        "C:\Program Files (x86)\Flagship Studios\Hellgate London",
        "C:\London2038",
        "D:\Program Files\Flagship Studios\Hellgate London",
        "D:\Program Files (x86)\Flagship Studios\Hellgate London",
        "D:\London2038"
    )

    foreach ($Candidate in $Candidates) {
        if (Test-GameDir $Candidate) {
            return $Candidate
        }
    }
    return $null
}

function Run-Python {
    param([string[]]$Python, [string[]]$Arguments)
    if ($Python.Count -gt 1) {
        $PythonArgs = $Python[1..($Python.Count - 1)]
    } else {
        $PythonArgs = @()
    }
    & $Python[0] @PythonArgs @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "Dawert direct play launcher"
Write-Host "==========================="
Write-Host "Normal play bypasses Launcher.exe so it cannot overwrite localized archives."
Write-Host ""

$Python = Find-Python
if ($null -eq $Python) {
    Write-Host "Python 3 is required. Run setup-windows.bat first."
    Read-Host "Press Enter to close"
    exit 1
}

$GameDir = Find-GameDir
if (-not $GameDir) {
    $GameDir = Read-Host "Hellgate London folder containing Data"
}
if (-not (Test-GameDir $GameDir)) {
    Write-Host "Invalid game folder or missing MP_x64\London2038_dx9_x64.exe:"
    Write-Host "  $GameDir"
    Read-Host "Press Enter to close"
    exit 1
}

$SavedLanguage = Get-SavedLanguage
if ([string]::IsNullOrWhiteSpace($SavedLanguage)) {
    do {
        $Language = Read-Host "Language to apply before launch"
    } while ([string]::IsNullOrWhiteSpace($Language))
} else {
    $Language = Read-Host "Language to apply before launch [$SavedLanguage]"
    if ([string]::IsNullOrWhiteSpace($Language)) {
        $Language = $SavedLanguage
    }
}
Save-Language $Language

Write-Host ""
Write-Host "Mode:"
Write-Host "  1. Play now - repack language and start game directly"
Write-Host "  2. Official checksum update - verify/download official files, then repack again"
$Mode = Read-Host "Choose [1]"
if ([string]::IsNullOrWhiteSpace($Mode)) {
    $Mode = "1"
}

if ($Mode -eq "2") {
    Write-Host ""
    Write-Host "Running official checksum updater..."
    Run-Python $Python @(
        (Join-Path $ScriptDir "repacker.py"),
        "--game-dir", $GameDir,
        "--action", "checksum-update",
        "--language", $Language,
        "--quiet-decrypt-log"
    )

    $Continue = Read-Host "Start the game directly now? [Y/n]"
    if ($Continue -match "^[Nn]") {
        Write-Host "Done. Run play-windows.bat when you want to play with translation."
        Read-Host "Press Enter to close"
        exit 0
    }
    $SkipRepack = $true
}

if (-not $SkipRepack) {
    Write-Host ""
    Write-Host "Applying language repack: $Language"
    Run-Python $Python @(
        (Join-Path $ScriptDir "repacker.py"),
        "--game-dir", $GameDir,
        "--language", $Language,
        "--exclude", "none",
        "--quiet-decrypt-log"
    )
}

$Exe = Join-Path $GameDir "MP_x64\London2038_dx9_x64.exe"
$WorkDir = Split-Path -Parent $Exe
Write-Host ""
Write-Host "Starting game directly:"
Write-Host "  $Exe"
Start-Process -FilePath $Exe -WorkingDirectory $WorkDir
Write-Host "Done. If you need official updates, run update-windows.bat or choose mode 2 here."
Read-Host "Press Enter to close"

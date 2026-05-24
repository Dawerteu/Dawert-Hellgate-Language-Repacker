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
        (Test-Path (Join-Path $Path "Launcher.exe"))
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
        throw "Command failed: $($Python -join ' ') $($Arguments -join ' ')"
    }
}

Write-Host "Dawert official updater"
Write-Host "======================="
Write-Host "This verifies official checksums, downloads official changed files, refreshes backup, then can reinstall language."
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
    Write-Host "Invalid game folder or missing Launcher.exe:"
    Write-Host "  $GameDir"
    Read-Host "Press Enter to close"
    exit 1
}

$SavedLanguage = Get-SavedLanguage
if ([string]::IsNullOrWhiteSpace($SavedLanguage)) {
    do {
        $Language = Read-Host "Language to install after update"
    } while ([string]::IsNullOrWhiteSpace($Language))
} else {
    $Language = Read-Host "Language to install after update [$SavedLanguage]"
    if ([string]::IsNullOrWhiteSpace($Language)) {
        $Language = $SavedLanguage
    }
}
Save-Language $Language

Write-Host ""
Write-Host "Running checksum updater..."
Run-Python $Python @(
    (Join-Path $ScriptDir "repacker.py"),
    "--game-dir", $GameDir,
    "--action", "checksum-update",
    "--language", $Language,
    "--quiet-decrypt-log"
)

Write-Host ""
Write-Host "Done. For normal play, use play-windows.bat."
Read-Host "Press Enter to close"

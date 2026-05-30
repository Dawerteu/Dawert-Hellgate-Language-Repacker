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

function Get-InstalledLanguage {
    param([string]$GameDir)
    $File = Join-Path $GameDir "Data\dawertrepacker\installed-language.txt"
    if (Test-Path $File) {
        $Value = (Get-Content $File -TotalCount 1).Trim()
        if (-not [string]::IsNullOrWhiteSpace($Value)) {
            return $Value
        }
    }
    return ""
}

function Save-Settings {
    param([string]$Language)
    Set-Content -Path $ConfigFile -Value @(
        "language=$Language"
    ) -Encoding ASCII
}

function Test-GameDir {
    param([string]$Path)
    return (
        $Path -and
        (Test-Path (Join-Path $Path "Data")) -and
        (Test-Path (Join-Path $Path "Launcher.exe")) -and
        (Find-GameExe $Path)
    )
}

function Find-GameExe {
    param([string]$GameDir)
    $Candidates = @(
        (Join-Path $GameDir "MP_x64\London2038_dx9_x64.exe"),
        (Join-Path $GameDir "MP_x86\London2038_dx9_x86.exe")
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Path $Candidate) {
            return $Candidate
        }
    }
    return $null
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

Write-Host "Dawert direct play launcher"
Write-Host "==========================="
Write-Host "Normal play bypasses Launcher.exe so it cannot overwrite localized archives."
Write-Host ""

$GameDir = Find-GameDir
if (-not $GameDir) {
    $GameDir = Read-Host "Hellgate London folder containing Data"
}
if (-not (Test-GameDir $GameDir)) {
    Write-Host "Invalid game folder or missing Launcher.exe / London2038 DX9 executable:"
    Write-Host "  $GameDir"
    Read-Host "Press Enter to close"
    exit 1
}

$SavedLanguage = Get-SavedLanguage
if ([string]::IsNullOrWhiteSpace($SavedLanguage)) {
    $SavedLanguage = Get-InstalledLanguage $GameDir
    if (-not [string]::IsNullOrWhiteSpace($SavedLanguage)) {
        Write-Host "Found installed language from game data: $SavedLanguage"
    }
}
if ([string]::IsNullOrWhiteSpace($SavedLanguage)) {
    Write-Host "No installed language is saved for direct play."
    Write-Host "Install a language first with start-windows.bat or the repacker menu."
    Read-Host "Press Enter to close"
    exit 1
}
$Language = $SavedLanguage
Save-Settings $Language

$Exe = Find-GameExe $GameDir
if (-not $Exe) {
    Write-Host "No London2038 game executable found."
    Read-Host "Press Enter to close"
    exit 1
}
$WorkDir = Split-Path -Parent $Exe
Write-Host ""
Write-Host "Starting game directly:"
Write-Host "  $Exe"
Start-Process -FilePath $Exe -WorkingDirectory $WorkDir
Write-Host "Done. If you need official updates, run update-windows.bat or menu option 12."
Read-Host "Press Enter to close"

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepackerDir = Split-Path -Parent $ScriptDir
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
        (Join-Path (Split-Path -Parent $RepackerDir) "london2038\wineprefix\drive_c\Program Files\Flagship Studios\Hellgate London"),
        (Join-Path (Split-Path -Parent $RepackerDir) "london2038\wineprefix\drive_c\London2038"),
        (Join-Path $RepackerDir "london2038\wineprefix\drive_c\Program Files\Flagship Studios\Hellgate London"),
        (Join-Path $RepackerDir "london2038\wineprefix\drive_c\London2038"),
        (Join-Path $RepackerDir "Hellgate London"),
        (Join-Path $RepackerDir "London2038"),
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
    return Find-GameDirByScan
}

function Find-GameDirByScan {
    $Roots = @(
        (Split-Path -Parent $RepackerDir),
        $RepackerDir,
        (Get-Location).Path
    )
    if ($env:LOCALAPPDATA) {
        $Roots += (Join-Path $env:LOCALAPPDATA "london2038")
    }
    if ($env:APPDATA) {
        $Roots += (Join-Path $env:APPDATA "london2038")
    }

    foreach ($Root in $Roots) {
        if (-not $Root -or -not (Test-Path $Root)) {
            continue
        }
        $Launchers = @(Get-ChildItem -Path $Root -Filter "Launcher.exe" -File -Recurse -Depth 8 -ErrorAction SilentlyContinue)
        foreach ($Launcher in $Launchers) {
            $Candidate = $Launcher.DirectoryName
            if (Test-GameDir $Candidate) {
                return $Candidate
            }
        }
    }
    return $null
}

function Resolve-GameDirInput {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    $Value = $Path.Trim().Trim('"').Trim("'")
    try {
        if (Test-Path -LiteralPath $Value) {
            $Value = (Resolve-Path -LiteralPath $Value -ErrorAction Stop).Path
        }
    } catch {
    }

    if (Test-Path -LiteralPath $Value -PathType Leaf) {
        $Value = Split-Path -Parent $Value
    }

    $Current = $Value
    while (-not [string]::IsNullOrWhiteSpace($Current)) {
        if (Test-GameDir $Current) {
            return $Current
        }
        $Parent = Split-Path -Parent $Current
        if ([string]::IsNullOrWhiteSpace($Parent) -or $Parent -eq $Current) {
            break
        }
        $Current = $Parent
    }

    if (Test-Path -LiteralPath $Value -PathType Container) {
        $Launchers = @(Get-ChildItem -Path $Value -Filter "Launcher.exe" -File -Recurse -Depth 8 -ErrorAction SilentlyContinue)
        foreach ($Launcher in $Launchers) {
            $Candidate = $Launcher.DirectoryName
            if (Test-GameDir $Candidate) {
                return $Candidate
            }
        }
    }
    return $null
}

function Show-GameDirHelp {
    param([string]$Path)
    Write-Host "Invalid game folder:"
    Write-Host "  $Path"
    Write-Host ""
    Write-Host "Expected the Hellgate/London2038 install root folder containing:"
    Write-Host "  Launcher.exe"
    Write-Host "  Data\"
    Write-Host "  MP_x64\London2038_dx9_x64.exe or MP_x86\London2038_dx9_x86.exe"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  C:\Program Files\Flagship Studios\Hellgate London"
    Write-Host "  C:\London2038"
    Write-Host ""
    Write-Host "You may also enter a folder inside the Hellgate install, such as Data or MP_x64;"
    Write-Host "the launcher will walk upward and scan below that folder for Launcher.exe."
}

Write-Host "Dawert direct play launcher"
Write-Host "==========================="
Write-Host "Normal play bypasses Launcher.exe so it cannot overwrite localized archives."
Write-Host ""

$GameDir = Find-GameDir
if (-not $GameDir) {
    $GameDir = Read-Host "Hellgate London folder containing Data"
}
$GameDirInput = $GameDir
$GameDir = Resolve-GameDirInput $GameDir
if (-not (Test-GameDir $GameDir)) {
    Show-GameDirHelp $GameDirInput
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
    Write-Host "Install a language first with windows\start-windows.bat or the repacker menu."
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
Write-Host "Done. If you need official updates, run windows\update-windows.bat or menu option 12."
Read-Host "Press Enter to close"

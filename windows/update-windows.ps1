$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepackerDir = Split-Path -Parent $ScriptDir
$Repacker = Join-Path $RepackerDir "repacker.py"
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
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  C:\Program Files\Flagship Studios\Hellgate London"
    Write-Host "  C:\London2038"
    Write-Host ""
    Write-Host "You may also enter a folder inside the Hellgate install, such as Data or MP_x64;"
    Write-Host "the updater will walk upward and scan below that folder for Launcher.exe."
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
    Write-Host "Python 3 is required. Run windows\setup-windows.bat first."
    Read-Host "Press Enter to close"
    exit 1
}

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
    $Repacker,
    "--game-dir", $GameDir,
    "--action", "checksum-update",
    "--language", $Language,
    "--quiet-decrypt-log"
)

Write-Host ""
Write-Host "Done. For normal play, use windows\play-windows.bat."
Read-Host "Press Enter to close"

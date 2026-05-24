$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-Python38 {
    param([string]$Command, [string[]]$Arguments = @())
    try {
        & $Command @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3,8) else 1)" *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        if (Test-Python38 "py" @("-3")) {
            return @("py", "-3")
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-Python38 "python") {
            return @("python")
        }
    }
    return $null
}

function Install-Python {
    Write-Host "Python 3.8+ not found. Installing dependency..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
        return
    }

    if (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install python -y
        return
    }

    $InstallerUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
    $InstallerPath = Join-Path $env:TEMP "python-3.12.10-amd64.exe"
    Write-Host "Downloading Python installer from python.org..."
    Invoke-WebRequest -Uri $InstallerUrl -OutFile $InstallerPath
    Write-Host "Installing Python..."
    Start-Process -FilePath $InstallerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" -Wait
}

Write-Host "Dawert Language Repacker setup"
Write-Host "=============================="
Write-Host "Detected OS: Windows"
Write-Host ""

$Python = Get-PythonCommand
if ($null -eq $Python) {
    Install-Python
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $Python = Get-PythonCommand
}

if ($null -eq $Python) {
    Write-Host "Python install did not complete correctly."
    Write-Host "Install Python 3.8+ manually from https://www.python.org/downloads/windows/"
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Python found: $($Python -join ' ')"
Write-Host "Verifying repacker..."
if ($Python.Count -gt 1) {
    $PythonArgs = $Python[1..($Python.Count - 1)]
} else {
    $PythonArgs = @()
}
& $Python[0] @PythonArgs (Join-Path $ScriptDir "repacker.py") --help *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Repacker verification failed."
    Read-Host "Press Enter to close"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Start with start-windows.bat or start-windows.ps1."
Read-Host "Press Enter to close"
exit 0

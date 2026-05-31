@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

where powershell >nul 2>nul
if %ERRORLEVEL%==0 (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup-windows.ps1"
  exit /b %ERRORLEVEL%
)

where pwsh >nul 2>nul
if %ERRORLEVEL%==0 (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup-windows.ps1"
  exit /b %ERRORLEVEL%
)

echo PowerShell is required to run setup.
echo Install Python 3.8+ manually from https://www.python.org/downloads/windows/
pause
exit /b 1

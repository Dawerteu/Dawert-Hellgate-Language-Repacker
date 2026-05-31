@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

where powershell >nul 2>nul
if %ERRORLEVEL%==0 (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%update-windows.ps1"
  exit /b %ERRORLEVEL%
)

where pwsh >nul 2>nul
if %ERRORLEVEL%==0 (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%update-windows.ps1"
  exit /b %ERRORLEVEL%
)

echo PowerShell is required for the updater.
pause
exit /b 1

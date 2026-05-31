@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "REPACKER=%SCRIPT_DIR%..\repacker.py"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%REPACKER%" --interactive
  pause
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%REPACKER%" --interactive
  pause
  exit /b %ERRORLEVEL%
)

echo Python 3 is required. Install it from https://www.python.org/downloads/windows/
pause
exit /b 1

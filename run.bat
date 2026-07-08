@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV=%~dp0.venv"
set "PY=%VENV%\Scripts\python.exe"
set "PYW=%VENV%\Scripts\pythonw.exe"

if not exist "%PY%" (
    echo [ContentSuite] Creating virtual environment...
    python -m venv "%VENV%"
    if errorlevel 1 goto :error
)

echo [ContentSuite] Checking dependencies...
"%PY%" -m pip install -r requirements.txt -q
if errorlevel 1 goto :error

echo [ContentSuite] Starting...
echo [ContentSuite] Session log: %APPDATA%\ContentSuite\contentsuite.log
start "" "%PYW%" "%~dp0main.py"
exit /b 0

:error
echo.
echo [ContentSuite] Failed to start. Check that Python is installed and in PATH.
pause
exit /b 1
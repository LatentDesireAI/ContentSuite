@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV=%~dp0.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo [build] Creating virtual environment...
    python -m venv "%VENV%"
    if errorlevel 1 goto :error
)

echo [build] Installing dependencies...
"%PY%" -m pip install -r requirements.txt -q
"%PY%" -m pip install pyinstaller -q
if errorlevel 1 goto :error

echo [build] Running PyInstaller...
"%PY%" -m PyInstaller --noconfirm ContentSuite.spec
if errorlevel 1 goto :error

set "OUT=dist\ContentSuite"
set "ZIP=dist\ContentSuite-win64.zip"

if exist "%ZIP%" del /f "%ZIP%"

echo [build] Creating release archive...
powershell -NoProfile -Command ^
  "Compress-Archive -Path 'dist\ContentSuite\*' -DestinationPath '%ZIP%' -Force"

echo.
echo [build] Done.
echo   Folder: %OUT%
echo   Zip:    %ZIP%
echo.
echo Next: create a GitHub Release and upload %ZIP%
exit /b 0

:error
echo.
echo [build] Failed.
pause
exit /b 1
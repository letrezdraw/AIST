@echo off
setlocal
title AIST Launcher

echo --- AIST Application Launcher ---
echo.
echo This script will launch the Backend, Frontend, and GUI components,
echo each in its own new PowerShell window.
echo.
echo To shut down the application, use the system tray icon or the global hotkey.
echo.

:: Change directory to the script's location
cd /d "%~dp0"

:: Check if the PowerShell virtual environment script exists
IF NOT EXIST ".\venv\Scripts\Activate.ps1" (
    echo ERROR: Virtual environment not found.
    echo Please run the installation steps in README.md first.
    pause
    exit /b 1
)
 
echo Launching components...
:: The -NoExit flag keeps the new console window open even if the script inside it fails.
:: The -ExecutionPolicy Bypass flag ensures the activation script can run.
start "AIST Backend" powershell -ExecutionPolicy Bypass -NoExit -Command "& {.\venv\Scripts\Activate.ps1; python run_backend.py}"
timeout /t 2 /nobreak >nul :: Give the backend a moment to start before the frontend connects
start "AIST Frontend" powershell -ExecutionPolicy Bypass -NoExit -Command "& {.\venv\Scripts\Activate.ps1; python main.py}"
start "AIST GUI" powershell -ExecutionPolicy Bypass -NoExit -Command "& {.\venv\Scripts\Activate.ps1; python run_gui.py}"
 
echo.
echo All components launched. This launcher window will now close.
timeout /t 3 >nul
exit /b 0
@echo off
REM This script starts the AIST AI Assistant.
REM It uses PowerShell to activate the virtual environment, install dependencies,
REM and run the main GUI application.

REM Change to the script's directory to ensure all paths are correct.
cd /d "%~dp0"

echo --- AIST AI Assistant ---

REM Check if the virtual environment's Python executable exists.
IF NOT EXIST "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found or is incomplete.
    echo Please run 'python -m venv venv' to create it, then run this script again.
    echo.
    pause
    exit /b
)

echo Found virtual environment.

REM Define the PowerShell command block that will be executed.
REM This is a more robust method that calls the venv executables directly,
REM avoiding potential PATH issues with environment activation.
REM 1. Define variables for the pip and python executables.
REM 2. Install/verify dependencies using the venv's pip.
REM 3. Run the main GUI application using the venv's python.
set "PS_COMMAND=& { $pip = '.\venv\Scripts\pip.exe'; $python = '.\venv\Scripts\python.exe'; Write-Host '--- Installing/Verifying Dependencies ---' -ForegroundColor Green; & $pip install -r requirements.txt; Write-Host '--- Starting AIST GUI ---' -ForegroundColor Green; & $python gui.py }"

REM Execute the command block using PowerShell.
powershell -NoProfile -ExecutionPolicy Bypass -Command "%PS_COMMAND%"

echo.
echo The AIST application has closed. Press any key to exit this window.
pause >nul
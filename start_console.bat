@echo off
setlocal

:: ============================================================================
:: AIST Manual Console Helper
::
:: This script requests admin rights and opens a pre-configured command
:: prompt with the virtual environment activated. You can then run the
:: necessary commands manually.
:: ============================================================================
title AIST Manual Console Helper

:: 1. Check for Administrator privileges and self-elevate if necessary.
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Requesting administrative privileges to manage AIST...
    powershell -command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: Change directory to the script's location
cd /d "%~dp0"

:: 2. Open a new PowerShell console with the venv activated and keep it open.
echo.
echo A new PowerShell console will now open with the AIST environment ready.
start "AIST Manual Console" powershell -ExecutionPolicy Bypass -NoExit -Command ". .\venv\Scripts\Activate.ps1"

exit /b
@echo off
setlocal

:: ==========================================================================
:: AIST Console Helper
:: 
:: This script opens a new PowerShell console with the project's virtual
:: environment pre-activated.
::
:: NOTE: If you want to use the global hotkey (Ctrl+Win+X) and it doesn't
:: work, you may need to run this script as an Administrator. To do that,
:: right-click this file and select "Run as administrator".
:: ==========================================================================
title AIST Console

:: Change directory to the script's location
cd /d "%~dp0"

:: Open a new PowerShell console with the venv activated and keep it open.
echo.
echo Opening a new PowerShell console with the AIST environment ready...
start "AIST Console" powershell -ExecutionPolicy Bypass -NoExit -Command ". .\venv\Scripts\Activate.ps1"

exit /b
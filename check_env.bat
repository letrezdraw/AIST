@echo off
setlocal

echo.
echo --- AIST Environment Prerequisite Checker ---
echo This script will check for the tools required to install llama-cpp-python.
echo.

set "SEPARATOR=--------------------------------------------------"

:: =================================================================
echo %SEPARATOR%
echo [1] Checking for NVIDIA GPU Driver ^(nvidia-smi^) - Press any key to start...
echo %SEPARATOR%
pause >nul
echo.

echo --- Running 'nvidia-smi'...
where nvidia-smi
nvidia-smi
echo.
echo --- Result for Check [1] ---
echo If the commands above ran successfully and showed your GPU info, this check PASSED.
echo The "CUDA Version" in the top right is the MAXIMUM version your driver supports.
echo If you saw an error like "'nvidia-smi' is not recognized", this check FAILED.
echo.

:: =================================================================
echo %SEPARATOR%
echo [2] Checking for NVIDIA CUDA Toolkit ^(nvcc^) - Press any key to start...
echo %SEPARATOR%
pause >nul
echo.

echo --- Running 'nvcc --version'...
where nvcc
nvcc --version
echo.
echo --- Result for Check [2] ---
echo If the command above ran and showed a version number, this check PASSED.
echo This version should ideally match the one in start_aist.bat ^(e.g., 12.1 for cu121^).
echo If you saw an error like "'nvcc' is not recognized", this check FAILED.
echo.

:: =================================================================
echo %SEPARATOR%
echo [3] Checking for C++ Compiler ^(for building from source^) - Manual Check
echo %SEPARATOR%
echo.

echo This check is for the alternative installation method ^(building from source^).
echo It is NOT required if the pre-compiled wheel method in 'start_aist.bat' works.
echo To check for this, open the 'Visual Studio Installer' from your Start Menu
echo and ensure the 'Desktop development with C++' workload is installed.
echo.

:: =================================================================
echo %SEPARATOR%
echo --- Final Summary ---
echo %SEPARATOR%
echo - For the current 'start_aist.bat' to work, you need checks [1] and [2] to PASS.
echo - If they fail, install the NVIDIA drivers and the correct CUDA Toolkit version.
echo - If you continue to have issues after passing checks 1 and 2, you may need
echo   to install the C++ Build Tools ^(check [3]^) and remove the --extra-index-url
echo   from the start_aist.bat script to build from source as a last resort.
echo.

pause
@echo off
REM NetWalker Build Script for Windows
REM Author: Mark Oldham

echo NetWalker Build Script
echo =====================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Install/upgrade PyInstaller if needed
echo Installing/upgrading PyInstaller...
python -m pip install --upgrade pyinstaller

REM Run the build script
echo Running build process...
python build_executable.py

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo.
echo Build completed successfully!
echo Check the dist directory for the executable and ZIP file.
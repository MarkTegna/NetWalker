@echo off
REM NetWalker Web Interface Startup Script
REM Author: Mark Oldham

echo ========================================
echo NetWalker Web Interface
echo Version 1.0.0
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Starting NetWalker Web Interface...
echo.
echo The application will be available at:
echo   http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause

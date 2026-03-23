@echo off
REM Start NetWalker Web UI
REM Author: Mark Oldham

echo ================================================================================
echo NetWalker Web UI Startup Script
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found. Please install Python 3.8 or higher.
    exit /b 1
)

REM Check if netwalker.ini exists
if not exist "netwalker.ini" (
    echo [WARN] netwalker.ini not found in current directory
    echo        Please copy netwalker.ini from NetWalker project
    echo.
    set /p response="Continue anyway? (y/n): "
    if not "%response%"=="y" exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt --quiet

REM Start the application
echo.
echo ================================================================================
echo Starting NetWalker Web UI...
echo ================================================================================
echo.
echo Server will be available at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

# NetWalker Build Script for Windows PowerShell
# Author: Mark Oldham

Write-Host "NetWalker Build Script" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install/upgrade PyInstaller if needed
Write-Host "Installing/upgrading PyInstaller..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller"
    }
} catch {
    Write-Host "Error installing PyInstaller: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the build script
Write-Host "Running build process..." -ForegroundColor Yellow
try {
    python build_executable.py
    if ($LASTEXITCODE -ne 0) {
        throw "Build process failed"
    }
} catch {
    Write-Host "Build failed: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Check the dist directory for the executable and ZIP file." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
@echo off
REM Setup Clean Test Files - Batch Script
REM Copies clean test files from prodtest_files for each test run
REM Author: Mark Oldham

echo NetWalker - Setting up clean test files...
echo.

REM Copy clean test files
copy "prodtest_files\secret_test_creds.ini" "secret_creds.ini" >nul
if %errorlevel% equ 0 (
    echo ✓ Copied clean credentials file
) else (
    echo ✗ Failed to copy credentials file
    exit /b 1
)

copy "prodtest_files\seed_file.csv" "seed_file.csv" >nul
if %errorlevel% equ 0 (
    echo ✓ Copied clean seed devices file
) else (
    echo ✗ Failed to copy seed devices file
    exit /b 1
)

echo.
echo Clean test files ready for testing!
echo.
echo Usage:
echo   setup_clean_test_files.bat          - Run this before each test
echo   .\dist\netwalker\netwalker.exe      - Test with default settings
echo   .\dist\netwalker\netwalker.exe --seed-devices "DEVICE:IP" - Test with CLI override
echo.
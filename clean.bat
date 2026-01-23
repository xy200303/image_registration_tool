@echo off
chcp 65001 >nul
echo ========================================
echo Image Registration Tool - Clean Script
echo ========================================
echo.

echo Cleaning build files...
if exist build (
    rmdir /s /q build
    echo [OK] Removed build/ directory
) else (
    echo [SKIP] build/ directory not found
)

if exist dist (
    rmdir /s /q dist
    echo [OK] Removed dist/ directory
) else (
    echo [SKIP] dist/ directory not found
)

echo.
echo ========================================
echo Clean completed!
echo ========================================
echo.
pause

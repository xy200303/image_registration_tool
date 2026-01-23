@echo off
chcp 65001 >nul
echo ========================================
echo Image Registration Tool - Build Script
echo ========================================
echo.

echo [1/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [2/4] Installing PyInstaller...
pip install pyinstaller -q

echo.
echo [3/4] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [4/4] Building executable...
pyinstaller image_registration_tool.spec --noconfirm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo The executable can be found in:
    echo dist\ImageRegistrationTool.exe
    echo.
    echo File size:
    dir dist\ImageRegistrationTool.exe | findstr "ImageRegistrationTool.exe"
    echo.
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause

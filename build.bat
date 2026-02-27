@echo off
echo ============================================
echo   DogeAutoSub v2.0 - Build Script
echo ============================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Clean previous builds
echo [1/4] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Ensure PyInstaller is installed
echo [2/4] Checking PyInstaller...
pip install pyinstaller --quiet

REM Ensure temp directory exists
if not exist modules\temp mkdir modules\temp

REM Build the application
echo [3/4] Building application...
echo.
pyinstaller DogeAutoSubApp.spec --clean --noconfirm

REM Verify build
echo.
echo [4/4] Verifying build...

if exist "dist\DogeAutoSub\DogeAutoSub.exe" (
    echo.
    echo ============================================
    echo   BUILD SUCCESSFUL
    echo   Output: dist\DogeAutoSub\DogeAutoSub.exe
    echo ============================================
    echo.
    
    REM Show file size
    for %%A in ("dist\DogeAutoSub\DogeAutoSub.exe") do echo   EXE size: %%~zA bytes
    echo.
) else (
    echo.
    echo ============================================
    echo   BUILD FAILED - Check errors above
    echo ============================================
    echo.
)

pause

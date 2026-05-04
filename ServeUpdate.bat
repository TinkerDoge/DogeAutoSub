@echo off
echo ============================================
echo   DogeAutoSub v2.0 - APP
echo ============================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run serve update script
python serve_updates.py

pause

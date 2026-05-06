@echo off
title DogeAutoSub - Fresh Install

REM Tiny launcher. All the logic lives in Install_DogeAutoSub.ps1 alongside
REM this file. We use -ExecutionPolicy Bypass so the script runs even on
REM machines with restrictive defaults — no admin / install required.
REM
REM No Python is needed. Pure PowerShell handles HTTP, JSON, zip extract,
REM and shortcut creation. PowerShell ships with Windows 7 and later.
REM
REM Pass extra args to forward to the .ps1, e.g.:
REM    Install_DogeAutoSub.bat -Server http://192.168.1.50:8100
REM    Install_DogeAutoSub.bat -InstallDir D:\Apps\DogeAutoSub
REM    Install_DogeAutoSub.bat -NoPrompt
REM
REM ────────────────────────────────────────────────────────────────────

set "PS1=%~dp0Install_DogeAutoSub.ps1"

if not exist "%PS1%" (
    echo.
    echo  ERROR: Install_DogeAutoSub.ps1 not found beside this batch file.
    echo  Expected: %PS1%
    echo.
    pause
    exit /b 1
)

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%PS1%" %*
set RC=%ERRORLEVEL%

REM PowerShell handles its own pause/feedback, but in case it crashed
REM before reaching that point keep this window open.
if not "%RC%"=="0" (
    echo.
    echo  Installer exited with code %RC%.
    pause
)

exit /b %RC%

@echo off
setlocal enabledelayedexpansion
title DogeAutoSub — Fresh Install

REM ────────────────────────────────────────────────────────────────
REM  DogeAutoSub fresh installer
REM  Downloads the full release from the LAN update server and
REM  extracts it locally. No Python/admin required.
REM
REM  Defaults:
REM    Server        http://dogeautosub.local:8100  (mDNS)
REM    Install dir   %USERPROFILE%\DogeAutoSub
REM
REM  You can override either by editing the two SET lines below or
REM  by passing them on the command line:
REM    Install_DogeAutoSub.bat http://192.168.1.50:8100  D:\Apps\DogeAutoSub
REM ────────────────────────────────────────────────────────────────

set "SERVER=%~1"
if "%SERVER%"=="" set "SERVER=http://dogeautosub.local:8100"

set "INSTALL_DIR=%~2"
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=%USERPROFILE%\DogeAutoSub"

echo.
echo  ===================================================
echo    DogeAutoSub Installer
echo  ===================================================
echo    Server      : %SERVER%
echo    Install to  : %INSTALL_DIR%
echo  ===================================================
echo.

REM ── Probe the server ──────────────────────────────────────────
echo  [1/4] Probing update server...
powershell -NoProfile -Command ^
  "try { $r = Invoke-WebRequest -Uri '%SERVER%/version.json' -UseBasicParsing -TimeoutSec 5; $j = $r.Content | ConvertFrom-Json; Write-Host '  Server reachable. Latest version:' $j.version; $j.filename | Out-File -Encoding ascii -NoNewline '%TEMP%\dogesub_filename.txt'; $j.version | Out-File -Encoding ascii -NoNewline '%TEMP%\dogesub_version.txt' } catch { Write-Host '  ERROR: cannot reach' '%SERVER%/version.json' -ForegroundColor Red; Write-Host '  Make sure the update server is running on the host machine.' -ForegroundColor Yellow; exit 1 }"
if errorlevel 1 goto :error

set /p ZIP_NAME=<"%TEMP%\dogesub_filename.txt"
set /p VERSION=<"%TEMP%\dogesub_version.txt"

REM Servers may publish DogeAutoSub_v<ver>.zip (small) or
REM DogeAutoSub_v<ver>_full.zip (PyInstaller bundle). Prefer _full.
set "FULL_ZIP=DogeAutoSub_v%VERSION%_full.zip"
echo.
echo  Latest version : %VERSION%
echo  Full bundle    : %FULL_ZIP%

REM ── Confirm ──────────────────────────────────────────────────
echo.
set /p CONFIRM=Proceed with download ^& install? [Y/n]:
if /i "%CONFIRM%"=="n" goto :cancelled

REM ── Wipe existing install ────────────────────────────────────
if exist "%INSTALL_DIR%" (
    echo.
    echo  [2/4] Removing previous install at "%INSTALL_DIR%"...
    rmdir /s /q "%INSTALL_DIR%" 2>nul
    if exist "%INSTALL_DIR%" (
        echo  ERROR: could not remove "%INSTALL_DIR%". Close DogeAutoSub if it's running.
        goto :error
    )
)

REM ── Download ────────────────────────────────────────────────
set "TMP_ZIP=%TEMP%\%FULL_ZIP%"
if exist "%TMP_ZIP%" del /q "%TMP_ZIP%"

echo.
echo  [3/4] Downloading %FULL_ZIP% from %SERVER%...
echo         (this can be several GB — be patient)

powershell -NoProfile -Command ^
  "try { $ProgressPreference='Continue'; Invoke-WebRequest -Uri '%SERVER%/%FULL_ZIP%' -OutFile '%TMP_ZIP%' -UseBasicParsing } catch { Write-Host '  Full bundle not found, trying delta zip...' -ForegroundColor Yellow; try { Invoke-WebRequest -Uri '%SERVER%/%ZIP_NAME%' -OutFile '%TMP_ZIP%' -UseBasicParsing } catch { Write-Host '  ERROR: download failed:' $_.Exception.Message -ForegroundColor Red; exit 1 } }"
if errorlevel 1 goto :error
if not exist "%TMP_ZIP%" goto :error

REM ── Extract ─────────────────────────────────────────────────
echo.
echo  [4/4] Extracting to "%INSTALL_DIR%"...
mkdir "%INSTALL_DIR%" 2>nul
powershell -NoProfile -Command ^
  "try { Expand-Archive -LiteralPath '%TMP_ZIP%' -DestinationPath '%INSTALL_DIR%\..' -Force } catch { Write-Host '  ERROR: extract failed:' $_.Exception.Message -ForegroundColor Red; exit 1 }"
if errorlevel 1 goto :error

del /q "%TMP_ZIP%" 2>nul

REM ── Locate the actual exe (zip may have nested folder) ──────
set "EXE_PATH=%INSTALL_DIR%\DogeAutoSub.exe"
if not exist "%EXE_PATH%" (
    REM PyInstaller bundles produce DogeAutoSub\DogeAutoSub.exe
    if exist "%INSTALL_DIR%\DogeAutoSub\DogeAutoSub.exe" (
        set "EXE_PATH=%INSTALL_DIR%\DogeAutoSub\DogeAutoSub.exe"
    )
)

if not exist "%EXE_PATH%" (
    echo.
    echo  WARNING: extracted but DogeAutoSub.exe not found in expected location.
    echo  Look inside %INSTALL_DIR% manually.
    goto :end
)

REM ── Optional desktop shortcut ───────────────────────────────
echo.
set /p MAKE_SHORTCUT=Create desktop shortcut? [Y/n]:
if /i not "%MAKE_SHORTCUT%"=="n" (
    powershell -NoProfile -Command ^
      "$s = (New-Object -ComObject WScript.Shell).CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'),'DogeAutoSub.lnk')); $s.TargetPath='%EXE_PATH%'; $s.WorkingDirectory=Split-Path '%EXE_PATH%' -Parent; $s.IconLocation='%EXE_PATH%,0'; $s.Save()"
    echo  Shortcut placed on the desktop.
)

echo.
echo  ===================================================
echo    Install complete.
echo    %EXE_PATH%
echo  ===================================================

set /p LAUNCH=Launch DogeAutoSub now? [Y/n]:
if /i not "%LAUNCH%"=="n" start "" "%EXE_PATH%"

goto :end

:cancelled
echo.
echo  Cancelled.
goto :end

:error
echo.
echo  Install failed. See messages above.
exit /b 1

:end
echo.
pause
endlocal

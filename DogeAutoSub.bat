@echo off

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PYTHON_DIR=%VENV_DIR%\Scripts"

call "%VENV_DIR%\Scripts\activate"

echo Running AutoUI.py...
"%PYTHON_DIR%\python.exe" "%SCRIPT_DIR%\AutoUI.py" %*
if %errorlevel% equ 1 (
  echo The AutoUI.py window was closed unexpectedly.
) else (
  echo Much Thanks, Many Like.
  rem Display ASCII art
  echo ;
  echo                 ;i.
  echo                  M$L                    .;i.
  echo                  M$Y;                .;iii;;.
  echo                 ;$YY$i._           .iiii;;;;;
  echo                .iiiYYYYYYiiiii;;;;i;iii;; ;;;
  echo              .;iYYYYYYiiiiiiYYYiiiiiii;;  ;;;
  echo           .YYYY$$$$YYYYYYYYYYYYYYYYiii;; ;;;;
  echo         .YYY$$$$$$YYYYYY$$$$iiiY$$$$$$$ii;;;;
  echo        :YYYF`,  TYYYYY$$$$$YYYYYYYi$$$$$iiiii;
  echo        Y$MM: \  :YYYY$$P"````"T$YYMMMMMMMMiiYY.
  echo     `.;$$M$$b.,dYY$$Yi; .(     .YYMMM$$$MMMMYY
  echo   .._$MMMMM$!YYYYYYYYYi;.`"  .;iiMMM$MMMMMMMYY
  echo    ._$MMMP` ```""4$$$$$iiiiiiii$MMMMMMMMMMMMMY;
  echo     MMMM$:       :$$$$$$$MMMMMMMMMMM$$MMMMMMMYYL
  echo    :MMMM$$.    .;PPb$$$$MMMMMMMMMM$$$$MMMMMMiYYU:
  echo     iMM$$;;: ;;;;i$$$$$$$MMMMM$$$$MMMMMMMMMMYYYYY
  echo     `$$$$i .. ``:iiii!*"``.$$$$$$$$$MMMMMMM$YiYYY
  echo      :Y$$iii;;;.. ` ..;;i$$$$$$$$$MMMMMM$$YYYYiYY:
  echo       :$$$$$iiiiiii$$$$$$$$$$$MMMMMMMMMMYYYYiiYYYY.
  echo        `$$$$$$$$$$$$$$$$$$$$MMMMMMMM$YYYYYiiiYYYYYY
  echo         YY$$$$$$$$$$$$$$$$MMMMMMM$$YYYiiiiiiYYYYYYY
  echo        :YYYYYY$$$$$$$$$$$$$$$$$$YYYYYYYiiiiYYYYYYi' 
  echo ; 
)

call "%VENV_DIR%\Scripts\deactivate"

set /a COUNTDOWN=5
echo Dogeing in %COUNTDOWN% seconds...
:COUNTDOWN_LOOP
timeout /t 1 /nobreak > nul
set /a COUNTDOWN-=1
if %COUNTDOWN% gtr 0 (
  echo Dogeing in %COUNTDOWN% seconds...
  goto COUNTDOWN_LOOP
)

goto END

:END
exit /b

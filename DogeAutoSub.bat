@echo off

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON=D:\Software\python310\python.exe"
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
set "WHISPER_DIR=%VENV_DIR%\Lib\site-packages\whisper"

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    "%PYTHON%" -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate"
    echo Installing/updating requirements...
    python -m pip install --upgrade pip
    python -m pip install --upgrade -r "%REQUIREMENTS%"
    echo Copying custom audio.py and transcribe.py to whisper package...
    copy "%SCRIPT_DIR%modules\audio.py" "%WHISPER_DIR%\audio.py" /Y
    copy "%SCRIPT_DIR%modules\transcribe.py" "%WHISPER_DIR%\transcribe.py" /Y

) else (
    call "%VENV_DIR%\Scripts\activate"
    echo Updating requirements...
    echo Checking for existing PySide2 installation...
    python -m pip show PySide2 >nul 2>&1
    if %errorlevel% equ 0 (
        echo Uninstalling existing PySide2...
        python -m pip uninstall -y PySide2
    )
    python -m pip install --upgrade -r "%REQUIREMENTS%"
    echo Copying custom audio.py and transcribe.py to whisper package...
    copy "%SCRIPT_DIR%modules\audio.py" "%WHISPER_DIR%\audio.py" /Y
    copy "%SCRIPT_DIR%modules\transcribe.py" "%WHISPER_DIR%\transcribe.py" /Y
)

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

echo Running AutoUI.py...
python "%SCRIPT_DIR%\AutoUI.py" %*
if %errorlevel% equ 1 (
  echo The AutoUI.py window was closed unexpectedly.
) else (
  echo Much Thanks, Many Like.
)
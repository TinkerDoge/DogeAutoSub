@echo off

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PYTHON_DIR=%VENV_DIR%\Scripts"
set "PYTHON=C:\python3.9.7\python.exe"
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
set "WHISPER_DIR=%VENV_DIR%\Lib\site-packages\whisper"
set "CACHE_DIR=%VENV_DIR%\Lib\site-packages\whisper\.cache\whisper"
set "MODELS_DIR=%SCRIPT_DIR%\modules\models"

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    "%PYTHON%" -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate"
    echo Installing/updating requirements...
    "%PYTHON_DIR%\python.exe" -m pip install --upgrade pip
    "%PYTHON_DIR%\pip.exe" install --upgrade -r "%REQUIREMENTS%"
    echo Copying custom audio.py and transcribe.py to whisper package...
    copy "%SCRIPT_DIR%modules\audio.py" "%WHISPER_DIR%\audio.py" /Y
    copy "%SCRIPT_DIR%modules\transcribe.py" "%WHISPER_DIR%\transcribe.py" /Y
    echo Checking and copying pre-downloaded models to cache directory...
    if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
    if exist "%MODELS_DIR%" (
        for %%f in ("%MODELS_DIR%\*") do (
            if not exist "%CACHE_DIR%\%%~nxf" (
                echo Copying %%f to cache directory...
                copy "%%f" "%CACHE_DIR%\" 
            )
        )
    ) else (
        echo Models folder not found, skipping model copy...
    )
) else (
    call "%VENV_DIR%\Scripts\activate"
    echo Updating requirements...
    echo Checking for existing PySide2 installation...
    "%PYTHON_DIR%\pip.exe" show PySide2 >nul 2>&1
    if %errorlevel% equ 0 (
        echo Uninstalling existing PySide2...
        "%PYTHON_DIR%\pip.exe" uninstall -y PySide2
    )
    "%PYTHON_DIR%\pip.exe" install --upgrade -r "%REQUIREMENTS%"
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
"%PYTHON_DIR%\python.exe" "%SCRIPT_DIR%\AutoUI.py" %*
if %errorlevel% equ 1 (
  echo The AutoUI.py window was closed unexpectedly.
) else (
  echo Much Thanks, Many Like.
)
@echo off

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PYTHON_DIR=%VENV_DIR%\Scripts"
set "PYTHON=C:\python3.9.7\python.exe"
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
set "WHISPER_DIR=%VENV_DIR%\Lib\site-packages\whisper"
set "CACHE_DIR=%VENV_DIR%\Lib\site-packages\whisper\.cache\whisper"
set "MODELS_DIR=%SCRIPT_DIR%models"

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
    for %%f in ("%MODELS_DIR%\*") do (
        if not exist "%CACHE_DIR%\%%~nxf" (
            echo Copying %%f to cache directory...
            copy "%%f" "%CACHE_DIR%\"
        )
    )
) else (
    call "%VENV_DIR%\Scripts\activate"
    echo Updating requirements...
    "%PYTHON_DIR%\pip.exe" install --upgrade -r "%REQUIREMENTS%"
    echo Copying custom audio.py and transcribe.py to whisper package...
    copy "%SCRIPT_DIR%modules\audio.py" "%WHISPER_DIR%\audio.py" /Y
    copy "%SCRIPT_DIR%modules\transcribe.py" "%WHISPER_DIR%\transcribe.py" /Y
    echo Checking and copying pre-downloaded models to cache directory...
    if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
    for %%f in ("%MODELS_DIR%\*") do (
        if not exist "%CACHE_DIR%\%%~nxf" (
            echo Copying %%f to cache directory...
            copy "%%f" "%CACHE_DIR%\"
        )
    )
)

echo Running AutoUI.py...
"%PYTHON_DIR%\python.exe" "%SCRIPT_DIR%\AutoUI.py" %*
if %errorlevel% equ 1 (
  echo The AutoUI.py window was closed unexpectedly.
) else (
  echo Much Thanks, Many Like.
)
@echo off

set PYTHON="C:\python3.7.0\python.exe"
set VENV_DIR="D:\BANK\Software\CODE\DogeAutoSub\venv"

:activate_venv
set PYTHON="%VENV_DIR%\Scripts\Python.exe"
echo venv %PYTHON%

:launch
%PYTHON% AutoSub.py %*
pause
exit /b
@echo off

set VENV_DIR=D:\BANK\Software\CODE\DogeAutoSub\venv
set PYTHON_DIR =%VENV_DIR%\Scripts\
call %VENV_DIR%\Scripts\activate

%PYTHON_DIR%python AutoUI.py %*

pause

call %VENV_DIR%\Scripts\deactivate

exit /b

@echo off

set VENV_DIR=D:\BANK\Software\CODE\DogeAutoSub\venv

call %VENV_DIR%\Scripts\activate

python AutoUI.py %*

pause

call %VENV_DIR%\Scripts\deactivate

exit /b

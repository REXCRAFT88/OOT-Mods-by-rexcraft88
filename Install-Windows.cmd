@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
if errorlevel 1 goto fail
py -3 install_gui.py
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Installation failed. Read the error above. Python 3.11 or newer is required.
pause
exit /b 1

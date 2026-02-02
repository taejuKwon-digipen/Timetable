@echo off
cd /d "%~dp0"

echo [1] py main.py 실행...
py main.py
if %errorlevel% equ 0 goto :end

echo.
echo [2] python main.py 실행...
python main.py
if %errorlevel% equ 0 goto :end

echo.
echo 실행 실패. Python + PyQt6 설치 필요.
echo 터미널에서: py -m pip install PyQt6
pause
:end

@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   시간표 관리 프로그램 빌드
echo ========================================
echo.

echo [1] PyInstaller 설치 확인...
py -m pip install pyinstaller PyQt6 --quiet 2>nul
if errorlevel 1 (
    python -m pip install pyinstaller PyQt6 --quiet 2>nul
)

echo.
echo [2] 빌드 실행 (단일 exe, 콘솔 없음)...
py -m PyInstaller --onefile --windowed --name "TimeTable" --clean main.py 2>nul
if errorlevel 1 (
    python -m PyInstaller --onefile --windowed --name "TimeTable" --clean main.py
)

if exist "dist\TimeTable.exe" (
    echo.
    echo ========================================
    echo   빌드 완료!
    echo   dist\TimeTable.exe
    echo ========================================
) else (
    echo.
    echo 빌드 실패. 오류 메시지를 확인하세요.
)

echo.
pause

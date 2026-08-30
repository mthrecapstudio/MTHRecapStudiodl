@echo off
title MTH Recap - Auto Discord Server Setup
echo ========================================================
echo   SETUP DISCORD SERVER TU DONG CHO MTH RECAP STUDIO
echo ========================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo [*] Dang chay bang moi truong Python .venv...
    ".venv\Scripts\python.exe" setup_server.py
) else (
    echo [*] Dang chay bang Python he thong...
    python setup_server.py
)

echo.
echo ========================================================
echo Da hoan tat! Nhan phim bat ky de thoat.
pause >nul

@echo off
title MTH Recap - AI Support Bot
echo ========================================================
echo       KHOI DONG DISCORD AI SUPPORT BOT (MTH RECAP)
echo ========================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo [*] Dang chay Bot bang moi truong Python .venv...
    ".venv\Scripts\python.exe" bot.py
) else (
    echo [*] Dang chay Bot bang Python he thong...
    python bot.py
)

echo.
pause

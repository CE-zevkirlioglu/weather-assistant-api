@echo off
echo ========================================
echo Weather Assistant Backend Baslatiliyor...
echo ========================================
echo.

cd /d "%~dp0"
set PYTHONPATH=src
python src/server.py

pause


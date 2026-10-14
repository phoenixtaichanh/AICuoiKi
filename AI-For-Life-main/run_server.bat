@echo off
chcp 65001 >nul
title AI-For-Life Travel Assistant
cd /d D:\AI-For-Life-main\AI-For-Life-main

echo.
echo ==========================================
echo   Khoi dong AI-For-Life Travel Assistant
echo ==========================================
echo.

REM Chay launcher (se tu dong mo browser)
".venv\Scripts\python.exe" run.py

if errorlevel 1 (
    echo.
    echo Loi: Server khong the khoi dong. Kiem tra logs.
    pause
)

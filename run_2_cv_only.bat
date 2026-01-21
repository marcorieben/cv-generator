@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo [CV Generator - JSON to Word Only]
echo ========================================
echo [!DATE! !TIME!] Starting CV generation...
echo.

echo [!DATE! !TIME!] Activating virtual environment...
echo [!DATE! !TIME!] Processing JSON files...
echo.
.venv\Scripts\python.exe scripts\generate_cv.py

if !ERRORLEVEL! equ 0 (
    echo [!DATE! !TIME!] CV generation completed successfully
) else (
    echo [!DATE! !TIME!] CV generation failed with error code !ERRORLEVEL!
)
echo.

timeout /t 2 >nul
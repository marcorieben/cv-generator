@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
REM Unified CV Pipeline Launcher
REM Runs: PDF -> JSON -> Word in one flow

echo ========================================
echo [CV Generator - Unified Pipeline]
echo PDF -> JSON -> Word
echo ========================================
echo [!DATE! !TIME!] Starting pipeline...
echo.

echo [!DATE! !TIME!] Activating virtual environment...
echo [!DATE! !TIME!] Processing PDF files...
echo.
.venv\Scripts\python.exe scripts\pipeline.py

if !ERRORLEVEL! equ 0 (
    echo [!DATE! !TIME!] Pipeline completed successfully
) else (
    echo [!DATE! !TIME!] Pipeline failed with error code !ERRORLEVEL!
)
echo.

pause

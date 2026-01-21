@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo [CV Generator - Streamlit App]
echo ========================================
echo [!DATE! !TIME!] Starting Streamlit app...
echo.

echo [!DATE! !TIME!] Activating virtual environment...
echo [!DATE! !TIME!] Launching Streamlit server...
echo.
.venv\Scripts\python.exe -m streamlit run app.py

if !ERRORLEVEL! equ 0 (
    echo [!DATE! !TIME!] App stopped normally
) else (
    echo [!DATE! !TIME!] App encountered an error: !ERRORLEVEL!
)
echo.

pause
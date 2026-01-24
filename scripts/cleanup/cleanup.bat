"""
Module description

Purpose: Analyzed as PROMPT
Expected Lifetime: permanent
Category: PROMPT
Created: 2026-01-23
Last Updated: 2026-01-24
"""
@echo off
REM Cleanup System - Run via BAT file
REM
REM Usage:
REM   scripts\cleanup\cleanup.bat              - Analyze mode (safe, no changes)
REM   scripts\cleanup\cleanup.bat apply        - Apply mode (may delete files)

setlocal enabledelayedexpansion

echo.
echo Initializing cleanup environment...
echo.

REM Get the project root (two levels up from this script)
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..\") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

REM Check if venv exists
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ERROR: Virtual environment not found
    echo.
    echo Please run setup first:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Run cleanup
echo Running cleanup system...
echo.

REM Pass arguments through to Python
if "%1"=="" (
    REM No arguments - analyze mode
    .venv\Scripts\python.exe scripts\cleanup\cleanup.py
) else (
    REM Pass arguments
    .venv\Scripts\python.exe scripts\cleanup\cleanup.py %*
)

set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% equ 0 (
    echo.
    echo ✓ Cleanup completed successfully
    echo.
    echo View reports in: cleanup/runs/
    echo.
) else (
    echo.
    echo ✗ Cleanup encountered an error
    echo.
)

pause
exit /b %EXIT_CODE%

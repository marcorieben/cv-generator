@echo off
REM Unified CV Pipeline Launcher
REM Runs: PDF -> JSON -> Word in one flow

echo ========================================
echo CV Generator - Unified Pipeline
echo PDF -^> JSON -^> Word
echo ========================================
echo.

REM Use virtual environment Python
.venv\Scripts\python.exe run_pipeline.py

pause

"""
Module description

Purpose: Analyzed as PROMPT
Expected Lifetime: permanent
Category: PROMPT
Created: 2025-12-17
Last Updated: 2026-01-24
"""
@echo off
REM Unified CV Pipeline Launcher
REM Runs: PDF -> JSON -> Word in one flow

echo ========================================
echo CV Generator - Unified Pipeline
echo PDF -^> JSON -^> Word
echo ========================================
echo.

REM Use virtual environment Python
.venv\Scripts\python.exe scripts\pipeline.py

pause

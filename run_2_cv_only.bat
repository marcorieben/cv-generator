"""
Module description

Purpose: Analyzed as PROMPT
Expected Lifetime: permanent
Category: PROMPT
Created: 2025-12-17
Last Updated: 2026-01-24
"""
@echo off
echo Starting CV Generator...
python scripts/generate_cv.py
echo CV Generator finished.
timeout /t 2 >nul
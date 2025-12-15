@echo off
echo Starting CV Generator...
python scripts/generate_cv.py
echo CV Generator finished.
timeout /t 2 >nul
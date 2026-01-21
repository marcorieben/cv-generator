@echo off
REM Pre-commit hook installer for Windows

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo 🔧 Setting up Pre-Commit Hook (Windows)
echo ============================================================
echo.

set HOOK_DIR=.git\hooks
set HOOK_FILE=%HOOK_DIR%\pre-commit

if not exist "%HOOK_DIR%" (
    echo Creating .git\hooks directory...
    mkdir "%HOOK_DIR%"
)

echo Creating pre-commit hook file...

(
    echo @echo off
    echo REM Pre-commit hook - runs before each commit
    echo.
    echo python scripts\pre_commit_hook.py "%%1%%"
    echo if errorlevel 1 (
    echo     echo.
    echo     echo ⚠️  Pre-commit checks had warnings ^(commit allowed^)
    echo     exit /b 0
    echo ^)
    echo exit /b 0
) > "%HOOK_FILE%"

echo.
echo ✅ Hook installed at: %HOOK_FILE%
echo.
echo 📝 Hook behavior:
echo    • Validates commit message format
echo    • Extracts structured metadata
echo    • Scans for unused files
echo    • Generates commit documentation
echo.
echo 🚀 The hook will run automatically before each commit.
echo.
echo 💡 Tip: Make sure Python is in your PATH
echo    python --version
echo.
echo ============================================================
echo Setup complete!
echo ============================================================
echo.

endlocal

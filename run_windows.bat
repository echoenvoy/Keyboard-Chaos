@echo off
:: Keyboard Chaos — Windows launcher
:: Run this as Administrator for system-wide key hooks

echo.
echo  ██████████████████████████████████████
echo  ██   KEYBOARD CHAOS — Windows        ██
echo  ██████████████████████████████████████
echo.
echo  NOTE: Requires Administrator for global key hooks.
echo  Right-click this file > "Run as administrator"
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Install deps if needed
pip show keyboard >nul 2>&1
if %errorlevel% neq 0 (
    echo  Installing dependencies...
    pip install -r requirements.txt
)

echo  Launching...
python main.py %*
pause

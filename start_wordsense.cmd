@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Please install dependencies using the commands in README.md first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m wordsense
if errorlevel 1 pause

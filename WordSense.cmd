@echo off
setlocal
set "WORDSENSE_RELEASE=%~dp0dist\WordSense-v1.0.4"
if not exist "%WORDSENSE_RELEASE%\_internal\python313.dll" (
    echo The complete release folder is missing. Extract the release ZIP with its _internal folder.
    pause
    exit /b 1
)
if not exist "%WORDSENSE_RELEASE%\WordSense.exe" (
    echo WordSense.exe is missing from the release folder.
    pause
    exit /b 1
)
start "" "%WORDSENSE_RELEASE%\WordSense.exe"

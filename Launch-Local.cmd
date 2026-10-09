@echo off
cd /d "%~dp0"
if not exist "runtime\python.exe" (
    echo Bundled runtime is missing. Extract the entire ZIP before launching.
    pause
    exit /b 1
)
"runtime\python.exe" "serve_local.py" --open
if errorlevel 1 (
    echo.
    echo The server could not start. Check the error above.
    pause
)

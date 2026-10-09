@echo off
cd /d "%~dp0"
if not exist "runtime\python.exe" (
  echo Run Download-Game.cmd first; the bundled runtime is missing.
  pause
  exit /b 1
)
"runtime\python.exe" "verify_game.py"
pause

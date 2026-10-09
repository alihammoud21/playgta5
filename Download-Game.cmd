@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Download-Game.ps1"
if errorlevel 1 (
  echo.
  echo Download did not finish. Read the error above, then run this file again.
)
pause

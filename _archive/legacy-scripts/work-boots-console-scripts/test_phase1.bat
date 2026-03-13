@echo off
setlocal EnableExtensions

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found. Run scripts\run_phase1_api.bat first.
  exit /b 1
)

".venv\Scripts\python.exe" -m pytest app/tests -q %*
exit /b %errorlevel%

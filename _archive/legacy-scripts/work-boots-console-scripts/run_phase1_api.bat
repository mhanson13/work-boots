@echo off
setlocal EnableExtensions

REM Run from repo root regardless of current folder.
cd /d "%~dp0\.."

echo [Work Boots Console] Phase 1 API launcher
echo Mode: default sqlite (pass "postgres" to use .env DATABASE_URL)

echo.
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment in .venv ...
  where py >nul 2>&1
  if %errorlevel%==0 (
    py -3.10 -m venv .venv 2>nul
    if %errorlevel% neq 0 py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if %errorlevel% neq 0 goto :error
)

echo Installing/updating dependencies ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 goto :error

if not exist ".env" (
  echo Creating .env from .env.example ...
  copy /Y ".env.example" ".env" >nul
  if %errorlevel% neq 0 goto :error
)

echo.
echo Starting API at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
if /I "%~1"=="postgres" (
  echo Using DATABASE_URL from .env
  ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000 --env-file .env
) else (
  echo Using SQLite database file: local_phase1.db
  set "DATABASE_URL=sqlite:///./local_phase1.db"
  ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
)
exit /b %errorlevel%

:error
echo.
echo Launch failed. Fix the error above and rerun scripts\run_phase1_api.bat
exit /b 1

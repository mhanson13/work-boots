@echo off
setlocal EnableExtensions

REM Run from repo root regardless of current folder.
cd /d "%~dp0\.."

set "USE_POSTGRES=0"
set "UPGRADE_PIP=0"

for %%A in (%*) do (
  if /I "%%~A"=="postgres" set "USE_POSTGRES=1"
  if /I "%%~A"=="upgrade-pip" set "UPGRADE_PIP=1"
  if /I "%%~A"=="--upgrade-pip" set "UPGRADE_PIP=1"
)

echo [mbsrn] API Launcher
if "%USE_POSTGRES%"=="1" (
  echo Mode: postgres ^(using DATABASE_URL from .env^)
) else (
  echo Mode: sqlite ^(local.db^)
)
if "%UPGRADE_PIP%"=="1" (
  echo Pip upgrade: enabled
) else (
  echo Pip upgrade: skipped
)
echo.

if not exist ".venv\Scripts\python.exe" (
  echo [1/5] Creating virtual environment in .venv ...
  where py >nul 2>&1
  if %errorlevel%==0 (
    py -3.10 -m venv .venv 2>nul
    if %errorlevel% neq 0 py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if %errorlevel% neq 0 goto :error_venv
)

if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment python not found after setup.
  goto :error_venv
)

if "%UPGRADE_PIP%"=="1" (
  echo [2/5] Upgrading pip ...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  if %errorlevel% neq 0 goto :error_deps
)

if not exist "requirements.txt" (
  echo requirements.txt was not found in repo root.
  goto :error_deps
)

echo [3/5] Installing runtime dependencies from requirements.txt ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 goto :error_deps

if not exist ".env" (
  if not exist ".env.example" (
    echo .env is missing and .env.example was not found.
    goto :error_env
  )
  echo [4/5] Creating .env from .env.example ...
  copy /Y ".env.example" ".env" >nul
  if %errorlevel% neq 0 goto :error_env
)

echo [5/5] Starting API at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.

if "%USE_POSTGRES%"=="1" (
  echo Using DATABASE_URL from .env
  ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000 --env-file .env
) else (
  echo Using SQLite database file: local.db
  set "DATABASE_URL=sqlite:///./local.db"
  ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000 --env-file .env
)
exit /b %errorlevel%

:error_venv
echo.
echo Failed to create or locate the virtual environment.
echo Verify Python is installed and available as "py" or "python".
echo Then rerun scripts\run_api.bat
exit /b 1

:error_deps
echo.
echo Dependency installation failed.
echo Review the pip output above and retry.
echo You can rerun with pip upgrade enabled:
echo   scripts\run_api.bat --upgrade-pip
exit /b 1

:error_env
echo.
echo Environment file setup failed.
echo Ensure .env.example exists or create .env manually.
echo Then rerun scripts\run_api.bat
exit /b 1

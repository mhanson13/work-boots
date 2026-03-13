@echo off
setlocal EnableExtensions

cd /d "%~dp0\.."

echo [Work Boots Console] Test Runner
echo.

if not exist "requirements-dev.txt" (
  echo requirements-dev.txt was not found in repo root.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment in .venv ...
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

echo Installing test dependencies from requirements-dev.txt ...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if %errorlevel% neq 0 goto :error_deps

echo Running pytest ...
".venv\Scripts\python.exe" -m pytest app/tests -q %*
if %errorlevel% neq 0 goto :error_tests
exit /b 0

:error_venv
echo.
echo Failed to create or locate virtual environment.
echo Verify Python is installed and available as "py" or "python".
exit /b 1

:error_deps
echo.
echo Failed to install test dependencies.
echo Review the pip output above and retry.
exit /b 1

:error_tests
echo.
echo Tests failed.
echo Review failures above.
exit /b 1

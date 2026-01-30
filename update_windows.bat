@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Attendance System - Windows Update
echo   Version: 2.11.0
echo ========================================
echo.

REM === VERIFY LOCATION ===
if not exist "%~dp0README.md" (
    echo ERROR: This script must be run from the Attendance folder.
    pause
    exit /b 1
)

cd /d "%~dp0"
echo Working directory: %CD%
echo.

REM ========================================
REM   STEP 1: BACKUP DATABASE
REM ========================================
echo [1/5] Backing up database...

if exist "attendance.db" (
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "BACKUP_NAME=attendance.db.backup.!dt:~0,8!_!dt:~8,6!"
    copy "attendance.db" "!BACKUP_NAME!" >nul
    echo   Backup created: !BACKUP_NAME!
) else (
    echo   No database found (first install?)
)
echo.

REM ========================================
REM   STEP 2: STOP RUNNING SERVICES
REM ========================================
echo [2/5] Stopping running services...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo   Services stopped.
echo.

REM ========================================
REM   STEP 3: UPDATE CODE FROM GITHUB
REM ========================================
echo [3/5] Updating from GitHub...

git fetch origin
if %errorLevel% neq 0 (
    echo   ERROR: Failed to fetch from GitHub.
    pause
    exit /b 1
)

git reset --hard origin/master
if %errorLevel% neq 0 (
    echo   ERROR: Failed to update code.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('git log --oneline -1') do echo   Current version: %%v
echo.

REM ========================================
REM   STEP 4: UPDATE BACKEND DEPENDENCIES
REM ========================================
echo [4/5] Updating Backend dependencies...

cd backend
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
call deactivate
cd ..

echo   Backend updated.
echo.

REM ========================================
REM   STEP 5: REBUILD FRONTEND
REM ========================================
echo [5/5] Rebuilding Frontend...

cd frontend
call npm install --silent
call npm run build

if not exist "dist\index.html" (
    echo   ERROR: Frontend build failed!
    cd ..
    pause
    exit /b 1
)
cd ..

echo   Frontend rebuilt.
echo.

REM ========================================
REM   COMPLETE
REM ========================================
echo ========================================
echo   UPDATE COMPLETE!
echo ========================================
echo.
echo   To start the application:
echo     Double-click: start_system.bat
echo.
echo   Clear browser cache (Ctrl+Shift+R) to see changes.
echo.
echo ========================================
echo.
pause

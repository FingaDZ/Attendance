@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Attendance System - Production Start
echo ========================================
echo.

REM === AUTO-DETECT LOCAL IP ===
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set LOCAL_IP=%%b
)
REM Trim leading space
set LOCAL_IP=%LOCAL_IP: =%

echo [1/4] Detected IP: %LOCAL_IP%
echo.

REM === VERIFY DEPENDENCIES ===
echo [2/4] Verifying dependencies...

if not exist "%~dp0backend\venv\Scripts\python.exe" (
    echo.
    echo ERROR: Backend virtual environment not found!
    echo.
    echo Please run these commands first:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0frontend\dist\index.html" (
    echo.
    echo ERROR: Frontend build not found!
    echo.
    echo Please run these commands first:
    echo   cd frontend
    echo   npm install
    echo   npm run build
    echo.
    pause
    exit /b 1
)

echo   - Backend venv: OK
echo   - Frontend build: OK
echo.

REM === KILL EXISTING PROCESSES ===
echo [3/4] Cleaning up existing processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM === START BACKEND (serves API + Frontend) ===
echo [4/4] Starting Backend Server (Port 8000)...
echo.
start "Attendance Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 5 /nobreak >nul

echo ========================================
echo   System Started Successfully!
echo ========================================
echo.
echo   Access URLs:
echo   - Local:     http://localhost:8000
echo   - Dashboard: http://%LOCAL_IP%:8000
echo   - Kiosk:     http://%LOCAL_IP%:8000/kiosk
echo   - API Docs:  http://%LOCAL_IP%:8000/docs
echo.
echo   NOTE: Camera requires HTTPS or Chrome flag.
echo   See: chrome://flags/#unsafely-treat-insecure-origin-as-secure
echo.
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul


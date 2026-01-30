@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Attendance System - LAN Access Mode
echo ========================================
echo.

REM === AUTO-DETECT LOCAL IP ===
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set LOCAL_IP=%%b
)
set LOCAL_IP=%LOCAL_IP: =%

echo Detected IP: %LOCAL_IP%
echo.

REM === START BACKEND ===
echo Starting Backend Server...
start "Attendance Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   Access the application at:
echo.
echo   Dashboard: http://%LOCAL_IP%:8000
echo   Kiosk:     http://%LOCAL_IP%:8000/kiosk
echo   API:       http://%LOCAL_IP%:8000/docs
echo.
echo   CAMERA NOTE:
echo   Camera access requires HTTPS or Chrome flag.
echo   On client devices, open:
echo   chrome://flags/#unsafely-treat-insecure-origin-as-secure
echo   Add: http://%LOCAL_IP%:8000
echo ========================================
echo.
pause

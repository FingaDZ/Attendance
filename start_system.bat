@echo off
echo ========================================
echo   Attendance System - Startup Script
echo ========================================
echo.

REM Kill any existing Python/Node processes
echo [1/4] Cleaning up existing processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

REM Start Backend
echo [2/4] Starting Backend Server...
start "Backend Server" cmd /k "cd /d %~dp0 && backend\venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

REM Start Frontend
echo [3/4] Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo [4/4] System started successfully!
echo.
echo ========================================
echo   Access URLs:
echo   - Frontend: https://localhost:5173
echo   - Backend API: http://localhost:8000
echo   - Network: https://192.168.66.103:5173
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul

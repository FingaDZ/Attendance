@echo off
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     ATTENDANCE SYSTEM - SERVICE INSTALLER            ║
echo  ║     Installs as Windows Service                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

REM === CHECK ADMIN RIGHTS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [ERROR] This script requires Administrator privileges.
    echo          Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

set "INSTALL_PATH=C:\Attendance"
set "NSSM_URL=https://nssm.cc/release/nssm-2.24.zip"
set "NSSM_PATH=%INSTALL_PATH%\tools\nssm.exe"
set "SERVICE_NAME=AttendanceSystem"

REM === DOWNLOAD NSSM IF NOT EXISTS ===
if not exist "%NSSM_PATH%" (
    echo [1/4] Downloading NSSM...
    
    if not exist "%INSTALL_PATH%\tools" mkdir "%INSTALL_PATH%\tools"
    
    REM Download using PowerShell
    powershell -Command "Invoke-WebRequest -Uri '%NSSM_URL%' -OutFile '%TEMP%\nssm.zip'"
    
    REM Extract
    powershell -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force"
    
    REM Copy the correct version (64-bit)
    copy "%TEMP%\nssm-2.24\win64\nssm.exe" "%NSSM_PATH%" >nul
    
    echo  [OK] NSSM installed.
) else (
    echo [1/4] NSSM already installed.
)

REM === STOP EXISTING SERVICE IF RUNNING ===
echo [2/4] Checking existing service...
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo  [*] Stopping existing service...
    "%NSSM_PATH%" stop %SERVICE_NAME% >nul 2>&1
    "%NSSM_PATH%" remove %SERVICE_NAME% confirm >nul 2>&1
    echo  [OK] Old service removed.
)

REM === INSTALL SERVICE ===
echo [3/4] Installing Windows Service...

REM Get Python path from venv
set "PYTHON_PATH=%INSTALL_PATH%\backend\venv\Scripts\python.exe"

REM Install service
"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%"
"%NSSM_PATH%" set %SERVICE_NAME% AppParameters "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%INSTALL_PATH%\backend"

REM Service settings
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "Attendance System"
"%NSSM_PATH%" set %SERVICE_NAME% Description "Face Recognition Attendance System - Port 8000"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_PATH%" set %SERVICE_NAME% ObjectName LocalSystem

REM Logging
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%INSTALL_PATH%\logs\service.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%INSTALL_PATH%\logs\service-error.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateBytes 1048576

REM Create logs directory
if not exist "%INSTALL_PATH%\logs" mkdir "%INSTALL_PATH%\logs"

echo  [OK] Service installed.

REM === START SERVICE ===
echo [4/4] Starting service...
"%NSSM_PATH%" start %SERVICE_NAME%

timeout /t 3 >nul

REM Check status
sc query %SERVICE_NAME% | findstr "RUNNING" >nul
if %errorLevel% equ 0 (
    echo  [OK] Service is running!
) else (
    echo  [!] Service may have failed to start. Check logs:
    echo      %INSTALL_PATH%\logs\service-error.log
)

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           SERVICE INSTALLATION COMPLETE              ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Service Name: %SERVICE_NAME%
echo  Status: Run 'sc query %SERVICE_NAME%' to check
echo.
echo  Commands:
echo    Start:   nssm start %SERVICE_NAME%
echo    Stop:    nssm stop %SERVICE_NAME%
echo    Status:  sc query %SERVICE_NAME%
echo    Remove:  nssm remove %SERVICE_NAME%
echo.
echo  Access: http://localhost:8000
echo  Logs:   %INSTALL_PATH%\logs\
echo.
pause

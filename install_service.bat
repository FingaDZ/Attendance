@echo off
setlocal enabledelayedexpansion

echo.
echo  ========================================================
echo       ATTENDANCE SYSTEM - SERVICE INSTALLER
echo       Installs as Windows Service
echo  ========================================================
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
set "NSSM_PATH=%INSTALL_PATH%\tools\nssm.exe"
set "SERVICE_NAME=AttendanceSystem"

REM === CREATE TOOLS DIRECTORY ===
if not exist "%INSTALL_PATH%\tools" mkdir "%INSTALL_PATH%\tools"
if not exist "%INSTALL_PATH%\logs" mkdir "%INSTALL_PATH%\logs"

REM === DOWNLOAD NSSM IF NOT EXISTS ===
if not exist "%NSSM_PATH%" (
    echo [1/4] Downloading NSSM...
    
    REM Download using PowerShell with better error handling
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ProgressPreference = 'SilentlyContinue'; " ^
        "try { " ^
        "  Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip' -UseBasicParsing; " ^
        "  Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm_extract' -Force; " ^
        "  Copy-Item '%TEMP%\nssm_extract\nssm-2.24\win64\nssm.exe' '%NSSM_PATH%' -Force; " ^
        "  Write-Host 'NSSM downloaded successfully'; " ^
        "} catch { " ^
        "  Write-Host 'Download failed, trying alternative...'; " ^
        "  Invoke-WebRequest -Uri 'https://github.com/kirillkovalenko/nssm/releases/download/2.24.101/nssm-2.24.101.zip' -OutFile '%TEMP%\nssm.zip' -UseBasicParsing; " ^
        "  Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm_extract' -Force; " ^
        "  Copy-Item '%TEMP%\nssm_extract\nssm-2.24.101\win64\nssm.exe' '%NSSM_PATH%' -Force; " ^
        "}"
    
    if not exist "%NSSM_PATH%" (
        echo  [ERROR] Failed to download NSSM. Please check internet connection.
        pause
        exit /b 1
    )
    echo  [OK] NSSM installed.
) else (
    echo [1/4] NSSM already installed.
)

REM === VERIFY NSSM EXISTS ===
if not exist "%NSSM_PATH%" (
    echo  [ERROR] NSSM file not found.
    pause
    exit /b 1
)
echo  [OK] NSSM verified.

REM === STOP EXISTING SERVICE IF RUNNING ===
echo [2/4] Checking existing service...
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo  [*] Stopping existing service...
    net stop %SERVICE_NAME% >nul 2>&1
    "%NSSM_PATH%" remove %SERVICE_NAME% confirm >nul 2>&1
    timeout /t 2 >nul
    echo  [OK] Old service removed.
)

REM === INSTALL SERVICE ===
echo [3/4] Installing Windows Service...

set "PYTHON_PATH=%INSTALL_PATH%\backend\venv\Scripts\python.exe"

REM Verify Python exists
if not exist "%PYTHON_PATH%" (
    echo  [ERROR] Python venv not found at %PYTHON_PATH%
    echo  Please run install_windows.bat first.
    pause
    exit /b 1
)

REM Install service using NSSM
"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "-m" "uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "8000"

REM Configure service
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%INSTALL_PATH%\backend"
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "Attendance System"
"%NSSM_PATH%" set %SERVICE_NAME% Description "Face Recognition Attendance System - Port 8000"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_PATH%" set %SERVICE_NAME% ObjectName LocalSystem

REM Logging configuration
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%INSTALL_PATH%\logs\service.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%INSTALL_PATH%\logs\service-error.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStdoutCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppStderrCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateOnline 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateBytes 5242880

REM Exit actions
"%NSSM_PATH%" set %SERVICE_NAME% AppExit Default Restart
"%NSSM_PATH%" set %SERVICE_NAME% AppRestartDelay 5000

echo  [OK] Service installed.

REM === START SERVICE ===
echo [4/4] Starting service...
net start %SERVICE_NAME%

timeout /t 3 >nul

REM Check status
sc query %SERVICE_NAME% | findstr "RUNNING" >nul
if %errorLevel% equ 0 (
    echo  [OK] Service is running!
) else (
    echo  [!] Service may have failed to start.
    echo  Checking logs...
    if exist "%INSTALL_PATH%\logs\service-error.log" (
        echo.
        echo  === Last 10 lines of error log ===
        powershell -Command "Get-Content '%INSTALL_PATH%\logs\service-error.log' -Tail 10"
    )
)

echo.
echo  ========================================================
echo            SERVICE INSTALLATION COMPLETE
echo  ========================================================
echo.
echo  Service Name: %SERVICE_NAME%
echo.
echo  Management Commands (run as Administrator):
echo    Start:    net start %SERVICE_NAME%
echo    Stop:     net stop %SERVICE_NAME%
echo    Status:   sc query %SERVICE_NAME%
echo    Restart:  net stop %SERVICE_NAME% ^& net start %SERVICE_NAME%
echo    Remove:   "%NSSM_PATH%" remove %SERVICE_NAME%
echo.
echo  Access URL: http://localhost:8000
echo  Logs:       %INSTALL_PATH%\logs\
echo.
pause

@echo off
echo.
echo  ========================================================
echo       ATTENDANCE SYSTEM - UNINSTALLER
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
set "SERVICE_NAME=AttendanceSystem"
set "NSSM_PATH=%INSTALL_PATH%\tools\nssm.exe"

echo  This will completely remove the Attendance System.
echo.
echo  WARNING: This will delete:
echo    - Windows Service
echo    - All application files
echo    - Database (attendance.db)
echo    - All logs
echo.
set /p CONFIRM="Are you sure? Type YES to confirm: "

if /i not "%CONFIRM%"=="YES" (
    echo  Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Stopping service...
net stop %SERVICE_NAME% >nul 2>&1
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    if exist "%NSSM_PATH%" (
        "%NSSM_PATH%" remove %SERVICE_NAME% confirm >nul 2>&1
    ) else (
        sc delete %SERVICE_NAME% >nul 2>&1
    )
    echo  [OK] Service removed.
) else (
    echo  [OK] No service found.
)

echo [2/4] Stopping Python processes...
taskkill /F /IM python.exe >nul 2>&1
echo  [OK] Processes stopped.

echo [3/4] Removing startup shortcut...
set "SHORTCUT_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Attendance System.lnk"
if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%" >nul 2>&1
    echo  [OK] Startup shortcut removed.
) else (
    echo  [OK] No startup shortcut found.
)

echo [4/4] Removing application files...
if exist "%INSTALL_PATH%" (
    rmdir /s /q "%INSTALL_PATH%"
    echo  [OK] Application files removed.
) else (
    echo  [OK] No application files found.
)

echo.
echo  ========================================================
echo            UNINSTALL COMPLETE
echo  ========================================================
echo.
echo  The Attendance System has been completely removed.
echo.
echo  Note: Python, Node.js, and Git were NOT uninstalled.
echo  To remove them, use Windows Settings > Apps.
echo.
pause

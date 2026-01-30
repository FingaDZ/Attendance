@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Attendance System - Windows Installer
echo   Version: 2.11.0
echo ========================================
echo.

REM === CHECK ADMIN RIGHTS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges.
    echo Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM === DEFINE INSTALL PATH ===
set "INSTALL_PATH=C:\Attendance"
if not "%~1"=="" set "INSTALL_PATH=%~1"

echo Install Path: %INSTALL_PATH%
echo.

REM ========================================
REM   STEP 1: CHECK/INSTALL PREREQUISITES
REM ========================================
echo [1/6] Checking prerequisites...
echo.

REM --- Check Python ---
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo   Python not found. Installing via winget...
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo   ERROR: Python installation failed.
        echo   Please install Python 3.11 manually from https://python.org
        pause
        exit /b 1
    )
    echo   Python installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   Python: %%v OK
)

REM --- Check Node.js ---
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo   Node.js not found. Installing via winget...
    winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo   ERROR: Node.js installation failed.
        echo   Please install Node.js LTS manually from https://nodejs.org
        pause
        exit /b 1
    )
    echo   Node.js installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f %%v in ('node --version 2^>^&1') do echo   Node.js: %%v OK
)

REM --- Check Git ---
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo   Git not found. Installing via winget...
    winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo   ERROR: Git installation failed.
        echo   Please install Git manually from https://git-scm.com
        pause
        exit /b 1
    )
    echo   Git installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f "tokens=3" %%v in ('git --version 2^>^&1') do echo   Git: %%v OK
)

echo.

REM ========================================
REM   STEP 2: CLONE OR UPDATE REPOSITORY
REM ========================================
echo [2/6] Getting source code...

if exist "%INSTALL_PATH%\.git" (
    echo   Existing installation found. Updating...
    cd /d "%INSTALL_PATH%"
    
    REM Backup database
    if exist "attendance.db" (
        for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
        set "BACKUP_NAME=attendance.db.backup.!dt:~0,8!_!dt:~8,6!"
        copy "attendance.db" "!BACKUP_NAME!" >nul
        echo   Database backed up: !BACKUP_NAME!
    )
    
    git fetch origin
    git reset --hard origin/master
) else (
    echo   Fresh installation...
    git clone https://github.com/FingaDZ/Attendance.git "%INSTALL_PATH%"
    cd /d "%INSTALL_PATH%"
)

echo   Source code ready.
echo.

REM ========================================
REM   STEP 3: SETUP BACKEND
REM ========================================
echo [3/6] Setting up Backend...

cd /d "%INSTALL_PATH%\backend"

if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
)

echo   Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

REM Verify InsightFace
python -c "import insightface; print('   InsightFace: OK')" 2>nul
if %errorLevel% neq 0 (
    echo   WARNING: InsightFace may need Visual Studio Build Tools.
    echo   Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

call deactivate
echo   Backend ready.
echo.

REM ========================================
REM   STEP 4: SETUP FRONTEND
REM ========================================
echo [4/6] Setting up Frontend...

cd /d "%INSTALL_PATH%\frontend"

echo   Installing Node.js dependencies...
call npm install --silent

echo   Building production bundle...
call npm run build

if not exist "dist\index.html" (
    echo   ERROR: Frontend build failed!
    pause
    exit /b 1
)

echo   Frontend ready.
echo.

REM ========================================
REM   STEP 5: CREATE STARTUP SHORTCUT
REM ========================================
echo [5/6] Creating startup shortcut...

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Attendance System.lnk"

REM Create VBScript to make shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%SHORTCUT_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%INSTALL_PATH%\start_system.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo   Auto-start shortcut created.
echo.

REM ========================================
REM   STEP 6: DISPLAY SUMMARY
REM ========================================
echo [6/6] Installation Complete!
echo.
echo ========================================
echo   INSTALLATION SUCCESSFUL!
echo ========================================
echo.
echo   Install Location: %INSTALL_PATH%
echo.
echo   To start the application:
echo     Double-click: %INSTALL_PATH%\start_system.bat
echo.
echo   The app will auto-start when Windows boots.
echo.
echo   FIRST RUN NOTE:
echo   The AI model (~400MB) will download automatically.
echo   This may take a few minutes on first start.
echo.
echo   CAMERA ACCESS:
echo   For LAN camera access, configure Chrome flag:
echo   chrome://flags/#unsafely-treat-insecure-origin-as-secure
echo.
echo ========================================
echo.
pause

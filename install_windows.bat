@echo off
setlocal enabledelayedexpansion

REM === PROGRESS BAR FUNCTION ===
REM Usage: call :progress PERCENT MESSAGE
goto :main

:progress
set "pct=%~1"
set "msg=%~2"
set "bar="
set /a "filled=pct/5"
set /a "empty=20-filled"
for /l %%i in (1,1,%filled%) do set "bar=!bar!#"
for /l %%i in (1,1,%empty%) do set "bar=!bar!-"
echo.
echo [%bar%] %pct%%% - %msg%
exit /b 0

:spinner
set "chars=|/-\"
set /a "idx=%1 %% 4"
set "char=!chars:~%idx%,1!"
<nul set /p "=%char%"
exit /b 0

:main
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     ATTENDANCE SYSTEM - WINDOWS INSTALLER            ║
echo  ║     Version: 2.12.0                                  ║
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

REM === DEFINE INSTALL PATH ===
set "INSTALL_PATH=C:\Attendance"
if not "%~1"=="" set "INSTALL_PATH=%~1"

echo  Install Path: %INSTALL_PATH%
echo.

REM ══════════════════════════════════════════════════════════
REM   STEP 1: CHECK/INSTALL PREREQUISITES (0% - 15%)
REM ══════════════════════════════════════════════════════════
call :progress 0 "Checking prerequisites..."

REM --- Check Python 3.11 ---
echo.
echo  [*] Checking Python 3.11...
py -3.11 --version >nul 2>&1
if %errorLevel% neq 0 (
    call :progress 5 "Installing Python 3.11..."
    echo.
    echo  [!] Python 3.11 not found. Installing via winget...
    echo  [!] NOTE: InsightFace requires Python 3.10 or 3.11 (NOT 3.12+)
    echo.
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo  [ERROR] Python 3.11 installation failed.
        pause
        exit /b 1
    )
    echo  [OK] Python 3.11 installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f "tokens=2" %%v in ('py -3.11 --version 2^>^&1') do echo  [OK] Python 3.11: %%v
)

call :progress 5 "Checking Node.js..."

REM --- Check Node.js ---
echo  [*] Checking Node.js...
node --version >nul 2>&1
if %errorLevel% neq 0 (
    call :progress 8 "Installing Node.js..."
    winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo  [ERROR] Node.js installation failed.
        pause
        exit /b 1
    )
    echo  [OK] Node.js installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f %%v in ('node --version 2^>^&1') do echo  [OK] Node.js: %%v
)

call :progress 10 "Checking Git..."

REM --- Check Git ---
echo  [*] Checking Git...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    call :progress 12 "Installing Git..."
    winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo  [ERROR] Git installation failed.
        pause
        exit /b 1
    )
    echo  [OK] Git installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f "tokens=3" %%v in ('git --version 2^>^&1') do echo  [OK] Git: %%v
)

call :progress 15 "Prerequisites OK"

REM ══════════════════════════════════════════════════════════
REM   STEP 2: CLONE OR UPDATE REPOSITORY (15% - 30%)
REM ══════════════════════════════════════════════════════════
call :progress 15 "Getting source code from GitHub..."

if exist "%INSTALL_PATH%\.git" (
    echo.
    echo  [*] Existing installation found. Updating...
    cd /d "%INSTALL_PATH%"
    
    REM Backup database
    if exist "attendance.db" (
        call :progress 18 "Backing up database..."
        for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
        set "BACKUP_NAME=attendance.db.backup.!dt:~0,8!_!dt:~8,6!"
        copy "attendance.db" "!BACKUP_NAME!" >nul
        echo  [OK] Database backed up: !BACKUP_NAME!
    )
    
    call :progress 22 "Fetching updates..."
    git fetch origin
    git reset --hard origin/master
) else (
    echo.
    echo  [*] Fresh installation. Cloning repository...
    call :progress 20 "Cloning repository..."
    git clone https://github.com/FingaDZ/Attendance.git "%INSTALL_PATH%"
    cd /d "%INSTALL_PATH%"
)

call :progress 30 "Source code ready"
echo  [OK] Source code ready.

REM ══════════════════════════════════════════════════════════
REM   STEP 3: SETUP BACKEND (30% - 60%)
REM ══════════════════════════════════════════════════════════
call :progress 30 "Setting up Backend..."

cd /d "%INSTALL_PATH%\backend"

if not exist "venv" (
    call :progress 32 "Creating Python virtual environment..."
    echo.
    echo  [*] Creating virtual environment with Python 3.11...
    py -3.11 -m venv venv
)

call :progress 35 "Upgrading pip..."
echo  [*] Upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

call :progress 40 "Installing Python dependencies (this may take several minutes)..."
echo.
echo  [*] Installing Python dependencies...
echo  [*] This includes: FastAPI, Uvicorn, InsightFace, OpenCV, etc.
echo.

REM Install with visible output for progress
pip install -r requirements.txt 2>&1 | findstr /i "Installing Collecting Building"

call :progress 55 "Verifying InsightFace installation..."

REM Verify InsightFace
echo.
echo  [*] Verifying InsightFace...
python -c "import insightface; print('  [OK] InsightFace loaded successfully')" 2>nul
if %errorLevel% neq 0 (
    echo  [!] WARNING: InsightFace may need Visual Studio Build Tools.
    echo  [!] Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

call deactivate
call :progress 60 "Backend ready"
echo  [OK] Backend ready.

REM ══════════════════════════════════════════════════════════
REM   STEP 4: SETUP FRONTEND (60% - 85%)
REM ══════════════════════════════════════════════════════════
call :progress 60 "Setting up Frontend..."

cd /d "%INSTALL_PATH%\frontend"

call :progress 65 "Installing Node.js dependencies..."
echo.
echo  [*] Installing Node.js dependencies...
call npm install 2>&1 | findstr /i "added packages"

call :progress 75 "Building production bundle..."
echo.
echo  [*] Building production bundle with Vite...
call npm run build

if not exist "dist\index.html" (
    echo  [ERROR] Frontend build failed!
    pause
    exit /b 1
)

call :progress 85 "Frontend ready"
echo  [OK] Frontend ready.

REM ══════════════════════════════════════════════════════════
REM   STEP 5: CREATE STARTUP SHORTCUT (85% - 95%)
REM ══════════════════════════════════════════════════════════
call :progress 85 "Creating auto-start shortcut..."

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Attendance System.lnk"

echo  [*] Creating startup shortcut...

REM Create VBScript to make shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%SHORTCUT_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%INSTALL_PATH%\start_system.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

call :progress 95 "Shortcut created"
echo  [OK] Auto-start shortcut created.

REM ══════════════════════════════════════════════════════════
REM   STEP 6: COMPLETE (100%)
REM ══════════════════════════════════════════════════════════
call :progress 100 "Installation Complete!"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           INSTALLATION SUCCESSFUL!                   ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Install Location: %INSTALL_PATH%
echo.
echo  ┌─────────────────────────────────────────────────────┐
echo  │ TO START THE APPLICATION:                          │
echo  │   Double-click: %INSTALL_PATH%\start_system.bat           │
echo  │                                                     │
echo  │ AUTO-START:                                         │
echo  │   The app will start automatically when Windows    │
echo  │   boots.                                            │
echo  │                                                     │
echo  │ FIRST RUN NOTE:                                     │
echo  │   The AI model (~400MB) downloads automatically.   │
echo  │   This may take a few minutes on first start.      │
echo  │                                                     │
echo  │ CAMERA ACCESS (LAN):                                │
echo  │   Configure Chrome flag:                            │
echo  │   chrome://flags/#unsafely-treat-insecure-origin   │
echo  └─────────────────────────────────────────────────────┘
echo.
pause

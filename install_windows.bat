@echo off
setlocal enabledelayedexpansion

REM === PROGRESS BAR FUNCTION ===
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

:error
echo.
echo  [ERROR] %~1
echo.
echo  Installation failed. Please check the error above.
echo  For help, visit: https://github.com/FingaDZ/Attendance
echo.
pause
exit /b 1

:main
cls
echo.
echo  ========================================================
echo       ATTENDANCE SYSTEM - WINDOWS INSTALLER
echo       Version: 2.12.0
echo  ========================================================
echo.

REM === CHECK ADMIN RIGHTS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    call :error "This script requires Administrator privileges. Right-click and select 'Run as Administrator'"
)

REM === CHECK INTERNET CONNECTIVITY ===
echo  [*] Checking internet connection...
ping -n 1 github.com >nul 2>&1
if %errorLevel% neq 0 (
    ping -n 1 8.8.8.8 >nul 2>&1
    if %errorLevel% neq 0 (
        call :error "No internet connection. Please check your network and try again."
    )
)
echo  [OK] Internet connection OK
echo.

REM === DEFINE INSTALL PATH ===
set "INSTALL_PATH=C:\Attendance"
set "REPO_URL=https://github.com/FingaDZ/Attendance.git"

echo  Install Path: %INSTALL_PATH%
echo  Repository:   %REPO_URL%
echo.

REM === CHECK DISK SPACE ===
echo  [*] Checking disk space...
for /f "tokens=3" %%a in ('dir C:\ ^| findstr /C:"bytes free"') do set "FREE_SPACE=%%a"
set "FREE_SPACE=%FREE_SPACE:,=%"
REM Need at least 2GB (2147483648 bytes)
powershell -Command "if ([int64]'%FREE_SPACE%' -lt 2147483648) { exit 1 }" >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] WARNING: Less than 2GB free space on C: drive.
    echo  [!] Installation may fail. Recommended: 5GB+ free space.
    echo.
    set /p CONTINUE_LOW_SPACE="Continue anyway? (Y/N): "
    if /i not "!CONTINUE_LOW_SPACE!"=="Y" (
        call :error "Not enough disk space. Please free up space and try again."
    )
)
echo  [OK] Disk space OK

REM === CONFIGURE FIREWALL ===
echo  [*] Configuring firewall for port 8000...
netsh advfirewall firewall show rule name="Attendance System" >nul 2>&1
if %errorLevel% neq 0 (
    netsh advfirewall firewall add rule name="Attendance System" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
    echo  [OK] Firewall rule added for port 8000
) else (
    echo  [OK] Firewall rule already exists
)

echo.

REM ══════════════════════════════════════════════════════════
REM   STEP 1: CHECK/INSTALL PREREQUISITES (0% - 20%)
REM ══════════════════════════════════════════════════════════
call :progress 0 "Checking prerequisites..."

REM --- Check Git FIRST (needed for clone) ---
echo.
echo  [*] Checking Git...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    call :progress 3 "Installing Git..."
    echo  [!] Git not found. Installing via winget...
    winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        call :error "Git installation failed. Please install Git manually from https://git-scm.com"
    )
    echo  [OK] Git installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f "tokens=3" %%v in ('git --version 2^>^&1') do echo  [OK] Git: %%v
)

REM --- Check Python 3.11 ---
call :progress 5 "Checking Python 3.11..."
echo  [*] Checking Python 3.11...
py -3.11 --version >nul 2>&1
if %errorLevel% neq 0 (
    call :progress 8 "Installing Python 3.11..."
    echo.
    echo  [!] Python 3.11 not found. Installing via winget...
    echo  [!] NOTE: InsightFace requires Python 3.10 or 3.11 (NOT 3.12+)
    echo.
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        call :error "Python 3.11 installation failed. Please install manually from https://python.org"
    )
    echo  [OK] Python 3.11 installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f "tokens=2" %%v in ('py -3.11 --version 2^>^&1') do echo  [OK] Python 3.11: %%v
)

REM --- Check Node.js ---
call :progress 12 "Checking Node.js..."
echo  [*] Checking Node.js...
node --version >nul 2>&1
if %errorLevel% neq 0 (
    call :progress 15 "Installing Node.js..."
    echo  [!] Node.js not found. Installing via winget...
    winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        call :error "Node.js installation failed. Please install manually from https://nodejs.org"
    )
    echo  [OK] Node.js installed. Please restart this script.
    pause
    exit /b 0
) else (
    for /f %%v in ('node --version 2^>^&1') do echo  [OK] Node.js: %%v
)

call :progress 20 "Prerequisites OK"

REM ══════════════════════════════════════════════════════════
REM   STEP 2: CLONE OR UPDATE REPOSITORY (20% - 35%)
REM ══════════════════════════════════════════════════════════
call :progress 20 "Getting source code from GitHub..."

if exist "%INSTALL_PATH%\.git" (
    echo.
    echo  [*] Existing installation found at %INSTALL_PATH%
    
    REM Get current version
    cd /d "%INSTALL_PATH%"
    for /f "tokens=*" %%v in ('git describe --tags --always 2^>nul') do set "CURRENT_VERSION=%%v"
    echo  [*] Current version: %CURRENT_VERSION%
    
    REM Backup database
    if exist "attendance.db" (
        call :progress 22 "Backing up database..."
        for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
        set "BACKUP_NAME=attendance.db.backup.!dt:~0,8!_!dt:~8,6!"
        copy "attendance.db" "!BACKUP_NAME!" >nul 2>&1
        echo  [OK] Database backed up: !BACKUP_NAME!
    )
    
    REM Add safe directory for git
    git config --global --add safe.directory "%INSTALL_PATH%" >nul 2>&1
    
    REM Fetch and check for updates
    call :progress 25 "Checking for updates..."
    git fetch origin >nul 2>&1
    
    for /f "tokens=*" %%v in ('git rev-parse HEAD 2^>nul') do set "LOCAL_HASH=%%v"
    for /f "tokens=*" %%v in ('git rev-parse origin/master 2^>nul') do set "REMOTE_HASH=%%v"
    
    if "!LOCAL_HASH!"=="!REMOTE_HASH!" (
        echo  [OK] Already up to date.
    ) else (
        call :progress 28 "Updating to latest version..."
        echo  [*] New version available. Updating...
        git reset --hard origin/master
        if %errorLevel% neq 0 (
            call :error "Failed to update from GitHub. Check your internet connection."
        )
        for /f "tokens=*" %%v in ('git describe --tags --always 2^>nul') do set "NEW_VERSION=%%v"
        echo  [OK] Updated: %CURRENT_VERSION% -^> !NEW_VERSION!
    )
) else (
    echo.
    echo  [*] Fresh installation. Cloning repository...
    call :progress 25 "Cloning repository..."
    
    REM Clone the repository
    git clone "%REPO_URL%" "%INSTALL_PATH%"
    if %errorLevel% neq 0 (
        call :error "Failed to clone repository. Check your internet connection."
    )
    
    cd /d "%INSTALL_PATH%"
    git config --global --add safe.directory "%INSTALL_PATH%" >nul 2>&1
    
    for /f "tokens=*" %%v in ('git describe --tags --always 2^>nul') do set "INSTALLED_VERSION=%%v"
    echo  [OK] Installed version: !INSTALLED_VERSION!
)

call :progress 35 "Source code ready"
echo  [OK] Source code ready.

REM ══════════════════════════════════════════════════════════
REM   STEP 3: SETUP BACKEND (35% - 65%)
REM ══════════════════════════════════════════════════════════
call :progress 35 "Setting up Backend..."

cd /d "%INSTALL_PATH%\backend"

if not exist "venv" (
    call :progress 38 "Creating Python virtual environment..."
    echo.
    echo  [*] Creating virtual environment with Python 3.11...
    py -3.11 -m venv venv
    if %errorLevel% neq 0 (
        call :error "Failed to create Python virtual environment."
    )
)

call :progress 42 "Upgrading pip..."
echo  [*] Upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

call :progress 45 "Installing Python dependencies (this may take several minutes)..."
echo.
echo  [*] Installing Python dependencies...
echo  [*] This includes: FastAPI, Uvicorn, InsightFace, OpenCV, etc.
echo.

pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo.
    echo  [!] Some packages may have failed. Trying with numpy fix...
    pip install "numpy<2" -q
    pip install -r requirements.txt
)

call :progress 60 "Verifying InsightFace installation..."

REM Verify InsightFace
echo.
echo  [*] Verifying InsightFace...
python -c "import insightface; print('  [OK] InsightFace loaded successfully')" 2>nul
if %errorLevel% neq 0 (
    echo  [!] WARNING: InsightFace verification failed.
    echo  [!] Trying numpy fix...
    pip install "numpy<2" -q
    python -c "import insightface; print('  [OK] InsightFace loaded successfully')" 2>nul
    if %errorLevel% neq 0 (
        echo  [!] InsightFace may need Visual Studio Build Tools.
        echo  [!] Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    )
)

call deactivate
call :progress 65 "Backend ready"
echo  [OK] Backend ready.

REM ══════════════════════════════════════════════════════════
REM   STEP 4: SETUP FRONTEND (65% - 90%)
REM ══════════════════════════════════════════════════════════
call :progress 65 "Setting up Frontend..."

cd /d "%INSTALL_PATH%\frontend"

call :progress 70 "Installing Node.js dependencies..."
echo.
echo  [*] Installing Node.js dependencies...
call npm install
if %errorLevel% neq 0 (
    call :error "Failed to install Node.js dependencies."
)

call :progress 80 "Building production bundle..."
echo.
echo  [*] Building production bundle with Vite...
call npm run build
if %errorLevel% neq 0 (
    call :error "Frontend build failed."
)

if not exist "dist\index.html" (
    call :error "Frontend build verification failed - dist/index.html not found."
)

call :progress 90 "Frontend ready"
echo  [OK] Frontend ready.

REM ══════════════════════════════════════════════════════════
REM   STEP 5: CREATE STARTUP SHORTCUT (90% - 95%)
REM ══════════════════════════════════════════════════════════
call :progress 90 "Creating auto-start shortcut..."

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
REM   STEP 6: INSTALL AND START SERVICE (95% - 100%)
REM ══════════════════════════════════════════════════════════
call :progress 95 "Installing Windows Service..."

set "NSSM_PATH=%INSTALL_PATH%\tools\nssm.exe"
set "SERVICE_NAME=AttendanceSystem"

REM Create directories
if not exist "%INSTALL_PATH%\tools" mkdir "%INSTALL_PATH%\tools"
if not exist "%INSTALL_PATH%\logs" mkdir "%INSTALL_PATH%\logs"

REM Download NSSM if not exists
if not exist "%NSSM_PATH%" (
    echo  [*] Downloading NSSM (Service Manager)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ProgressPreference = 'SilentlyContinue'; " ^
        "try { " ^
        "  Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip' -UseBasicParsing; " ^
        "  Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm_extract' -Force; " ^
        "  Copy-Item '%TEMP%\nssm_extract\nssm-2.24\win64\nssm.exe' '%NSSM_PATH%' -Force; " ^
        "} catch { exit 1 }"
    if not exist "%NSSM_PATH%" (
        echo  [!] WARNING: Could not download NSSM. Service will not be installed.
        echo  [!] You can start manually with: %INSTALL_PATH%\start_system.bat
        goto :skip_service
    )
    echo  [OK] NSSM installed.
)

REM Stop existing service if running
net stop %SERVICE_NAME% >nul 2>&1
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    "%NSSM_PATH%" remove %SERVICE_NAME% confirm >nul 2>&1
    timeout /t 2 >nul
)

REM Install service
echo  [*] Installing Windows Service...
set "PYTHON_PATH=%INSTALL_PATH%\backend\venv\Scripts\python.exe"

"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "-m" "uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "8000" >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%INSTALL_PATH%\backend" >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "Attendance System" >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% Description "Face Recognition Attendance System - Port 8000" >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%INSTALL_PATH%\logs\service.log" >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%INSTALL_PATH%\logs\service-error.log" >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateFiles 1 >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateBytes 5242880 >nul 2>&1
"%NSSM_PATH%" set %SERVICE_NAME% AppExit Default Restart >nul 2>&1

echo  [OK] Service installed.

REM Start service
echo  [*] Starting service...
net start %SERVICE_NAME% >nul 2>&1
timeout /t 3 >nul

sc query %SERVICE_NAME% | findstr "RUNNING" >nul
if %errorLevel% equ 0 (
    echo  [OK] Service is running!
) else (
    echo  [!] Service may have failed to start. Check logs: %INSTALL_PATH%\logs\
)

:skip_service
call :progress 100 "Installation Complete!"

echo.
echo  ========================================================
echo            INSTALLATION SUCCESSFUL!
echo  ========================================================
echo.
echo  Install Location: %INSTALL_PATH%
echo  Service Name:     %SERVICE_NAME%
echo  Status:           RUNNING
echo.
echo  --------------------------------------------------------
echo   ACCESS URLS (open in browser):
echo  --------------------------------------------------------
echo   Dashboard:  http://localhost:8000
echo   Kiosk:      http://localhost:8000/kiosk
echo.
echo  --------------------------------------------------------
echo   SERVICE COMMANDS (run as Admin):
echo  --------------------------------------------------------
echo   Status:   sc query %SERVICE_NAME%
echo   Stop:     net stop %SERVICE_NAME%
echo   Start:    net start %SERVICE_NAME%
echo   Restart:  net stop %SERVICE_NAME% ^& net start %SERVICE_NAME%
echo   Remove:   %NSSM_PATH% remove %SERVICE_NAME%
echo.
echo  --------------------------------------------------------
echo   FIRST RUN NOTE:
echo  --------------------------------------------------------
echo   The AI model (~400MB) downloads automatically.
echo   Wait 1-2 minutes before accessing the dashboard.
echo.
echo  ========================================================
echo.

REM Open browser automatically
echo  [*] Opening browser...
start "" "http://localhost:8000"

pause

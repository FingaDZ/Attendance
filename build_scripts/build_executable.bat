@echo off
REM ========================================
REM   FaceAttendanceAI - Build Script v2
REM   Uses existing backend environment
REM ========================================

echo.
echo ========================================
echo   FaceAttendanceAI Build Process
echo ========================================
echo.

REM Check if backend venv exists
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment not found!
    echo Please ensure backend\venv exists with all dependencies installed.
    pause
    exit /b 1
)

echo [1/5] Using existing backend environment...
.\backend\venv\Scripts\python.exe --version
echo.

REM Step 2: Verify frontend is built
echo [2/5] Checking frontend build...
if not exist "frontend\dist" (
    echo [ERROR] Frontend not built!
    echo Please run: cd frontend ^&^& npm run build
    pause
    exit /b 1
)
echo    Frontend dist found!
echo.

REM Step 3: Install PyInstaller in backend env
echo [3/5] Installing PyInstaller...
.\backend\venv\Scripts\python.exe -m pip install --quiet pyinstaller>=6.0
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller!
    pause
    exit /b 1
)
echo    PyInstaller installed!
echo.

REM Step 4: Generate spec file with correct paths
echo [4/5] Generating PyInstaller configuration...
.\backend\venv\Scripts\python.exe build_scripts\build_config.py
if errorlevel 1 (
    echo [ERROR] Failed to generate configuration!
    pause
    exit /b 1
)
echo.

REM Step 5: Run PyInstaller
echo [5/5] Building executable with PyInstaller...
echo    This may take 5-10 minutes...
echo    Please be patient...
echo.

.\backend\venv\Scripts\python.exe -m PyInstaller --clean build_scripts\FaceAttendanceAI.spec
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)
echo.
echo    Executable created!
echo.

REM Step 6: Copy to output location
echo [6/6] Copying executable to F:\Code\...
if exist "dist\FaceAttendanceAI.exe" (
    copy /Y "dist\FaceAttendanceAI.exe" "F:\Code\FaceAttendanceAI.exe"
    if errorlevel 1 (
        echo [WARNING] Could not copy to F:\Code\
        echo    Executable is available at: %cd%\dist\FaceAttendanceAI.exe
    ) else (
        echo    ✅ Copied to: F:\Code\FaceAttendanceAI.exe
    )
) else (
    echo [ERROR] Executable not found in dist folder!
    pause
    exit /b 1
)
echo.

REM Display results
echo ========================================
echo   BUILD COMPLETE!
echo ========================================
echo.
echo Executable location: F:\Code\FaceAttendanceAI.exe
echo.
echo File size:
for %%A in ("F:\Code\FaceAttendanceAI.exe") do echo    %%~zA bytes (%%~zAMB)
echo.
echo ========================================
echo   How to use:
echo   1. Double-click FaceAttendanceAI.exe
echo   2. Wait for browser to open
echo   3. Access at http://localhost:8000
echo ========================================
echo.
echo Press any key to exit...
pause >nul

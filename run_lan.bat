@echo off
echo Starting Attendance System for LAN Access (HTTPS)...
echo Local IP: 192.168.66.102
echo.
echo Starting Backend...
start "Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo.
echo Starting Frontend (HTTPS)...
start "Frontend" cmd /k "cd frontend && npm run dev"
echo.
echo Access the app at: https://192.168.66.102:5173
echo.
echo IMPORTANT: You will see a "Not Secure" warning.
echo Click "Advanced" -> "Proceed to..." to access the site.
echo This is required for camera access on mobile.
pause

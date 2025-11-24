# Attendance System - Windows 10/11 Deployment Guide

## Prerequisites

Before starting, ensure you have the following installed:

1.  **Python 3.10 or 3.11**
    *   Download: [python.org](https://www.python.org/downloads/)
    *   **IMPORTANT**: Check "Add Python to PATH" during installation.

2.  **Node.js 20.x (LTS)**
    *   Download: [nodejs.org](https://nodejs.org/)
    *   This includes `npm`.

3.  **Git**
    *   Download: [git-scm.com](https://git-scm.com/downloads)

4.  **Visual Studio Build Tools** (Required for InsightFace/InsightFace dependencies)
    *   Download: [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
    *   During installation, select **"Desktop development with C++"**.

---

## Step 1: Clone the Repository

Open PowerShell or Command Prompt and run:

```powershell
cd C:\path\to\your\projects
git clone https://github.com/FingaDZ/Attendance.git
cd Attendance
```

---

## Step 2: Setup Backend

1.  **Create Virtual Environment**:
    ```powershell
    cd backend
    python -m venv venv
    ```

2.  **Activate Virtual Environment**:
    ```powershell
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```powershell
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  **Verify Installation**:
    ```powershell
    python -c "import insightface; print('InsightFace OK')"
    ```

---

## Step 3: Setup Frontend

1.  **Navigate to Frontend Directory**:
    ```powershell
    cd ..\frontend
    ```

2.  **Install Dependencies**:
    ```powershell
    npm install
    ```

3.  **Configure API URL (Optional)**:
    *   By default, the frontend expects the backend at `/api` (via proxy) or `http://localhost:8000`.
    *   If running in production mode without a proxy, edit `src\api.js`:
        ```javascript
        baseURL: 'http://localhost:8000',
        ```

4.  **Build for Production**:
    ```powershell
    npm run build
    ```

---

## Step 4: Running the Application

You have two options: running in development mode (easier for testing) or production mode.

### Option A: Development Mode (Recommended for local use)

1.  **Start Backend**:
    Open a new terminal:
    ```powershell
    cd backend
    .\venv\Scripts\activate
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    > **Note**: The first run will download the `buffalo_l` model (~400MB). This may take a few minutes.

2.  **Start Frontend**:
    Open a second terminal:
    ```powershell
    cd frontend
    npm run dev
    ```
    Access at: `http://localhost:5173`

### Option B: Production Mode (Using a simple script)

Create a file named `run_app.bat` in the root folder:

```batch
@echo off
start "Backend" cmd /k "cd backend & venv\Scripts\activate & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "Frontend" cmd /k "cd frontend & npm run preview -- --port 3000"
echo Application started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
pause
```

Run `run_app.bat` to start both services.

---

## Step 5: Auto-Start on Boot (Optional)

To start the application automatically when Windows starts:

1.  Press `Win + R`, type `shell:startup`, and press Enter.
2.  Create a shortcut to your `run_app.bat` file in this folder.

---

## Troubleshooting

### "Microsoft Visual C++ 14.0 or greater is required"
*   **Solution**: Install **Visual Studio Build Tools** and ensure "Desktop development with C++" is checked.

### "ImportError: DLL load failed" (OpenCV/Numpy)
*   **Solution**: Reinstall the package:
    ```powershell
    pip uninstall opencv-python numpy
    pip install opencv-python numpy
    ```

### Frontend shows "Network Error"
*   Ensure the backend is running on port 8000.
*   Check `frontend\src\api.js` to ensure `baseURL` matches your backend URL.

### InsightFace Model Download Issues
*   On first run, the backend downloads models to `%USERPROFILE%\.insightface\models`.
*   If it fails, download `buffalo_s.zip` manually from the InsightFace GitHub releases, extract it, and place it in that folder.

---

## 🔄 Updating an Existing Installation

If you already have the Attendance system installed and want to update to the latest version:

### Step 1: Backup Current Installation

```powershell
# Backup database
Copy-Item attendance.db -Destination "attendance.db.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Optional: Backup entire folder
Compress-Archive -Path . -DestinationPath "..\attendance_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
```

### Step 2: Stop Running Services

If you have the application running, stop it:
- Close all terminal windows running the backend/frontend
- Or press `Ctrl+C` in each terminal

### Step 3: Update Code

```powershell
# Navigate to project directory
cd C:\path\to\Attendance

# Stash any local changes (if any)
git stash

# Pull latest code
git pull origin master

# If you had local changes, reapply them
# git stash pop
```

### Step 4: Update Backend Dependencies

```powershell
cd backend
.\venv\Scripts\activate

# Update dependencies
pip install --upgrade pip
pip install -r requirements.txt

deactivate
```

### Step 5: Update Frontend Dependencies

```powershell
cd ..\frontend

# Update dependencies (optional, only if package.json changed)
npm install

# Rebuild production build
npm run build
```

### Step 6: Restart Application

Run your application as usual:
- Use `run_app.bat` if you created it
- Or manually start backend and frontend in separate terminals

### Quick Update Script

Create a file `update_attendance.bat` in the root folder:

```batch
@echo off
echo === Attendance System Update ===

echo Backing up database...
copy attendance.db attendance.db.backup.%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%

echo Pulling latest code...
git pull origin master

echo Updating backend...
cd backend
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
call deactivate

echo Updating frontend...
cd ..\frontend
call npm install
call npm run build

echo === Update Complete ===
echo You can now run the application with run_app.bat
pause
```

Run updates:
```powershell
.\update_attendance.bat
```

---

## 🔌 API Integration

The system provides a REST API for external integrations. See [API_INTEGRATION.md](../API_INTEGRATION.md) for complete documentation.

**Access API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Example: Get Employees**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/employees/" -Method Get
```

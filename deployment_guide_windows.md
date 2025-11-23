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

## 🔌 API Integration

The system provides a REST API for external integrations. See [API_INTEGRATION.md](../API_INTEGRATION.md) for complete documentation.

**Access API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Example: Get Employees**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/employees/" -Method Get
```

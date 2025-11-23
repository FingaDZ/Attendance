# 📸 AI Face Recognition Attendance System

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Node.js](https://img.shields.io/badge/node-20.x-green)
![React](https://img.shields.io/badge/react-18-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688)

A robust, high-accuracy attendance system powered by **InsightFace (ArcFace)** and **FastAPI**. Designed for real-time face recognition across multiple cameras with advanced preprocessing for lighting and camera variations.

---

## ✨ Key Features

### 🧠 Advanced Face Recognition
*   **High Accuracy**: Uses **ArcFace** embeddings (InsightFace) for state-of-the-art recognition.
*   **Cross-Camera Support**: Optimized to recognize faces across different camera types (Webcam ↔ Mobile).
*   **Smart Preprocessing**:
    *   Automatic eye alignment and rotation.
    *   Consistent 200x200px face cropping.
    *   **Lighting Invariance**: Uses grayscale processing for secondary photos to handle varying light conditions.
    *   Gentle CLAHE enhancement for detail preservation.

### 👥 Employee Management
*   **Multi-Photo Registration**: Captures 3 angles/variations per employee for robust matching.
*   **PIN Backup**: Secure PIN verification fallback if face recognition fails.
*   **Department & Role Tracking**: Organize employees by department.

### 📹 Camera & Monitoring
*   **Multi-Camera Support**: Connect multiple RTSP streams or USB webcams.
*   **Live View**: Real-time video feed with bounding boxes and confidence scores.
*   **Camera Management**: Add, remove, and toggle cameras dynamically.

### 📊 Dashboard & Reporting
*   **Real-time Logs**: View attendance events (Entry/Exit) as they happen.
*   **Smart Logic**: Automatically determines Entry vs. Exit based on previous logs.
*   **Work Time Calculation**: Tracks total minutes worked per day.
*   **Exportable Reports**: Download attendance data in **Excel** or **PDF** formats.

---

## 🛠️ Tech Stack

### Backend
*   **Framework**: FastAPI (Python)
*   **AI/ML**: InsightFace, ONNX Runtime, OpenCV
*   **Database**: SQLite (via SQLAlchemy)
*   **Server**: Uvicorn

### Frontend
*   **Framework**: React (Vite)
*   **Styling**: TailwindCSS
*   **HTTP Client**: Axios
*   **Icons**: Lucide React

---

## 🚀 Installation & Deployment

We provide detailed guides for different environments:

### 🐧 [Ubuntu / Linux Deployment Guide](./deployment_guide.md)
Complete guide for deploying on Ubuntu 22.04 servers, including:
*   System dependencies (Python 3.10, Node.js 20)
*   Systemd service configuration (Auto-start)
*   Nginx Proxy Manager integration (HTTPS)

### 🪟 [Windows Deployment Guide](./deployment_guide_windows.md)
Guide for running locally or on Windows servers:
*   Prerequisites (Visual Studio Build Tools)
*   PowerShell installation scripts
*   Production & Development modes

---

## 📖 Usage Guide

### 1. Initial Setup
1.  Deploy the application using one of the guides above.
2.  Access the web interface (default: `http://localhost:3000` or your domain).

### 2. Registering Employees
1.  Go to the **Employees** page.
2.  Click **"Add Employee"**.
3.  Enter details (Name, Department, PIN).
4.  **Capture Photos (Critical Step)**:
    *   **Focus**: Position the face strictly within the guide circle.
    *   **3 Variations**: Take 3 photos to cover different looks (e.g., with/without glasses, slight angle changes).
    *   **Lighting**: Ensure even lighting on the face. Avoid strong backlighting or deep shadows.
    *   **Photo 2 (B&W)**: The second photo is automatically saved in **Black & White**. This helps the AI recognize faces under different colored lighting conditions.
    *   **Recommendation**: Use a neutral background. Avoid blurring.
5.  Click **Save**.
    *   *Tip: You can update photos later directly from the Employee List by clicking the Edit icon.*

### 3. Taking Attendance (Live View)
*   **Process**: The employee simply looks at the camera.
    *   **1st Recognition**: Logs **ENTRY**.
    *   **2nd Recognition**: Logs **EXIT**.
*   **Feedback**: A **voice message** will confirm the action (e.g., "Welcome, [Name]" or "Goodbye, [Name]").
*   **Security**: The system requires a high precision match (>90%). Scanned photos or phone screens may not pass verification.

### 4. Data & Reports
*   **Logs**: All events are stored in the database.
*   **Exports**: Download data in **Excel** or **CSV** formats from the Reports page.
*   **Integration**: The system provides an API for integration with external HR systems or apps.

---

## ⚠️ Database & Maintenance

**Current Database**: `SQLite`

This system uses SQLite for simplicity and portability. While robust for small to medium deployments, it may experience performance degradation with extremely large datasets (millions of logs).

**Recommendation**:
To maintain optimal speed, we recommend setting up a maintenance task (Cron Job) to archive or delete logs older than **13 months**.

**Example Maintenance Script (Linux):**
```bash
# Delete logs older than 395 days (13 months)
sqlite3 /opt/Attendance/attendance.db "DELETE FROM logs WHERE timestamp < datetime('now', '-395 days');"
```

---

## 📦 Version History

### v1.1.0 (Current)
*   **UI/UX**: Full Responsive Design (Mobile/Tablet support).
*   **Feature**: Mobile Drawer Navigation & Adaptive Grids.
*   **Fix**: Corrected camera aspect ratio distortion during registration.
*   **Optimization**: Improved face positioning guides for mobile & desktop.

### v1.0.0
*   **Core**: Initial release with InsightFace integration.
*   **Feature**: Multi-photo registration (3 photos).
*   **Optimization**: Advanced preprocessing pipeline (Align, Crop, Resize, CLAHE).
*   **Optimization**: Grayscale processing for lighting invariance.
*   **UI**: Modern React Dashboard with Dark Mode support.
*   **Deployment**: Added Systemd and Windows deployment support.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# 📸 AI Face Recognition Attendance System

![Version](https://img.shields.io/badge/version-1.5.0-blue.svg)
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

## 🔄 Updating the System

If you already have Attendance installed and want to update to the latest version:

### Ubuntu/Linux
```bash
cd /opt/Attendance
sudo /opt/update_attendance.sh
```

### Windows
```powershell
cd C:\path\to\Attendance
.\update_attendance.bat
```

See the deployment guides for detailed update procedures:
- [Ubuntu Update Guide](./deployment_guide.md#-updating-an-existing-installation)
- [Windows Update Guide](./deployment_guide_windows.md#-updating-an-existing-installation)

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
*   **Security**: The system requires a high precision match (>87%). Scanned photos or phone screens may not pass verification.

### 4. Data & Reports
*   **Logs**: All events are stored in the database.
*   **Exports**: Download data in **Excel** or **CSV** formats from the Reports page.
*   **Integration**: The system provides an API for integration with external HR systems or apps.

### 5. API Integration

The system provides a comprehensive REST API for external integrations. See **[API_INTEGRATION.md](./API_INTEGRATION.md)** for complete documentation.

**Quick Example:**
```python
import requests

# Get all employees
response = requests.get("http://localhost:8000/api/employees/")
employees = response.json()

# Get today's attendance logs
from datetime import date
today = date.today().isoformat()
response = requests.get(
    "http://localhost:8000/api/attendance/",
    params={"start_date": today, "end_date": today}
)
logs = response.json()
```

**Interactive Documentation:**
- Swagger UI: `http://your-server:8000/docs`
- ReDoc: `http://your-server:8000/redoc`

---

## 📹 Camera Setup Guide

### Adding a Webcam
1. Go to **Settings** → **Camera Management**
2. Click **"Add Camera"**
3. Enter:
   - **Name**: "Webcam" (or any descriptive name)
   - **Source**: `0` (for default webcam) or `1`, `2`, etc. for additional USB cameras
4. Click **Save**
5. The camera will start automatically

### Adding an IP Camera (RTSP)
1. Go to **Settings** → **Camera Management**
2. Click **"Add Camera"**
3. Enter:
   - **Name**: "Entrance Camera" (or any descriptive name)
   - **Source**: RTSP URL

**RTSP URL Format Examples:**

**Dahua Cameras:**
```
rtsp://admin:Password@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0
```

**Hikvision Cameras:**
```
rtsp://admin:Password@192.168.1.64:554/Streaming/Channels/101
```

**Generic RTSP:**
```
rtsp://username:password@ip_address:port/path
```

**Tips:**
- Replace `admin` and `Password` with your camera credentials
- Use the camera's **main stream** for better quality
- Test the RTSP URL with VLC Media Player first: `Media → Open Network Stream`
- Ensure the camera is on the same network or accessible via port forwarding

### Network Requirements
- **Bandwidth**: 2-5 Mbps per camera (H.264/H.265)
- **Latency**: < 100ms for real-time recognition
- **Ports**: 
  - RTSP: 554 (TCP)
  - HTTP: 80 (for camera web interface)

---

## 💻 System Requirements

### Minimum Server Specifications

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores (2.0 GHz) | 4 cores (3.0 GHz+) |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 20 GB SSD | 50 GB SSD |
| **GPU** | Not required | NVIDIA GPU (CUDA) for faster processing |
| **Network** | 100 Mbps | 1 Gbps |

### Operating System
- **Linux**: Ubuntu 22.04 LTS (recommended for production)
- **Windows**: Windows 10/11 (for development or small deployments)

### Network Configuration

**Required Ports:**
| Service | Port | Protocol | Purpose |
|---------|------|----------|----------|
| Backend API | 8000 | TCP | FastAPI server |
| Frontend | 3000 | TCP | React application |
| HTTPS (via proxy) | 443 | TCP | Secure access |
| HTTP (via proxy) | 80 | TCP | Redirect to HTTPS |
| SSH (Linux) | 22 | TCP | Remote management |

**Firewall Rules:**
```bash
# Ubuntu/Linux
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 22/tcp
```

**Network Topology:**
```
[IP Cameras] ──┐
               ├──> [Network Switch] ──> [Server] ──> [Nginx Proxy] ──> [Internet]
[Webcams] ─────┘
```

### Performance Guidelines
- **1-2 cameras**: 2 CPU cores, 4 GB RAM
- **3-5 cameras**: 4 CPU cores, 8 GB RAM
- **6+ cameras**: 6+ CPU cores, 16 GB RAM, consider GPU acceleration

---

## 📦 Version History

*   **Documentation**: System requirements and network specifications.
*   **Enhancement**: Dahua, Hikvision RTSP URL examples.

### v1.5.2 (Stable)
*   **Fix**: Corrected recognition threshold to 85% (Frontend & Backend).
*   **UI**: Updated Live View overlay to reflect 85% minimum.
*   **UI**: Reduced landmark visibility (subtle dots).

### v1.5.1 (Stable)
*   **Fix**: Resolved 502 Bad Gateway error caused by missing method in `face_service.py`.
*   **Fix**: Fixed 500 Internal Server Error on photo updates.
*   **Stability**: Reverted experimental liveness detection features to ensure system stability.

### v1.5.0
*   **Feature**: Enhanced photo capture flow.
*   **Feature**: Improved face recognition precision (90% threshold).
*   **UI**: Updated branding and layout.

### v1.4.0
*   **Feature**: Adaptive image quality handling.

### v1.3.0
*   **Feature**: InsightFace Buffalo_L model integration.

### v1.2.0
*   **Feature**: Automatic log cleanup (deletes logs older than 6 months).
*   **Optimization**: Scheduled daily maintenance at 11:00 AM.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

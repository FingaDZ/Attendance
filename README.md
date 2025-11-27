---
---
![Version](https://img.shields.io/badge/version-1.8.1-green.svg) ![Python](https://img.shields.io/badge/python-3.10-blue.svg) ![React](https://img.shields.io/badge/react-19-blue.svg)

# Attendance System v1.8.1 🚀

A state-of-the-art facial recognition attendance system designed for high accuracy and adaptability. Built with **FastAPI** (Backend) and **React** (Frontend).

## 🌟 Key Features

### 1. High-Precision Recognition (MediaPipe) 👁️
- **478 Facial Landmarks**: Uses MediaPipe Face Mesh for extreme precision (vs 68 points in older versions).
- **Robust Liveness Detection**: Active detection of blinking, head movement, and texture analysis to prevent photo spoofing.
- **Iris Tracking**: Precise eye tracking for attention awareness.

### 2. Adaptive Training System 🧠
- **Self-Learning**: The system automatically updates employee profiles when appearance changes (e.g., beard growth, aging).
- **Stability Check**: Updates only trigger after **3 consecutive high-confidence recognitions** (>90%).
- **Weighted Updates**: Uses a rolling average to gradually evolve the biometric profile without losing the original identity.

### 3. Optimized RTSP Streaming 📹 (NEW in v1.8.1)
- **MJPEG Endpoint**: Dedicated `/api/stream/{camera_id}` for bandwidth-efficient streaming.
- **Dual Resolution**: High-res for recognition, low-res (640x480) for web display.
- **70% Bandwidth Reduction**: Optimized JPEG compression and FPS limiting.
- **Low Latency**: ~100-300ms delay for real-time monitoring.

### 4. Enterprise-Grade Attendance ⏱️
- **Strict Time Constraints**: Configurable windows for ENTRY (03:00-13:30) and EXIT (12:00-23:59).
- **Smart Auth**: Secure WAN access with PIN protection, seamless LAN access.
- **Reporting**: Export attendance logs to Excel/CSV.

---

## 📂 Project Structure

### Backend (`/backend`)
Powered by **FastAPI** and **Python 3.10**.
- **`app/services/face_service.py`**: Core recognition engine (InsightFace + MediaPipe).
- **`app/services/adaptive_training_service.py`**: Logic for automatic profile updates.
- **`app/services/liveness_service.py`**: Anti-spoofing logic.
- **`app/routers/api.py`**: REST API endpoints.
- **`app/models.py`**: SQLAlchemy database models.

### Frontend (`/frontend`)
Built with **React 19**, **Vite**, and **TailwindCSS**.
- **`src/pages/Dashboard.jsx`**: Real-time camera feed and attendance status.
- **`src/pages/Employees.jsx`**: Employee management (Add/Edit/Delete).
- **`src/pages/AttendanceLogs.jsx`**: View and export logs.

---

## 🚀 Deployment

### Quick Start (Ubuntu 22.04)
We provide a dedicated script for easy deployment on Ubuntu.

```bash
chmod +x deploy_ubuntu.sh
./deploy_ubuntu.sh
```

### Manual Installation
See the detailed guides below:
- **[Ubuntu / Linux Deployment Guide](deployment_guide.md)** (Recommended for Production)
- **[Windows 10/11 Deployment Guide](deployment_guide_windows.md)** (For Local Testing)

---

## 📋 Changelog

### v1.8.2 (2025-11-27) - RTSP Quality & Latency Fix
- **Fix**: Improved RTSP video quality (JPEG 85% vs 70%).
- **Fix**: Reduced frame skip from 5 to 1 (better quality, ~1s latency).
- **Fix**: Face recognition now works correctly on RTSP cameras.
- **Optimization**: Used `cap.grab()` for efficient frame skipping.

### v1.8.1 (2025-11-27) - MJPEG Streaming Optimization
- **New**: Added optimized MJPEG streaming endpoint `/api/stream/{camera_id}` for RTSP cameras.
- **Optimization**: Dual-resolution support (high-res for recognition, low-res for web streaming).
- **Optimization**: RTSP buffer reduction and FPS limiting to minimize latency.
- **Performance**: Reduced bandwidth usage by ~70% for web streaming (640x480 @ 70% JPEG quality).

### v1.8.0.1 (2025-11-27) - Patch
- **Fix**: Added `mediapipe` to `requirements.txt` for automated installation.
- **Docs**: Updated deployment guides with explicit MediaPipe installation steps.
- **Script**: Created `update_attendance.sh` for easy system updates.

### v1.8.0 (2025-11-27) - MAJOR UPDATE
- **New**: Integrated **MediaPipe Face Mesh** (478 landmarks) for superior accuracy.
- **New**: Added **Adaptive Training System** for automatic profile updates.
- **New**: Implemented **Active Liveness Detection** (Blink/Motion).
- **Security**: Enhanced anti-spoofing measures.
- **Fix**: Resolved dependency conflicts (Protobuf/Numpy) for stable production deployment.

### v1.7.2 (2025-11-26)
- **Fix**: Resolved `NameError` in API imports.
- **Docs**: Clarified LAN access instructions.
- **Improvement**: Stabilized Import/Export feature.

### v1.7.1 (2025-11-26)
- **Feature**: Added strict time constraints for attendance.
- **Feature**: Added Employee Import/Export.

---

## 📄 License
This project is licensed under the MIT License.

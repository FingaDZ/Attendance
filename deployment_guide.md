# Attendance System v1.8.0 - Ubuntu 22.04 Deployment Guide
## (With External Nginx Proxy Manager)

## Server Information
- IP: 192.168.20.56/24
- OS: Ubuntu 22.04 LTS
- User: root
- External Proxy: Nginx Proxy Manager (handles HTTPS & routing)

---

**Current Version:** v1.9.3
**Last Updated:** 2025-11-27

## 🚀 Quick Deployment (Recommended)

We have provided a script to automate the deployment process.

1. **Clone the repository:**
   ```bash
   cd /opt
   git clone https://github.com/FingaDZ/Attendance.git
   cd Attendance
   ```

2. **Run the deployment script:**
   ```bash
   chmod +x deploy_ubuntu.sh

### Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10 and pip
sudo apt install -y python3.10 python3.10-venv python3-pip

# Install libraries for InsightFace/OpenCV
sudo apt install -y build-essential cmake git wget libopencv-dev python3-opencv libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgfortran5 libopenblas-dev liblapack-dev libjpeg-dev libpng-dev libtiff-dev
```

### Step 2: Setup Backend (Critical for v1.8.0)

```bash
cd /opt/Attendance/backend

# Create & Activate Virtual Environment
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Base Dependencies
pip install -r requirements.txt

# ⚠️ CRITICAL STEP FOR v1.8.0 ⚠️
# You MUST install specific versions of Protobuf and Numpy to avoid conflicts between MediaPipe and InsightFace.
pip install "protobuf<5" "numpy<2"

# Install MediaPipe (new in v1.8.0)
pip install mediapipe

# Verify Installation
python3 -c "import mediapipe; import insightface; print('✅ System Ready')"
```

### Step 3: Setup Frontend

```bash
cd /opt/Attendance/frontend

# Install Node.js dependencies
npm install

# Build production version
npm run build
```

### Step 4: Systemd Services

**Backend Service (`/etc/systemd/system/attendance-backend.service`)**:
```ini
[Unit]
Description=Attendance System Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Attendance
Environment="PATH=/opt/Attendance/backend/venv/bin"
ExecStart=/opt/Attendance/backend/venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service (`/etc/systemd/system/attendance-frontend.service`)**:
```ini
[Unit]
Description=Attendance System Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Attendance/frontend
ExecStart=/usr/bin/serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable & Start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable attendance-backend attendance-frontend
sudo systemctl restart attendance-backend attendance-frontend
```

---

## 🆕 Version 1.8.0 Specifics

### 1. MediaPipe Integration (478 Landmarks)
The system now uses MediaPipe Face Mesh for high-precision landmark detection.
- **Impact**: Better accuracy for liveness detection (blinking, head movement).
- **Requirement**: `protobuf<5` and `numpy<2` are strictly required.

### 2. Adaptive Training
The system automatically updates employee profiles when:
- Recognition confidence is > 90%.
- Liveness score is > 80%.
- This happens 3 times consecutively.
- **Impact**: The system adapts to appearance changes (e.g., beard growth) automatically.

---

## 🔄 Updating from v1.7.x to v1.8.0

1. **Stop Services:**
   ```bash
   sudo systemctl stop attendance-backend attendance-frontend
   ```

2. **Pull Latest Code:**
   ```bash
   cd /opt/Attendance
   git pull origin main
   ```

3. **Update Backend Dependencies (CRITICAL):**
   ```bash
   cd backend
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install "protobuf<5" "numpy<2"  # <-- IMPORTANT
   deactivate
   ```

4. **Rebuild Frontend:**
   ```bash
   cd ../frontend
   npm install
   npm run build
   ```

5. **Restart Services:**
   ```bash
   sudo systemctl start attendance-backend attendance-frontend
   ```

---

## 🎥 MJPEG Streaming for RTSP Cameras (v1.8.1)

### Overview
Version 1.8.1 introduces optimized MJPEG streaming specifically designed for RTSP IP cameras, reducing bandwidth by ~70% while maintaining smooth video playback.

### Features
- **Dedicated Endpoint**: `/api/stream/{camera_id}` for efficient browser streaming
- **Dual Resolution**: Full-res for recognition, 640x480 for web display
- **Optimized for RTSP**: Automatic buffer reduction and FPS limiting
- **Low Latency**: ~100-300ms delay

### Usage in Frontend
```jsx
// React component
<img 
    src={`${API_BASE_URL}/stream/${cameraId}`}
    alt="Live Camera Feed"
    style={{ width: '100%', maxWidth: '640px' }}
/>
```

### Configuration
Edit `backend/app/services/camera_service.py` to adjust quality:
```python
self.stream_quality = 70  # 0-100 (higher = better quality)
self.stream_fps = 15      # Target FPS
```

### Performance
- **Bandwidth**: ~0.5-1 Mbps per stream (vs 3-5 Mbps raw RTSP)
- **CPU Usage**: ~5-10% per stream on Ubuntu 22.04
- **Latency**: 100-300ms

For detailed configuration and troubleshooting, see [MJPEG_STREAMING_GUIDE.md](MJPEG_STREAMING_GUIDE.md).

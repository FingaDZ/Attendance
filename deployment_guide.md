# Attendance System - Ubuntu 22.04 Deployment Guide
## (With External Nginx Proxy Manager)

## Server Information
- IP: 192.168.20.56/24
- OS: Ubuntu 22.04 LTS
- User: root
- External Proxy: Nginx Proxy Manager (handles HTTPS & routing)

---

## Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10 and pip
sudo apt install -y python3.10 python3.10-venv python3-pip

# Install Node.js 20.x (LTS) - Required for Vite 7+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify Node.js version
node --version  # Should show v20.x.x
npm --version

# Install build tools and libraries for InsightFace/OpenCV
sudo apt install -y \
    build-essential \
    cmake \
    git \
    wget \
    libopencv-dev \
    python3-opencv \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgfortran5

# Install additional libraries for face recognition
sudo apt install -y \
    libopenblas-dev \
    liblapack-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev

# Install Git
sudo apt install -y git
```

---

## Step 2: Clone Project from GitHub

```bash
# Navigate to /opt directory
cd /opt

# Clone the repository
git clone https://github.com/FingaDZ/Attendance.git
cd Attendance

# Or upload from your Windows machine:
# scp -r f:\Code\attendance root@192.168.20.56:/opt/Attendance
```

---

## Step 3: Setup Backend

```bash
cd /opt/Attendance/backend

# Create Python virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Verify InsightFace installation
python3 -c "import insightface; print('InsightFace OK')"

# Deactivate venv
deactivate
```

---

## Step 4: Setup Frontend

```bash
cd /opt/Attendance/frontend

# Clean npm cache (important!)
npm cache clean --force

# Remove existing node_modules if any
rm -rf node_modules package-lock.json

# Install Node.js dependencies
npm install

# Fix permissions for node_modules
chmod -R 755 node_modules

# Build production version
npm run build

# The build output will be in /opt/Attendance/frontend/dist
```

**If you still get "vite: Permission denied":**
```bash
# Option 1: Use npx to run vite
npx vite build

# Option 2: Install vite globally
npm install -g vite
vite build

# Option 3: Run with explicit node
node node_modules/vite/bin/vite.js build
```

---

## Step 5: Create Systemd Service for Backend

```bash
# Create service file
sudo nano /etc/systemd/system/attendance-backend.service
```

**Paste this content:**

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

**Save and enable:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable attendance-backend

# Start service
sudo systemctl start attendance-backend

# Check status
sudo systemctl status attendance-backend
```

---

## Step 6: Create Systemd Service for Frontend

```bash
# Install serve globally (simple static file server)
sudo npm install -g serve

# IMPORTANT: Find where 'serve' is installed
which serve
# It will likely output: /usr/bin/serve OR /usr/local/bin/serve
# Use this path in the ExecStart line below.
```

```bash
# Create service file
sudo nano /etc/systemd/system/attendance-frontend.service
```

**Paste this content (Update ExecStart with YOUR path from 'which serve'):**

```ini
[Unit]
Description=Attendance System Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Attendance/frontend
# REPLACE /usr/bin/serve with the output of 'which serve' if different
# Common paths: /usr/bin/serve, /usr/local/bin/serve, /usr/lib/node_modules/.bin/serve
ExecStart=/usr/bin/serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save and enable:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable attendance-frontend

# Start service
sudo systemctl start attendance-frontend

# Check status
```bash
# Allow backend port (8000)
sudo ufw allow 8000/tcp

# Allow frontend port (3000)
sudo ufw allow 3000/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Step 8: Configure Nginx Proxy Manager

### In your Nginx Proxy Manager UI:

#### **Proxy Host 1: Frontend**
- **Domain Names**: `attendance.yourdomain.com` (or your domain)
- **Scheme**: `http`
- **Forward Hostname/IP**: `192.168.20.56`
- **Forward Port**: `3000`
- **Cache Assets**: ✅ Enabled
- **Block Common Exploits**: ✅ Enabled
- **Websockets Support**: ✅ Enabled
- **SSL**: Configure your SSL certificate
- **Force SSL**: ✅ Enabled

#### **Proxy Host 2: Backend API**
- **Domain Names**: `attendance-api.yourdomain.com` (or subdomain)
- **Scheme**: `http`
- **Forward Hostname/IP**: `192.168.20.56`
- **Forward Port**: `8000`
- **Block Common Exploits**: ✅ Enabled
- **Websockets Support**: ✅ Enabled
- **SSL**: Configure your SSL certificate
- **Force SSL**: ✅ Enabled

**Custom Nginx Configuration (Advanced tab):**
```nginx
# Increase upload size for photos
client_max_body_size 50M;

# Increase timeouts for face recognition
proxy_read_timeout 300;
proxy_connect_timeout 300;
proxy_send_timeout 300;
```

---

## Step 9: Update Frontend API Configuration

```bash
# Edit frontend API configuration
nano /opt/Attendance/frontend/src/api.js
```

**Update baseURL to point to your API domain:**

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'https://attendance-api.yourdomain.com',  // Your API domain
});

export default api;
```

**Rebuild frontend:**

```bash
cd /opt/Attendance/frontend
npm run build

# Restart frontend service
sudo systemctl restart attendance-frontend
```

---

## Step 10: Alternative - Single Domain Setup

If you prefer using a single domain with `/api` path:

### Nginx Proxy Manager Configuration:

**Proxy Host: Combined**
- **Domain Names**: `attendance.yourdomain.com`
- **Scheme**: `http`
- **Forward Hostname/IP**: `192.168.20.56`
- **Forward Port**: `3000`

**Custom Nginx Configuration (Advanced tab):**
```nginx
# Frontend (default)
location / {
    proxy_pass http://192.168.20.56:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Increase timeouts
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    
    # Increase upload size
    client_max_body_size 50M;
}
```

**Frontend API config (if using single domain):**
```javascript
const api = axios.create({
    baseURL: '/api',  // Relative path
});
```

---

## Step 11: Test the System

```bash
# Check backend status
sudo systemctl status attendance-backend

# Check frontend status
sudo systemctl status attendance-frontend

# Test backend API locally
curl http://localhost:8000/api/employees/

# Test frontend locally
curl http://localhost:3000

# Access from browser (through Nginx Proxy Manager)
# Open: https://attendance.yourdomain.com
```

---

## Useful Commands

### View Backend Logs
```bash
sudo journalctl -u attendance-backend -f
```

### View Frontend Logs
```bash
sudo journalctl -u attendance-frontend -f
```

### Restart Services
```bash
# Restart backend
sudo systemctl restart attendance-backend

# Restart frontend
sudo systemctl restart attendance-frontend

# Restart both
sudo systemctl restart attendance-backend attendance-frontend
```

### Update Code from GitHub
```bash
cd /opt/Attendance
git pull origin master

# Rebuild frontend
cd frontend
npm run build

# Restart services
sudo systemctl restart attendance-backend attendance-frontend
```

---

## 🔄 Updating an Existing Installation

If you already have Attendance installed in `/opt/Attendance` and want to update to the latest version:

### Step 1: Backup Current Installation

```bash
# Backup database
cp /opt/Attendance/attendance.db /opt/Attendance/attendance.db.backup.$(date +%Y%m%d_%H%M%S)

# Optional: Backup entire installation
tar -czf /opt/attendance_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/Attendance
```

### Step 2: Stop Services

```bash
sudo systemctl stop attendance-backend
sudo systemctl stop attendance-frontend
```

### Step 3: Update Code

```bash
cd /opt/Attendance

# Stash any local changes (if any)
git stash

# Pull latest code
git pull origin master

# If you had local changes, reapply them
# git stash pop
```

### Step 4: Update Backend Dependencies

```bash
cd /opt/Attendance/backend
source venv/bin/activate

# Update dependencies
pip install --upgrade pip
pip install -r requirements.txt

deactivate
```

### Step 5: Update Frontend Dependencies

```bash
cd /opt/Attendance/frontend

# Update dependencies (optional, only if package.json changed)
npm install

# Rebuild production build
npm run build
```

### Step 6: Apply Database Migrations (if any)

```bash
# Currently, the system uses SQLite with automatic schema creation
# No manual migrations needed unless specified in release notes
```

### Step 7: Restart Services

```bash
sudo systemctl start attendance-backend
sudo systemctl start attendance-frontend

# Check status
sudo systemctl status attendance-backend
sudo systemctl status attendance-frontend
```

### Step 8: Verify Update

```bash
# Check backend API
curl http://localhost:8000/api/employees/

# Check frontend
curl http://localhost:3000

# Check logs for errors
sudo journalctl -u attendance-backend -n 50
sudo journalctl -u attendance-frontend -n 50
```

### Quick Update Script

Create a file `/opt/update_attendance.sh`:

```bash
#!/bin/bash
set -e

echo "=== Attendance System Update ==="

# Backup database
echo "Backing up database..."
cp /opt/Attendance/attendance.db /opt/Attendance/attendance.db.backup.$(date +%Y%m%d_%H%M%S)

# Stop services
echo "Stopping services..."
sudo systemctl stop attendance-backend attendance-frontend

# Update code
echo "Pulling latest code..."
cd /opt/Attendance
git pull origin master

# Update backend
echo "Updating backend dependencies..."
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Update frontend
echo "Rebuilding frontend..."
cd ../frontend
npm install
npm run build

# Restart services
echo "Restarting services..."
sudo systemctl start attendance-backend attendance-frontend

# Check status
echo "Checking service status..."
sudo systemctl status attendance-backend --no-pager
sudo systemctl status attendance-frontend --no-pager

echo "=== Update Complete ==="
echo "Check logs: sudo journalctl -u attendance-backend -f"
```

Make it executable:
```bash
sudo chmod +x /opt/update_attendance.sh
```

Run updates:
```bash
sudo /opt/update_attendance.sh
```

---

### Check Service Status
```bash
# All services
sudo systemctl status attendance-*

# Individual services
sudo systemctl status attendance-backend
sudo systemctl status attendance-frontend
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u attendance-backend -n 50 --no-pager

# Check if port 8000 is in use
sudo lsof -i :8000

# Manually test backend
cd /opt/Attendance
source backend/venv/bin/activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend won't start
```bash
# Check logs
sudo journalctl -u attendance-frontend -n 50 --no-pager

# Check if port 3000 is in use
sudo lsof -i :3000

# Manually test frontend
cd /opt/Attendance/frontend
serve -s dist -l 3000
```

### Frontend Error: "filter is not a function" or "map is not a function"
**Cause:** You are accessing `http://192.168.20.56:3000` directly.
- The static server (`serve`) on port 3000 **does NOT** proxy `/api` requests to the backend (port 8000).
- So `/api/attendance` returns 404 (HTML), which breaks the JS code expecting JSON.

**Solution 1 (Recommended):**
Access the app through **Nginx Proxy Manager** (port 80/443) as configured in Step 8.
- URL: `http://attendance.yourdomain.com` or `http://192.168.20.56` (if configured on port 80)
- Nginx Proxy Manager handles routing `/` to port 3000 and `/api` to port 8000.

**Solution 2 (For testing port 3000 directly):**
Update `src/api.js` to point directly to the backend IP/Port:
```javascript
const api = axios.create({
    baseURL: 'http://192.168.20.56:8000', // Direct backend URL
});
```
Then rebuild: `npm run build`

### Can't access through Nginx Proxy Manager
```bash
# Test local access first
curl http://192.168.20.56:3000  # Frontend
curl http://192.168.20.56:8000/api/employees/  # Backend

# Check firewall
sudo ufw status

# Check if services are listening
sudo netstat -tlnp | grep -E '3000|8000'
```

### InsightFace errors
```bash
# Install additional dependencies
source /opt/Attendance/backend/venv/bin/activate
pip install onnxruntime

# Test InsightFace
python3 -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_s'); print('OK')"
```

---

## Port Summary

| Service | Port | Access |
|---------|------|--------|
| Backend API | 8000 | Internal + Proxy Manager |
| Frontend | 3000 | Internal + Proxy Manager |
| SSH | 22 | External |

---

## System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum
- **Network**: 100Mbps+

---

## Security Recommendations

1. **Change default SSH port**
```bash
sudo nano /etc/ssh/sshd_config
# Change Port 22 to something else
sudo systemctl restart sshd
```

2. **Disable root SSH login** (after creating a sudo user)
```bash
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
```

3. **Setup automatic security updates**
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

4. **Regular backups of database**
```bash
# Create backup script
sudo nano /opt/backup-attendance.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /opt/Attendance/attendance.db $BACKUP_DIR/attendance_$DATE.db
# Keep only last 7 days
find $BACKUP_DIR -name "attendance_*.db" -mtime +7 -delete
```

```bash
# Make executable
sudo chmod +x /opt/backup-attendance.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /opt/backup-attendance.sh
```

---

## Next Steps

1. ✅ Configure Nginx Proxy Manager with your domain
2. ✅ Access the system at `https://attendance.yourdomain.com`
3. ✅ Register employees with 3 photos
4. ✅ Test face recognition
5. ✅ Configure cameras if needed
6. ✅ Set up automatic database backups
7. ✅ Monitor system logs regularly

---

## Quick Start Summary

```bash
# 1. Install dependencies (Step 1)
# 2. Clone project (Step 2)
# 3. Setup backend (Step 3)
# 4. Setup frontend (Step 4)
# 5. Create systemd services (Steps 5-6)
# 6. Configure firewall (Step 7)
# 7. Configure Nginx Proxy Manager (Step 8)
# 8. Update frontend API config (Step 9)
# 9. Test everything (Step 11)
```

---

## 🔌 API Integration

The system provides a REST API for external integrations. See [API_INTEGRATION.md](../API_INTEGRATION.md) for complete documentation.

**Access API Documentation:**
- Swagger UI: `https://attendance-api.yourdomain.com/docs`
- ReDoc: `https://attendance-api.yourdomain.com/redoc`

**Example: Get Attendance Logs**
```bash
curl "https://attendance-api.yourdomain.com/api/attendance/?start_date=2024-01-01&end_date=2024-01-31"
```

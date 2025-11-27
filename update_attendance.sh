#!/bin/bash

# Update Script for Attendance System v1.8.0+
# Usage: sudo ./update_attendance.sh

set -e

echo "=== Attendance System Update ==="

# Backup database
echo "📦 Backing up database..."
cp /opt/Attendance/attendance.db /opt/Attendance/attendance.db.backup.$(date +%Y%m%d_%H%M%S)

# Stop services
echo "⏸️  Stopping services..."
sudo systemctl stop attendance-backend attendance-frontend

# Update code
echo "📥 Pulling latest code from GitHub..."
cd /opt/Attendance
git pull origin master

# Update backend
echo "🐍 Updating backend dependencies..."
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# CRITICAL: Enforce compatible versions (v1.8.0+)
echo "🔧 Enforcing compatible library versions..."
pip install "protobuf<5" "numpy<2"

# Install MediaPipe if not present (v1.8.0+)
echo "📦 Ensuring MediaPipe is installed..."
pip install mediapipe

# Verify installation
python3 -c "import mediapipe; import insightface; print('✅ Dependencies verified')"

deactivate

# Update frontend
echo "🎨 Rebuilding frontend..."
cd ../frontend
npm install
npm run build

# Restart services
echo "🔄 Restarting services..."
sudo systemctl start attendance-backend attendance-frontend

# Check status
echo "📊 Checking service status..."
sudo systemctl status attendance-backend --no-pager
sudo systemctl status attendance-frontend --no-pager

echo ""
echo "=== Update Complete ==="
echo "✅ Backend: Running"
echo "✅ Frontend: Running"
echo "📝 Check logs: sudo journalctl -u attendance-backend -f"

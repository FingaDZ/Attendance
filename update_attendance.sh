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

# 3. Update Backend Dependencies
echo "📦 Updating backend dependencies..."
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3.10 -m venv venv
    source venv/bin/activate
fi

pip install --upgrade pip
# v2.0.0: Uninstall MediaPipe if present
pip uninstall -y mediapipe
# Force reinstall to ensure clean state
pip install -r requirements.txt
# Ensure compatibility
pip install "protobuf<5" "numpy<2"

# Verify installation
python3 -c "import insightface; print('✅ Dependencies verified')"

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

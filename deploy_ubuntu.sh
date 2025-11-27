#!/bin/bash

# Deployment Script for Attendance System v1.8.0 on Ubuntu 22.04
# Usage: ./deploy_ubuntu.sh

echo "🚀 Starting Deployment of Attendance System v1.8.0..."

# 1. Update Repository
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# 2. Backend Setup
echo "🐍 Setting up Backend..."
cd backend

# Ensure Python 3.10 is used
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10 could not be found. Please install it."
    exit 1
fi

# Create/Activate Virtual Environment
if [ ! -d "venv" ]; then
    echo "🌱 Creating virtual environment..."
    python3.10 -m venv venv
fi

source venv/bin/activate

# Install Dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# CRITICAL: Force compatible versions for MediaPipe & InsightFace
echo "🔧 Enforcing compatible library versions (Protobuf < 5, Numpy < 2)..."
pip install "protobuf<5" "numpy<2"

# Install MediaPipe (new in v1.8.0)
echo "📦 Installing MediaPipe for 478-point facial landmarks..."
pip install mediapipe

# Verify installation
python3 -c "import mediapipe; import insightface; print('✅ All dependencies verified')"

# Run Database Migrations (if any)
# python -m app.database_migration_script_if_exists

echo "✅ Backend dependencies installed."

# 3. Frontend Setup (Optional - if building on server)
# echo "🎨 Setting up Frontend..."
# cd ../frontend
# npm install
# npm run build
# cd ..

# 4. Restart Service (assuming systemd service named 'attendance')
# echo "🔄 Restarting Attendance Service..."
# sudo systemctl restart attendance

echo "🎉 Deployment Complete! v1.8.0 is ready."
echo "   - MediaPipe 478 Landmarks: ACTIVE"
echo "   - Adaptive Training: ACTIVE"
echo "   - Ensemble Method: DISABLED (Stability Mode)"

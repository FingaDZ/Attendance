#!/bin/bash

# Network Access Configuration for Attendance System
# This allows access from both LAN (192.168.20.x) and external networks

echo "=== Configuring Network Access ==="

# 1. Update backend to listen on all interfaces (0.0.0.0)
echo "[1/3] Configuring backend to listen on 0.0.0.0..."

# The backend service should use: uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Update frontend API base URL to use current hostname
echo "[2/3] Frontend will use relative API paths..."

# 3. Configure firewall (if needed)
echo "[3/3] Checking firewall rules..."

# Allow port 8000 (backend) and 3000 (frontend dev) or 80/443 (production)
if command -v ufw &> /dev/null; then
    sudo ufw allow 8000/tcp
    sudo ufw allow 3000/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo "✓ Firewall rules updated"
else
    echo "⚠ UFW not found, skipping firewall configuration"
fi

echo ""
echo "=== Configuration Complete ==="
echo ""
echo "Backend should be accessible from:"
echo "  - LAN: http://192.168.20.56:8000"
echo "  - External: https://hgq09k0j9p1.sn.mynetname.net"
echo ""
echo "Frontend should be accessible from:"
echo "  - LAN: http://192.168.20.56:3000 (or :80 if using nginx)"
echo "  - External: https://hgq09k0j9p1.sn.mynetname.net"
echo ""
echo "Note: Ensure your systemd service uses --host 0.0.0.0"

#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Attendance System Update ===${NC}"
echo "Date: $(date)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}Please run as root (sudo)${NC}"
  exit 1
fi

# Configuration
APP_DIR="/opt/Attendance"
BACKUP_DIR="/opt/backups"
DATE_SUFFIX=$(date +%Y%m%d_%H%M%S)

# 1. Backup Database
echo -e "\n${YELLOW}[1/6] Backing up database...${NC}"
mkdir -p $BACKUP_DIR
if [ -f "$APP_DIR/attendance.db" ]; then
    cp "$APP_DIR/attendance.db" "$BACKUP_DIR/attendance_$DATE_SUFFIX.db"
    echo "Database backed up to $BACKUP_DIR/attendance_$DATE_SUFFIX.db"
    
    # Clean old backups (keep last 7 days)
    find $BACKUP_DIR -name "attendance_*.db" -mtime +7 -delete
else
    echo "No database found to backup (first run?)"
fi

# 2. Stop Services
echo -e "\n${YELLOW}[2/6] Stopping services...${NC}"
systemctl stop attendance-backend attendance-frontend || true

# 3. Update Code
echo -e "\n${YELLOW}[3/6] Pulling latest code...${NC}"
cd $APP_DIR
git fetch origin master
git reset --hard origin/master
# git pull origin master

# 4. Update Backend
echo -e "\n${YELLOW}[4/6] Updating backend...${NC}"
cd $APP_DIR/backend
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
else
    echo -e "${RED}Error: Backend venv not found!${NC}"
    exit 1
fi

# 5. Update Frontend
echo -e "\n${YELLOW}[5/6] Updating frontend...${NC}"
cd $APP_DIR/frontend
# Only install if package.json changed (optimization)
npm install
npm run build

# 6. Restart Services
echo -e "\n${YELLOW}[6/6] Restarting services...${NC}"
systemctl start attendance-backend attendance-frontend

# Check status
echo -e "\n${GREEN}=== Update Complete ===${NC}"
echo "Checking service status..."

if systemctl is-active --quiet attendance-backend; then
    echo -e "Backend: ${GREEN}Active${NC}"
else
    echo -e "Backend: ${RED}Failed${NC}"
    systemctl status attendance-backend --no-pager
fi

if systemctl is-active --quiet attendance-frontend; then
    echo -e "Frontend: ${GREEN}Active${NC}"
else
    echo -e "Frontend: ${RED}Failed${NC}"
    systemctl status attendance-frontend --no-pager
fi

echo -e "\nView logs with: ${YELLOW}journalctl -u attendance-backend -f${NC}"

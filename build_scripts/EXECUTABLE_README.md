# FaceAttendanceAI - Windows Executable

## Overview

This is a standalone Windows executable version of the Face Attendance AI system. It bundles the entire application (backend + frontend + AI models) into a single `.exe` file.

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **RAM**: Minimum 4 GB (8 GB recommended)
- **Disk Space**: 2 GB free space
- **Dependencies**: Visual C++ Redistributable 2015-2022 ([Download here](https://aka.ms/vs/17/release/vc_redist.x64.exe))

## First Run

1. **Double-click** `FaceAttendanceAI.exe`
2. Windows Defender may show a warning (click "More info" → "Run anyway")
3. The application will:
   - Extract necessary files
   - Start the backend server
   - Automatically open your browser to `http://localhost:8000`

## Usage

### Starting the Application

Simply double-click `FaceAttendanceAI.exe`. A console window will appear showing the startup progress.

### Accessing the Interface

The application will automatically open in your default browser. If it doesn't, manually navigate to:
- **Frontend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Stopping the Application

Press `Ctrl+C` in the console window, or simply close the console window.

## Data Storage

All data is stored in your Windows user profile:

```
C:\Users\YourUsername\AppData\Roaming\FaceAttendanceAI\
├── attendance.db          (SQLite database)
├── photos\                (Employee photos)
└── models\                (AI models - ~200MB)
```

## Troubleshooting

### "Port 8000 is already in use"

Another instance is already running. Close it first, or check Task Manager for `FaceAttendanceAI.exe`.

### "VCRUNTIME140.dll not found"

Install Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Camera not working

- Grant camera permissions in Windows Settings
- Ensure no other application is using the camera
- Try refreshing the browser page

### Application won't start

1. Right-click `FaceAttendanceAI.exe` → "Run as administrator"
2. Check Windows Firewall settings
3. Temporarily disable antivirus and try again

## Features

✅ Face recognition attendance tracking  
✅ Multi-camera support (Webcam + IP cameras)  
✅ Employee management  
✅ Real-time attendance logs  
✅ Export reports (Excel/PDF)  
✅ No installation required - just run the .exe!

## Network Access

To access from other devices on your network:

1. Find your computer's IP address: `ipconfig` in Command Prompt
2. Access from other devices: `http://YOUR_IP:8000`
3. Ensure Windows Firewall allows port 8000

## Updates

To update to a newer version:

1. Download the new `FaceAttendanceAI.exe`
2. Replace the old file
3. Your data will be preserved (stored in AppData)

## Support

For issues or questions, refer to the main project documentation or contact support.

---

**Version**: 1.2.2  
**Build Date**: 2025-11-23  
**License**: MIT

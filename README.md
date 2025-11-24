---
---
![Version](https://img.shields.io/badge/version-1.6.15-blue.svg)

# Attendance System

A modern facial recognition attendance system with a Python (FastAPI) backend and React frontend.

## 📚 Deployment Guides
- **[Ubuntu / Linux Deployment Guide](deployment_guide.md)** (Recommended for Production)
- **[Windows 10/11 Deployment Guide](deployment_guide_windows.md)** (For Local Testing/Dev)

## 📋 Changelog

### v1.6.15 (2025-11-25)
- **Fix**: Restored missing state variables in Settings page (`newCamName` error).
- **Fix**: Added robust data safety checks in Dashboard to prevent white screen on LAN (`filter` error).
- **Docs**: Updated deployment guides and README with latest instructions.

### v1.6.14 (2025-11-24)
- **Fix**: Resolved frontend build permissions and path issues.
- **Improvement**: Enhanced error handling for network requests between frontend and backend.
- **Config**: Updated default API timeouts for slower networks.

### v1.6.13 (2025-11-24)
- **Fix**: Addressed initial LAN connectivity issues and CORS policies.
- **Refactor**: Cleanup of unused components in the dashboard.
- **UI**: Minor visual improvements to the sidebar and navigation.

### v1.6.12 (2025-11-24)
- **Fix**: Resolved LAN access issues (white page) by adding data safety checks in frontend.
- **Feature**: Re-implemented WAN Domain Configuration in Settings.
- **Security**: Restored SmartAuthMiddleware for secure WAN access.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

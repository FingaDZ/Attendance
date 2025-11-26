---
---
![Version](https://img.shields.io/badge/version-1.7.2-blue.svg)

# Attendance System

A modern facial recognition attendance system with a Python (FastAPI) backend and React frontend.

## 📚 Deployment Guides
- **[Ubuntu / Linux Deployment Guide](deployment_guide.md)** (Recommended for Production)
- **[Windows 10/11 Deployment Guide](deployment_guide_windows.md)** (For Local Testing/Dev)

## 📋 Changelog

### v1.7.2 (2025-11-26)
- **Fix**: Resolved `NameError: name 'pd' is not defined` by ensuring correct imports in `api.py`.
- **Docs**: Clarified LAN access instructions (must use port 8000 for full functionality).
- **Improvement**: Stabilized Import/Export feature with proper dependency checks.

### v1.7.1 (2025-11-26)
- **Feature**: Added strict time constraints for attendance logging (ENTRY: 03:00-13:30, EXIT: 12:00-23:59).
- **Feature**: Added Employee Import/Export functionality (CSV/Excel).
- **Improvement**: Enhanced error messages for attendance validation.
- **Fix**: Resolved API routing issues and improved CORS configuration.

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

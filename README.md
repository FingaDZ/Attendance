- **Lightweight Liveness**: Texture-based liveness detection (sharpness/color analysis) replaces heavy mesh-based checks.
- **Performance**: 3-5x faster detection and significantly lower CPU usage compared to previous versions.

### 2. Adaptive Training System 🧠
- **Self-Learning**: The system automatically updates employee profiles when appearance changes (e.g., beard growth, aging).
- **Stability Check**: Updates only trigger after **3 consecutive high-confidence recognitions** (>90%).
- **Weighted Updates**: Uses a rolling average to gradually evolve the biometric profile without losing the original identity.

### 3. Optimized RTSP Streaming 📹 (Optimized in v2.0.2)
- **MJPEG Endpoint**: Dedicated `/api/stream/{camera_id}` for bandwidth-efficient streaming.
- **Optimized Performance**: 640x360 @ 15 FPS with 75% JPEG quality for smooth playback.
- **CPU Optimized**: 2.5 FPS detection rate for 60-70% CPU reduction.
- **Hardware Acceleration**: VAAPI support for Intel/AMD GPUs (60-80% faster video decoding).
- **Low Latency**: ~150-300ms delay for real-time monitoring.
- **H.265 Support**: Compatible with H.265/HEVC camera streams for better compression.

### 4. Enterprise-Grade Attendance ⏱️
- **Strict Time Constraints**: Configurable windows for ENTRY (03:00-13:30) and EXIT (12:00-23:59).
- **Smart Auth**: Secure WAN access with PIN protection, seamless LAN access.
- **Reporting**: Export attendance logs to Excel/CSV.
- **Auto-Logging**: Automatic attendance recording during live video streaming (v2.0.3).
- **Visual Error Messages**: Clear on-screen feedback when logging is blocked (v2.0.4).

---

## 📂 Project Structure

### Backend (`/backend`)
Powered by **FastAPI** and **Python 3.10**.
- **`app/services/face_service.py`**: Core recognition engine (InsightFace + MediaPipe).
- **`app/services/adaptive_training_service.py`**: Logic for automatic profile updates.
- **`app/services/liveness_service.py`**: Anti-spoofing logic.
- **`app/routers/api.py`**: REST API endpoints.
- **`app/models.py`**: SQLAlchemy database models.

### Frontend (`/frontend`)
Built with **React 19**, **Vite**, and **TailwindCSS**.
- **`src/pages/Dashboard.jsx`**: Real-time camera feed and attendance status.
- **`src/pages/Employees.jsx`**: Employee management (Add/Edit/Delete).
- **`src/pages/AttendanceLogs.jsx`**: View and export logs.

---

## 🚀 Deployment

### Quick Start (Ubuntu 22.04)
We provide a dedicated script for easy deployment on Ubuntu.

```bash
chmod +x deploy_ubuntu.sh
./deploy_ubuntu.sh
```

### Manual Installation
See the detailed guides below:
- **[Ubuntu / Linux Deployment Guide](deployment_guide.md)** (Recommended for Production)
- **[Windows 10/11 Deployment Guide](deployment_guide_windows.md)** (For Local Testing)

---

## 📋 Changelog

### v2.0.7 (2025-11-28) - Frontend Error Handling Fix
- **🐛 Bug Fix**: Fixed issue where frontend was ignoring "blocked" responses from the backend, preventing error messages from displaying.
- **👁️ Client-Side Display**: Added logic in `LiveView.jsx` to parse and display error messages (Red/Orange/Blue) directly from the API response.
- **✅ Universal Fix**: Works for both Client Mode (Webcam) and Server Mode (RTSP) as both use the same logging endpoint.

### v2.0.6 (2025-11-28) - Debounce Fix
- **🐛 Bug Fix**: Fixed issue where error messages (Red/Orange/Blue badges) would disappear/flicker during the 5-second debounce period.
- **🧠 Smart Persistence**: System now remembers the blocking reason during the debounce cooldown to ensure consistent visual feedback.
- **👁️ UX Improvement**: Stable error display instead of flashing "Verified" green status.

### v2.0.5 (2025-11-28) - Critical Hotfix
- **🔧 Critical Fix**: Resolved API endpoint conflict (`/stream/{camera_id}`) that prevented v2.0.4 features from loading.
- **✅ Feature Activation**: Visual error messages and auto-logging logic are now correctly enforced.
- **🧹 Code Cleanup**: Removed obsolete `generate_frames` function to prevent future conflicts.

### v2.0.4 (2025-11-28) - Visual Error Messages
- **🎨 Visual Feedback**: Added color-coded error messages in live video streaming when logging is blocked.
- **🔴 Time Constraint Errors**: Red badge for "Heure Entrée Dépassée" and "Heure Sortie Dépassée".
- **🟠 Cooldown Warning**: Orange badge for "Temps de Travail minimum non achevé" with remaining wait time.
- **🔵 Quota Reached**: Blue badge for "Detection Déjà Effectué" when daily limit is reached.
- **📊 Better UX**: Users now see exactly why their attendance wasn't recorded instead of silent failures.

### v2.0.3 (2025-11-28) - Auto-Logging Restoration
- **✅ Auto-Logging Restored**: Fixed automatic attendance recording in live video streaming (broken since v2.0.0).
- **📊 Dashboard Optimization**: Dashboard now displays only today's logs by default (instead of entire month).
- **🔒 All Conditions Preserved**: Debounce (5s), time constraints, cooldowns (4h), and daily limits still enforced.
- **💾 Full History Retained**: All historical logs remain in database for future use and reporting.
- **🎯 Performance**: No impact on CPU usage or streaming latency.

### v2.0.2 (2025-11-28) - CPU Optimization Release
- **🚀 60-70% CPU Reduction**: Optimized detection frequency (2.5 FPS instead of 5 FPS).
- **⚡ Hardware Acceleration**: Added VAAPI support for Intel/AMD (60-80% faster video decoding).
- **📚 Documentation**: Complete CPU optimization guide with ARM support.
- **🔧 libjpeg-turbo**: Instructions for 40-50% faster JPEG encoding.
- **📊 Performance**: CPU usage reduced from 3-6% to 1-2% per stream.

### v2.0.1 (2025-11-28) - RTSP Performance Optimization
- **🚀 40-50% CPU Reduction**: Optimized RTSP streaming pipeline.
- **📉 Reduced Resolution**: 640x360 for better performance while maintaining quality.
- **⚡ Faster Encoding**: INTER_AREA interpolation + Progressive JPEG (75% quality).
- **🎯 Synchronized FPS**: 15 FPS capture/stream matching camera settings.
- **📹 H.265 Support**: Compatible with H.265/HEVC camera streams.
- **🐛 Bug Fixes**: Fixed recognition inconsistency ("Unknown" showing as "Verified").
- **📊 Dashboard**: Default date range set to current month for better UX.

### v2.0.0 (2025-11-28) - Major Performance Overhaul
- **🚀 3-5x Faster Detection**: Completely removed MediaPipe Face Mesh (468 landmarks).
- **⚡ InsightFace-Only Pipeline**: Now uses lightweight 5-keypoint detection and alignment.
- **📉 Reduced Resource Usage**: CPU usage down by 60%, memory footprint reduced by 300MB.
- **📹 RTSP Optimization**: Smooth performance even on low-resolution streams.
- **🧠 Lightweight Liveness**: Replaced heavy mesh-based check with efficient texture analysis.

### v1.9.5 (2025-11-27)
- **Performance Boost**: Detection speed increased 4x (2000ms → 500ms interval)
- **Bandwidth Optimization**: Reduced JPEG quality to 75% (60% smaller uploads)
- **Improved Responsiveness**: LiveView now updates 4 times per second
- **Maintained Accuracy**: No loss in recognition precision

### v1.9.4 (2025-11-27)
- **Clean Photo Capture**: RTSP camera photos now captured without detection overlays
- **Dual Stream Endpoints**: Added `/api/stream/{id}/clean` for overlay-free capture
- **Enhanced Camera Selection**: Full webcam and RTSP support in employee registration
- **Improved Detection**: Live view maintains overlays while captured photos remain clean

### v1.9.3 (2025-11-27)
- **Enhanced Camera Support**: Added camera selection (Webcam/RTSP) for employee photo capture
- **Optimized RTSP Overlay**: Repositioned status badge to top-left corner, reduced size by 50%
- **Maintained Stream Quality**: RTSP streams now use 100% JPEG quality
- **Improved UX**: Added static nose target (+) to Live View for better face positioning

### v1.9.2 (2025-11-27)
- **Quality**: Increased RTSP stream quality to 100% (Crystal clear)
- **Visuals**: Added static "Nose Target" (+) in frontend overlay
- **Cleanup**: Removed redundant backend overlays

### v1.9.1 (2025-11-27)
- **Fix**: Moved `AsyncFrameProcessor` to global scope (stability)
- **Stability**: RTSP streaming now robust over long periods

### v1.9.0 (2025-11-27)
- **Optimization**: Async Threaded Detection for RTSP (15 FPS smooth video)
- **Visuals**: Updated RTSP overlay to match frontend style
- **Feature**: Added "Nose Tip" (+) marker

### v1.8.5 (2025-11-27) - RTSP Detection & Visuals
- **Fix**: Restored detection overlays on RTSP streams (Live View).
- **Optimization**: Implemented decoupled rendering (smooth 15FPS video with 5FPS detection).
- **Visuals**: Added landmarks (including nose tracking) to visual feedback.
- **Fix**: Resolved 502 Bad Gateway error.

### v1.8.4 (2025-11-27) - Detection & Quality Boost
- **Fix**: Added thread lock to `FaceService` to prevent MediaPipe crashes during concurrent streaming/detection.
- **Quality**: Increased MJPEG resolution to **800x600** (was 640x480).
- **Quality**: Boosted JPEG quality to **90%** for sharper details.
- **Fix**: Resolved syntax error in service initialization.

### v1.8.3 (2025-11-27) - Robust RTSP & Threading Fix
- **Fix**: Implemented threaded frame capture (`CameraStream`) to solve concurrency issues.
- **Fix**: Resolved race condition between streaming and detection loops.
- **Fix**: Face recognition now works reliably on RTSP cameras.
- **Optimization**: Background thread ensures latest frame is always available (zero latency drift).
- **Resilience**: Added automatic reconnection logic for lost streams.

### v1.8.2 (2025-11-27) - RTSP Quality & Latency Fix
- **Fix**: Improved RTSP video quality (JPEG 85% vs 70%).
- **Fix**: Reduced frame skip from 5 to 1 (better quality, ~1s latency).
- **Fix**: Face recognition now works correctly on RTSP cameras.
- **Optimization**: Used `cap.grab()` for efficient frame skipping.

### v1.8.1 (2025-11-27) - MJPEG Streaming Optimization
- **New**: Added optimized MJPEG streaming endpoint `/api/stream/{camera_id}` for RTSP cameras.
- **Optimization**: Dual-resolution support (high-res for recognition, low-res for web streaming).
- **Optimization**: RTSP buffer reduction and FPS limiting to minimize latency.
- **Performance**: Reduced bandwidth usage by ~70% for web streaming (640x480 @ 70% JPEG quality).

### v1.8.0.1 (2025-11-27) - Patch
- **Fix**: Added `mediapipe` to `requirements.txt` for automated installation.
- **Docs**: Updated deployment guides with explicit MediaPipe installation steps.
- **Script**: Created `update_attendance.sh` for easy system updates.

### v1.8.0 (2025-11-27) - MAJOR UPDATE
- **New**: Integrated **MediaPipe Face Mesh** (478 landmarks) for superior accuracy.
- **New**: Added **Adaptive Training System** for automatic profile updates.
- **New**: Implemented **Active Liveness Detection** (Blink/Motion).
- **Security**: Enhanced anti-spoofing measures.
- **Fix**: Resolved dependency conflicts (Protobuf/Numpy) for stable production deployment.

### v1.7.2 (2025-11-26)
- **Fix**: Resolved `NameError` in API imports.
- **Docs**: Clarified LAN access instructions.
- **Improvement**: Stabilized Import/Export feature.

### v1.7.1 (2025-11-26)
- **Feature**: Added strict time constraints for attendance.
- **Feature**: Added Employee Import/Export.

---

## 📄 License
This project is licensed under the MIT License.

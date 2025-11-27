```

### Frontend Integration (React)
```jsx
// In your Dashboard or LiveView component
<img 
    src={`${API_BASE_URL}/stream/${selectedCamera.id}`}
    alt="Live Camera Feed"
    style={{ width: '100%', maxWidth: '640px' }}
/>
```

### HTML (Direct)
```html
<img src="http://your-server:8000/api/stream/1" alt="Camera 1" />
```

## ⚙️ Configuration

### Adjust Stream Quality
Edit `backend/app/services/camera_service.py`:

```python
class CameraService:
    def __init__(self):
        self.stream_quality = 70  # 0-100 (higher = better quality, more bandwidth)
        self.stream_fps = 15      # Target FPS for streaming
```

### Quality Recommendations
- **Low Bandwidth** (Mobile/Remote): `quality=50`, `fps=10`
- **Balanced** (Default): `quality=70`, `fps=15`
- **High Quality** (LAN): `quality=85`, `fps=20`

## 🔧 Troubleshooting

### Stream is Laggy
1. **Reduce FPS**: Lower `stream_fps` to 10
2. **Reduce Quality**: Lower `stream_quality` to 50-60
3. **Check Network**: Ensure stable connection to RTSP camera

### Stream Won't Load
1. **Verify Camera**: Check camera is active in `/api/cameras/`
2. **Test Endpoint**: Open `/api/stream/{camera_id}` directly in browser
3. **Check Logs**: `sudo journalctl -u attendance-backend -f`

### High CPU Usage
1. **Limit Concurrent Streams**: Only stream cameras being actively viewed
2. **Reduce Resolution**: Edit `get_frame_preview()` to use smaller dimensions
3. **Increase Sleep Time**: Adjust `time.sleep(0.066)` to higher value (e.g., 0.1 for 10 FPS)

## 📊 Performance Metrics

### Typical Performance (Ubuntu 22.04, 4 cores)
- **1 RTSP Stream**: ~5-10% CPU
- **3 RTSP Streams**: ~15-25% CPU
- **Memory**: ~50-100 MB per stream

### Network Usage
- **1 Stream (640x480 @ 70%)**: ~0.5-1 Mbps
- **3 Streams**: ~1.5-3 Mbps total

## 🎓 Technical Details

### MJPEG Format
- **Content-Type**: `multipart/x-mixed-replace; boundary=frame`
- **Frame Format**: Each frame is a complete JPEG image
- **Browser Support**: All modern browsers (Chrome, Firefox, Safari, Edge)

### Why MJPEG?
1. ✅ **Simple**: No complex codec/container handling
2. ✅ **Compatible**: Works in all browsers without plugins
3. ✅ **Low Latency**: ~100-300ms (vs 3-10s for HLS)
4. ✅ **No Dependencies**: No WebRTC servers or STUN/TURN needed

## 🔄 Updating to v1.8.1

On your Ubuntu server:
```bash
cd /opt/Attendance
sudo ./update_attendance.sh
```

Or manually:
```bash
git pull origin master
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart attendance-backend
```

## 📝 Notes
- The `/api/stream/` endpoint is separate from the recognition pipeline
- Face recognition still uses full-resolution frames for maximum accuracy
- Multiple clients can view the same stream simultaneously

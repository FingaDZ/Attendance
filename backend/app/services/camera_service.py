import cv2
import threading
import time
from ..models import Camera
from ..database import SessionLocal

class CameraService:
    def __init__(self):
        self.cameras = {} # id -> cv2.VideoCapture
        self.active_streams = {} # id -> bool
        self.stream_quality = 70  # JPEG quality for web streaming (0-100)
        self.stream_fps = 15  # Target FPS for web streaming

    def start_camera(self, camera_id, source):
        if camera_id in self.cameras:
            return

        # Handle integer source for webcams
        if str(source).isdigit():
            source = int(source)
        
        # Aggressive RTSP optimization for Dahua cameras
        if isinstance(source, str) and source.startswith('rtsp'):
            # Force UDP transport for lower latency (vs TCP)
            # Add transport parameter to RTSP URL if not present
            if '?' not in source:
                source = f"{source}?tcp=0"
            
            # Use GStreamer pipeline for ultra-low latency (if available)
            # Otherwise fall back to OpenCV with aggressive settings
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            
            # CRITICAL: Minimize buffering for real-time streaming
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Absolute minimum buffer
            
            # Force frame drop if processing is slow (prevent queue buildup)
            cap.set(cv2.CAP_PROP_FPS, 15)
            
            # Disable any internal buffering
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            
        else:
            cap = cv2.VideoCapture(source)
        
        if cap.isOpened():
            self.cameras[camera_id] = cap
            self.active_streams[camera_id] = True
            print(f"Camera {camera_id} started with source {source}")
        else:
            print(f"Failed to open camera {camera_id} with source {source}")

    def stop_camera(self, camera_id):
        if camera_id in self.cameras:
            self.active_streams[camera_id] = False
            self.cameras[camera_id].release()
            del self.cameras[camera_id]

    def get_frame(self, camera_id):
        """Get high-resolution frame for face recognition"""
        if camera_id not in self.cameras:
            return None
        
        cap = self.cameras[camera_id]
        
        # CRITICAL FIX: For RTSP streams, always grab the LATEST frame
        # Skip buffered frames to prevent 10-second delays
        # This is essential for real-time recognition
        for _ in range(5):  # Flush buffer by reading multiple frames
            ret, frame = cap.read()
        
        if ret:
            return frame
        else:
            # Try to reconnect if stream is lost
            # For now, just return None
            return None

    def get_frame_preview(self, camera_id, width=640, height=480):
        """Get low-resolution frame for web streaming (optimized)"""
        frame = self.get_frame(camera_id)
        if frame is None:
            return None
        
        # Resize to lower resolution for web streaming
        # This significantly reduces bandwidth
        frame_resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
        return frame_resized

    def get_frame_jpeg(self, camera_id, quality=None, preview=True):
        """
        Get JPEG-encoded frame for MJPEG streaming
        
        Args:
            camera_id: Camera ID
            quality: JPEG quality (0-100), defaults to self.stream_quality
            preview: If True, use low-res preview; if False, use full resolution
        
        Returns:
            JPEG bytes or None
        """
        if quality is None:
            quality = self.stream_quality
            
        # Get appropriate frame
        if preview:
            frame = self.get_frame_preview(camera_id)
        else:
            frame = self.get_frame(camera_id)
            
        if frame is None:
            return None
        
        # Encode to JPEG with specified quality
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
        
        if ret:
            return buffer.tobytes()
        return None

    def initialize_cameras_from_db(self):
        db = SessionLocal()
        cameras = db.query(Camera).filter(Camera.is_active == 1).all()
        for cam in cameras:
            self.start_camera(cam.id, cam.source)
        db.close()

camera_service = CameraService()

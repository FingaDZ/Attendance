import cv2
import threading
import time
from ..models import Camera
from ..database import SessionLocal

class CameraStream:
    def __init__(self, source):
        self.source = source
        self.frame = None
        self.preview_frame = None # Cached resized frame
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.cap = None
        
        # Initialize capture
        self._open_capture()

    def _open_capture(self):
        # Handle integer source for webcams
        source = self.source
        if str(source).isdigit():
            source = int(source)
            
        # Aggressive RTSP optimization for Dahua cameras
        if isinstance(source, str) and source.startswith('rtsp'):
            if '?' not in source:
                source = f"{source}?tcp=0"
            self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Remove FPS limit to drain buffer faster
            # self.cap.set(cv2.CAP_PROP_FPS, 15) 
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
        else:
            self.cap = cv2.VideoCapture(source)

    def start(self):
        if self.running:
            return
        
        if self.cap and self.cap.isOpened():
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            print(f"Camera stream started for {self.source}")
        else:
            print(f"Failed to open camera source {self.source}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()

    def _update(self):
        while self.running:
            if self.cap and self.cap.isOpened():
                # Grab first to clear buffer if multiple frames are available
                self.cap.grab() 
                ret, frame = self.cap.retrieve()
                
                if ret:
                    # Resize for preview immediately (640x360 is enough for web)
                    # This moves CPU load to capture thread (1 per frame) instead of API (N per client)
                    preview = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_NEAREST)
                    
                    with self.lock:
                        self.frame = frame
                        self.preview_frame = preview
                else:
                    # Try to reconnect
                    print(f"Stream lost for {self.source}, reconnecting...")
                    self.cap.release()
                    time.sleep(2)
                    self._open_capture()
            else:
                print(f"Camera not opened for {self.source}, retrying...")
                time.sleep(1)
                self._open_capture()
            
            # Minimal sleep to prevent CPU hogging, but fast enough to drain buffer
            time.sleep(0.005)

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def read_preview(self):
        with self.lock:
            return self.preview_frame.copy() if self.preview_frame is not None else None

class CameraService:
    def __init__(self):
        self.cameras = {} # id -> CameraStream
        self.stream_quality = 70 # Reduced default quality
        self.stream_fps = 20 # Increased FPS

    def start_camera(self, camera_id, source):
        if camera_id in self.cameras:
            return

        stream = CameraStream(source)
        stream.start()
        
        if stream.running:
            self.cameras[camera_id] = stream
            print(f"Camera {camera_id} started")
        else:
            print(f"Failed to start camera {camera_id}")

    def stop_camera(self, camera_id):
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]

    def get_frame(self, camera_id):
        """Get high-resolution frame for face recognition"""
        if camera_id not in self.cameras:
            return None
        
        return self.cameras[camera_id].read()

    def get_frame_preview(self, camera_id, width=640, height=360):
        """Get low-resolution frame for web streaming (optimized)"""
        if camera_id not in self.cameras:
            return None
            
        # Use cached preview frame
        return self.cameras[camera_id].read_preview()

    def get_frame_jpeg(self, camera_id, quality=None, preview=True):
        if quality is None:
            quality = 90  # Increased default quality to 90%
            
        if preview:
            frame = self.get_frame_preview(camera_id)
        else:
            frame = self.get_frame(camera_id)
            
        if frame is None:
            return None
        
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

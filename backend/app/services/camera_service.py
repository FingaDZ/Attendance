import cv2
import threading
import time
from ..models import Camera
from ..database import SessionLocal

class CameraService:
    def __init__(self):
        self.cameras = {} # id -> cv2.VideoCapture
        self.active_streams = {} # id -> bool

    def start_camera(self, camera_id, source):
        if camera_id in self.cameras:
            return

        # Handle integer source for webcams
        if str(source).isdigit():
            source = int(source)
            
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
        if camera_id not in self.cameras:
            return None
        
        cap = self.cameras[camera_id]
        ret, frame = cap.read()
        if ret:
            return frame
        else:
            # Try to reconnect if stream is lost
            # For now, just return None
            return None

    def initialize_cameras_from_db(self):
        db = SessionLocal()
        cameras = db.query(Camera).filter(Camera.is_active == 1).all()
        for cam in cameras:
            self.start_camera(cam.id, cam.source)
        db.close()

camera_service = CameraService()

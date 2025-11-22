import insightface
from insightface.app import FaceAnalysis
import cv2
import numpy as np

def test_insightface():
    print("Initializing FaceAnalysis...")
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    print("FaceAnalysis initialized.")

    # Create a dummy image (black image) just to test the 'get' method
    img = np.zeros((640, 640, 3), dtype=np.uint8)
    
    print("Detecting faces in dummy image...")
    faces = app.get(img)
    print(f"Detection complete. Found {len(faces)} faces (expected 0).")
    print("InsightFace test passed!")

if __name__ == "__main__":
    test_insightface()

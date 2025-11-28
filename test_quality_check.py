
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath("backend"))

# We need to mock insightface before importing face_service because it initializes FaceAnalysis in __init__
with patch('insightface.app.FaceAnalysis'):
    from app.services.face_service import FaceService

class TestQualityCheck(unittest.TestCase):
    def setUp(self):
        # Re-instantiate service with mocked app
        with patch('insightface.app.FaceAnalysis'):
            self.service = FaceService()
            self.service.app = MagicMock()

    def test_quality_check_success(self):
        # Create a dummy image (black)
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode('.jpg', img)
        img_bytes = img_encoded.tobytes()
        
        # Mock face detection
        mock_face = MagicMock()
        # bbox: x1, y1, x2, y2
        # Center face: 640x640 image -> center is 320,320
        # Face 200x200 centered: 220, 220, 420, 420
        mock_face.bbox = np.array([220, 220, 420, 420], dtype=np.float32)
        
        self.service.app.get.return_value = [mock_face]
        
        is_good, msg = self.service.check_face_quality(img_bytes)
        print(f"Success Test: {is_good}, {msg}")
        self.assertTrue(is_good)
        self.assertEqual(msg, "Quality OK")

    def test_quality_check_no_face(self):
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode('.jpg', img)
        img_bytes = img_encoded.tobytes()
        
        self.service.app.get.return_value = []
        
        is_good, msg = self.service.check_face_quality(img_bytes)
        print(f"No Face Test: {is_good}, {msg}")
        self.assertFalse(is_good)
        self.assertEqual(msg, "No face detected")

    def test_quality_check_small_face(self):
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode('.jpg', img)
        img_bytes = img_encoded.tobytes()
        
        mock_face = MagicMock()
        # Small face 50x50
        mock_face.bbox = np.array([300, 300, 350, 350], dtype=np.float32)
        
        self.service.app.get.return_value = [mock_face]
        
        is_good, msg = self.service.check_face_quality(img_bytes)
        print(f"Small Face Test: {is_good}, {msg}")
        self.assertFalse(is_good)
        self.assertIn("Face too small", msg)

if __name__ == '__main__':
    unittest.main()

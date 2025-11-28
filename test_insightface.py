
import insightface
import cv2
import numpy as np

print("InsightFace version:", insightface.__version__)
try:
    app = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    print("InsightFace initialized successfully")
except Exception as e:
    print(f"Error initializing InsightFace: {e}")

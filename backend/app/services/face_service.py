"""
Optimized Face Service - InsightFace Only (v2.0.0)
Removed MediaPipe dependency for 3-5x performance improvement
"""

import insightface
from insightface.app import FaceAnalysis
import numpy as np
import cv2
import pickle
from .adaptive_training_service import adaptive_training_service
import threading

class FaceService:
    # ArcFace 112x112 alignment template (standard)
    ARCFACE_TEMPLATE = np.array([
        [38.2946, 51.6963],  # left eye
        [73.5318, 51.5014],  # right eye
        [56.0252, 71.7366],  # nose
        [41.5493, 92.3655],  # left mouth corner
        [70.7299, 92.2041]   # right mouth corner
    ], dtype=np.float32)
    
    def __init__(self):
        """Initialize InsightFace buffalo_l model"""
        self.app = FaceAnalysis(
            name='buffalo_l',
            providers=['CPUExecutionProvider'],
            allowed_modules=['detection', 'recognition']
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        self.known_embeddings = []
        self.known_names = []
        self.known_ids = []
        
        self.adaptive_training_service = adaptive_training_service
        self.lock = threading.Lock()  # Thread-safe operations
    
    def load_embeddings(self, db_employees):
        """Load all 6 embeddings from database into memory"""
        self.known_embeddings = []
        self.known_names = []
        self.known_ids = []
        
        for emp in db_employees:
            for emb_field in [emp.embedding1, emp.embedding2, emp.embedding3,
                            emp.embedding4, emp.embedding5, emp.embedding6]:
                if emb_field:
                    emb = pickle.loads(emb_field)
                    self.known_embeddings.append(emb)
                    self.known_names.append(emp.name)
                    self.known_ids.append(emp.id)
        
        if self.known_embeddings:
            self.known_embeddings = np.array(self.known_embeddings)
    
    # ==================== ALIGNMENT ====================
    
    def validate_keypoints(self, kps):
        """
        Validate keypoint ordering and quality
        Returns: (is_valid, kps_array)
        """
        if kps is None or len(kps) != 5:
            return False, None
        
        kps_array = np.array(kps, dtype=np.float32)
        
        # Check if keypoints are in valid range
        if np.any(kps_array < 0) or np.any(np.isnan(kps_array)):
            return False, None
        
        # Verify ordering: left_eye should be left of right_eye
        left_eye, right_eye = kps_array[0], kps_array[1]
        if left_eye[0] >= right_eye[0]:  # left eye should have smaller x
            return False, None
        
        # Verify nose is between eyes (roughly)
        nose = kps_array[2]
        if not (left_eye[0] < nose[0] < right_eye[0]):
            return False, None
        
        return True, kps_array
    
    def align_face_arcface(self, img, kps):
        """
        Align face using 5-point similarity transform
        Returns: 112x112 aligned face crop or None
        """
        # Validate keypoints
        is_valid, kps_array = self.validate_keypoints(kps)
        if not is_valid:
            return None
        
        # Estimate similarity transform
        tform, inliers = cv2.estimateAffinePartial2D(
            kps_array,
            self.ARCFACE_TEMPLATE,
            method=cv2.LMEDS
        )
        
        # Validate transform
        if tform is None:
            return None
        
        # Warp to 112x112 with bilinear interpolation
        aligned = cv2.warpAffine(
            img, tform, (112, 112),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
        
        return aligned
    
    # ==================== LIGHTWEIGHT LIVENESS ====================
    
    def calculate_texture_liveness(self, face_crop):
        """
        Lightweight texture-based liveness on cropped ROI
        Returns: liveness_score (0.0 to 1.0)
        """
        if face_crop is None or face_crop.size == 0:
            return 0.0
        
        try:
            # Convert to grayscale
            if len(face_crop.shape) == 3:
                gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_crop
            
            # Calculate Laplacian variance (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-1 range
            # Real faces: 100-500, photos/screens: 10-100
            if laplacian_var > 500:
                score_sharpness = 1.0
            elif laplacian_var > 100:
                score_sharpness = (laplacian_var - 100) / 400
            else:
                score_sharpness = laplacian_var / 100
            
            # Color variance (real faces have more color variation)
            if len(face_crop.shape) == 3:
                hsv = cv2.cvtColor(face_crop, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                color_var = np.std(s)
                score_color = min(1.0, color_var / 50)
            else:
                score_color = 0.5
            
            # Weighted average
            final_score = (score_sharpness * 0.7) + (score_color * 0.3)
            
            return float(min(1.0, max(0.0, final_score)))
        
        except Exception as e:
            print(f"Liveness calculation error: {e}")
            return 0.5  # Neutral score on error
    
    # ==================== PREPROCESSING ====================
    
    def normalize_image(self, img, max_dim=1280):
        """Resize image if too large, maintaining aspect ratio"""
        if img is None:
            return None
        
        h, w = img.shape[:2]
        if max(h, w) <= max_dim:
            return img
        
        scale = max_dim / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # ==================== FACE REGISTRATION ====================
    
    def register_face(self, image_bytes, is_grayscale=False):
        """
        Register face from image bytes
        Returns: (processed_bytes, embedding_pickle)
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Normalize
        img = self.normalize_image(img)
        
        # Detect face
        faces = self.app.get(img)
        if not faces:
            return None, None
        
        # Get largest face
        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
        face = faces[0]
        
        # Align face
        aligned = self.align_face_arcface(img, face.kps)
        if aligned is None:
            # Fallback: use face embedding without alignment
            return None, pickle.dumps(face.embedding)
        
        # Apply grayscale if requested
        if is_grayscale:
            aligned = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
            aligned = cv2.cvtColor(aligned, cv2.COLOR_GRAY2BGR)
        
        # Get embedding from aligned face
        aligned_faces = self.app.get(aligned)
        if aligned_faces:
            embedding = aligned_faces[0].embedding
        else:
            embedding = face.embedding  # Fallback
        
        # Return aligned image bytes and embedding
        _, img_encoded = cv2.imencode('.jpg', aligned)
        processed_bytes = img_encoded.tobytes()
        
        return processed_bytes, pickle.dumps(embedding)
    
    # ==================== FACE RECOGNITION ====================
    
    def is_face_centered(self, bbox, img_w, img_h):
        """Check if face is in central zone (50% of frame)"""
        x1, y1, x2, y2 = bbox
        face_cx = (x1 + x2) / 2
        face_cy = (y1 + y2) / 2
        
        img_cx = img_w / 2
        img_cy = img_h / 2
        
        zone_w = img_w * 0.5
        zone_h = img_h * 0.5
        
        zone_x1 = img_cx - zone_w / 2
        zone_y1 = img_cy - zone_h / 2
        zone_x2 = img_cx + zone_w / 2
        zone_y2 = img_cy + zone_h / 2
        
        return (zone_x1 <= face_cx <= zone_x2 and zone_y1 <= face_cy <= zone_y2)
    
    def recognize_faces(self, frame, db=None):
        """
        Optimized face recognition using InsightFace only
        Returns: list of detection results
        """
        # Normalize frame
        frame = self.normalize_image(frame, max_dim=1280)
        
        # Detect faces (thread-safe)
        with self.lock:
            try:
                faces = self.app.get(frame)
            except Exception as e:
                print(f"Detection error: {e}")
                return []
        
        results = []
        
        # No known faces
        if len(self.known_embeddings) == 0:
            for face in faces:
                results.append({
                    "name": "Unknown",
                    "bbox": face.bbox.tolist(),
                    "confidence": 0.0,
                    "employee_id": None,
                    "keypoints": face.kps.tolist(),
                    "liveness": 0.0
                })
            return results
        
        # Normalize known embeddings
        norm_known = np.linalg.norm(self.known_embeddings, axis=1, keepdims=True)
        known_embeddings_norm = self.known_embeddings / (norm_known + 1e-10)
        
        for face in faces:
            # Quality check: face size and detection confidence
            bbox_w = face.bbox[2] - face.bbox[0]
            bbox_h = face.bbox[3] - face.bbox[1]
            
            if bbox_w < 80 or bbox_h < 80:
                # Face too small, skip
                continue
            
            # Check positioning
            if not self.is_face_centered(face.bbox, frame.shape[1], frame.shape[0]):
                results.append({
                    "name": "Positioning...",
                    "bbox": face.bbox.tolist(),
                    "confidence": 0.0,
                    "employee_id": None,
                    "keypoints": face.kps.tolist(),
                    "liveness": 0.0
                })
                continue
            
            # Calculate liveness on face ROI
            x1, y1, x2, y2 = map(int, face.bbox)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            face_roi = frame[y1:y2, x1:x2]
            liveness_score = self.calculate_texture_liveness(face_roi)
            
            # Normalize embedding
            face_emb = face.embedding
            face_emb_norm = face_emb / (np.linalg.norm(face_emb) + 1e-10)
            
            # Compute similarity
            sims = np.dot(known_embeddings_norm, face_emb_norm)
            max_idx = np.argmax(sims)
            max_sim = sims[max_idx]
            
            print(f"Face detected: {self.known_names[max_idx]} ({max_sim:.3f}), Liveness: {liveness_score:.2f}")
            
            # Adaptive threshold based on liveness
            if liveness_score > 0.7:
                threshold = 0.83  # More tolerant
            elif liveness_score > 0.5:
                threshold = 0.85  # Standard
            else:
                threshold = 0.88  # More strict
            
            # Match
            if max_sim > threshold:
                name = self.known_names[max_idx]
                emp_id = self.known_ids[max_idx]
                
                results.append({
                    "name": name,
                    "bbox": face.bbox.tolist(),
                    "confidence": float(max_sim),
                    "employee_id": emp_id,
                    "keypoints": face.kps.tolist(),
                    "liveness": float(liveness_score)
                })
                
                # Adaptive training
                if db:
                    self.adaptive_training_service.process_recognition(
                        db, emp_id, face_emb, float(max_sim), liveness_score
                    )
            else:
                results.append({
                    "name": "Unknown",
                    "bbox": face.bbox.tolist(),
                    "confidence": float(max_sim),
                    "employee_id": None,
                    "keypoints": face.kps.tolist(),
                    "liveness": float(liveness_score)
                })
        
        return results
    
    # ==================== DRAWING ====================
    
    def draw_results(self, frame, results):
        """
        Draw detection results with 5 keypoints
        """
        if not results:
            return frame
        
        primary = results[0]
        name = primary["name"]
        conf = primary["confidence"]
        kps = np.array(primary["keypoints"])
        
        # Determine color and text
        if name == "Positioning...":
            color = (0, 165, 255)  # Orange
            text = "Position your face"
            subtext = "Center your face"
        elif conf < 0.85:
            color = (0, 0, 255)  # Red
            text = f"Precision: {conf:.0%}"
            subtext = "Minimum: 85%"
        else:
            color = (0, 255, 0)  # Green
            text = name
            subtext = "Verified"
        
        # Draw badge (top-left, 220x50)
        badge_w, badge_h = 220, 50
        bx1, by1 = 20, 20
        bx2, by2 = bx1 + badge_w, by1 + badge_h
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx1, by1), (bx2, by2), color, -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        
        cv2.putText(frame, text, (bx1 + 10, by1 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, subtext, (bx1 + 10, by1 + 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1)
        
        # Draw 5 keypoints (cyan dots)
        for point in kps:
            x, y = int(point[0]), int(point[1])
            cv2.circle(frame, (x, y), 3, (255, 255, 0), -1)
        
        return frame

# Singleton instance
face_service = FaceService()

import insightface
from insightface.app import FaceAnalysis
import numpy as np
import cv2
import pickle
from .landmark_service import landmark_service
from .liveness_service import get_liveness_service
from .landmark_service import landmark_service
from .liveness_service import get_liveness_service
from .adaptive_training_service import adaptive_training_service
# from .ensemble_service import ensemble_service

class FaceService:
    def __init__(self):
        # Initialize InsightFace with 106 landmarks support
        # providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if GPU available
        self.app = FaceAnalysis(
            name='buffalo_l',
            providers=['CPUExecutionProvider'],
            allowed_modules=['detection', 'recognition', 'landmark_3d_68']
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        self.known_embeddings = []
        self.known_names = []
        self.known_ids = []
        
        # Initialize landmark and liveness services
        self.landmark_service = landmark_service
        self.liveness_service = get_liveness_service(landmark_service)
        self.adaptive_training_service = adaptive_training_service
        # self.ensemble_service = ensemble_service

    def load_embeddings(self, db_employees):
        """Load all 6 embeddings from database into memory for fast lookup."""
        self.known_embeddings = []
        self.known_names = []
        self.known_ids = []
        
        for emp in db_employees:
            # Load all 6 embeddings for each employee (v1.6.5: increased from 3)
            for i, emb_field in enumerate([
                emp.embedding1, emp.embedding2, emp.embedding3,
                emp.embedding4, emp.embedding5, emp.embedding6
            ], 1):
                if emb_field:
                    emb = pickle.loads(emb_field)
                    self.known_embeddings.append(emb)
                    self.known_names.append(emp.name)
                    self.known_ids.append(emp.id)
        
        # Convert to numpy array for matrix operations
        if self.known_embeddings:
            self.known_embeddings = np.array(self.known_embeddings)

    # ==================== LIVENESS DETECTION (v1.6.0) ====================

    def calculate_liveness_score(self, img, bbox):
        """
        Calculate a liveness score (0.0 to 1.0) based on passive image analysis.
        Checks for:
        1. Sharpness (Blur detection) - Screens/prints are often blurry or have moiré.
        2. Color Distribution - Real faces have rich color variance.
        3. Exposure - Screens are often overexposed (self-luminous).
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # Ensure bbox is within image
        h, w = img.shape[:2]
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(w, x2); y2 = min(h, y2)
        
        face_img = img[y1:y2, x1:x2]
        if face_img.size == 0:
            return 0.0

        # 1. Sharpness (Laplacian Variance)
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize sharpness (heuristic: >100 is good, <50 is bad)
        score_sharpness = min(1.0, sharpness / 200.0)
        
        # 2. Color Analysis (HSV)
        hsv = cv2.cvtColor(face_img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Check for "flat" colors (typical of prints)
        std_h = np.std(h)
        std_s = np.std(s)
        
        # Real faces usually have some color variation
        score_color = min(1.0, (std_h + std_s) / 40.0)
        
        # 3. Exposure (V channel)
        mean_v = np.mean(v)
        # Penalize extreme overexposure (screen glare) or underexposure
        if mean_v > 230 or mean_v < 30:
            score_exposure = 0.5
        else:
            score_exposure = 1.0

        # Weighted Average
        # Sharpness is most important for detecting blur/screens
        final_score = (score_sharpness * 0.5) + (score_color * 0.3) + (score_exposure * 0.2)
        
        return float(min(1.0, max(0.0, final_score)))

    # ==================== PREPROCESSING METHODS ====================

    def normalize_image(self, img, max_dim=1280):
        """
        Resize image if it exceeds max_dim, maintaining aspect ratio.
        This ensures consistent input size for both high-res photos and video frames.
        """
        if img is None:
            return None
            
        h, w = img.shape[:2]
        if max(h, w) <= max_dim:
            return img
            
        scale = max_dim / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    def align_face(self, img, landmarks):
        """Align face by rotating to make eyes horizontal."""
        if landmarks is None or len(landmarks) < 2:
            return img
        
        # Get eye positions (landmarks[0] = left eye, landmarks[1] = right eye)
        left_eye = landmarks[0]
        right_eye = landmarks[1]
        
        # Calculate angle between eyes
        dY = right_eye[1] - left_eye[1]
        dX = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dY, dX))
        
        # Get image center
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        # Rotate image
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        aligned = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return aligned
    
    def crop_face_region(self, img, bbox, margin=0.3):
        """Crop face region with margin."""
        x1, y1, x2, y2 = map(int, bbox)
        
        # Add margin
        w = x2 - x1
        h = y2 - y1
        margin_w = int(w * margin)
        margin_h = int(h * margin)
        
        # Expand bbox with margin
        x1 = max(0, x1 - margin_w)
        y1 = max(0, y1 - margin_h)
        x2 = min(img.shape[1], x2 + margin_w)
        y2 = min(img.shape[0], y2 + margin_h)
        
        # Crop
        cropped = img[y1:y2, x1:x2]
        return cropped
    
    def resize_face(self, img, target_size=(200, 200)):
        """Resize face to target size while maintaining aspect ratio."""
        h, w = img.shape[:2]
        target_w, target_h = target_size
        
        # Calculate scaling factor
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Create canvas and center the resized image
        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas
    
    def enhance_quality(self, img):
        """Enhance image quality: gentle CLAHE only to preserve natural appearance."""
        # Convert to LAB color space for better processing
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply gentle CLAHE only (no histogram equalization, no aggressive processing)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge back
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def convert_to_grayscale(self, img):
        """Convert image to grayscale (3-channel for consistency)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Convert back to 3-channel for InsightFace compatibility
        gray_3ch = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return gray_3ch

    def normalize_colors(self, img):
        """Normalize colors (simple histogram equalization for V channel in HSV)."""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.equalizeHist(v)
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def preprocess_face(self, image_bytes, is_grayscale=False):
        """
        Preprocess face for registration:
        1. Detect face
        2. Crop with margin
        3. Align eyes
        4. Resize to standard size
        5. Enhance quality
        6. Convert to grayscale (if requested) or normalize
        7. Generate embedding
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Normalize large images first
        img = self.normalize_image(img)
        
        faces = self.app.get(img)
        if not faces:
            return None, None
            
        # Get largest face
        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
        target_face = faces[0]
        bbox = target_face.bbox
        landmarks = target_face.kps  # 5 keypoints
        
        # 3. Crop face region
        face_img = self.crop_face_region(img, bbox, margin=0.3)
        
        # 4. Align eyes
        aligned_img = self.align_face(face_img, landmarks)
        
        # 5. Resize to 200x200
        resized_img = self.resize_face(aligned_img, (200, 200))
        
        # 6. Enhance quality
        enhanced_img = self.enhance_quality(resized_img)
        
        # 7. Grayscale conversion (for photo2)
        if is_grayscale:
            enhanced_img = self.convert_to_grayscale(enhanced_img)
        else:
            # 8. Normalize colors (if not grayscale)
            enhanced_img = self.normalize_colors(enhanced_img)
        
        # 9. Generate embedding from preprocessed image
        processed_faces = self.app.get(enhanced_img)
        if not processed_faces:
            # Fallback: use original face embedding
            embedding = target_face.embedding
        else:
            embedding = processed_faces[0].embedding
        
        # Return preprocessed image bytes and embedding
        _, img_encoded = cv2.imencode('.jpg', enhanced_img)
        processed_bytes = img_encoded.tobytes()
        
        return processed_bytes, pickle.dumps(embedding)

    def register_face(self, image_bytes, is_grayscale=False):
        """Detect face in image, preprocess, and return embedding + processed image."""
        # Use the complete preprocessing pipeline
        processed_bytes, embedding_pickle = self.preprocess_face(image_bytes, is_grayscale)
        
        if processed_bytes is None or embedding_pickle is None:
            return None, None
        
        return processed_bytes, embedding_pickle

    def recognize_faces(self, frame, use_liveness=True, db=None):
        """
        Detect and recognize faces in a frame with enhanced landmarks and liveness detection.
        Returns list of (name, bbox, confidence, employee_id, landmarks, liveness_score)
        
        Args:
            frame: Image frame
            use_liveness: Boolean to enable liveness detection
            db: Optional database session for adaptive training
        """
        # Normalize input frame
        frame = self.normalize_image(frame)
        
        faces = self.app.get(frame)
        results = []

        if len(self.known_embeddings) == 0:
            for face in faces:
                # Extract precise landmarks using MediaPipe (468 points)
                kps = self.landmark_service.extract_landmarks_from_frame(frame, face.bbox)
                results.append(("Unknown", face.bbox, 0.0, None, kps, 0.0))
            return results

        # Normalize known embeddings
        norm_known = np.linalg.norm(self.known_embeddings, axis=1, keepdims=True)
        known_embeddings_norm = self.known_embeddings / (norm_known + 1e-10)

        for face in faces:
            # Extract precise landmarks using MediaPipe (468 points)
            kps = self.landmark_service.extract_landmarks_from_frame(frame, face.bbox)
            
            # Calculate liveness score
            liveness_score = 0.0
            if use_liveness and kps is not None:
                liveness_score = self.liveness_service.calculate_liveness_score(
                    frame, kps, face.bbox
                )
            
            # 1. Check Strict Position
            # If the ENTIRE face bbox is not within the central zone, skip recognition.
            if not self.is_face_strictly_centered(face.bbox, frame.shape[1], frame.shape[0]):
                results.append(("Positioning...", face.bbox, 0.0, None, kps, liveness_score))
                continue

            # Normalize face embedding
            face_emb = face.embedding
            face_emb_norm = face_emb / (np.linalg.norm(face_emb) + 1e-10)

            # Compute cosine similarity
            sims = np.dot(known_embeddings_norm, face_emb_norm)
            max_sim_idx = np.argmax(sims)
            max_sim = sims[max_sim_idx]
            
            print(f"Detected Face. Best Match: {self.known_names[max_sim_idx]} with Score: {max_sim:.4f}, Liveness: {liveness_score:.2f}")

            # Calculate adaptive threshold based on liveness
            threshold = self.calculate_adaptive_threshold(liveness_score)
            
            # --- Ensemble Method (Phase 3) - DISABLED due to dependency conflicts ---
            # if max_sim < threshold and max_sim > (threshold - 0.10):
            #     face_crop = self.crop_face_region(frame, face.bbox, margin=0.0)
            #     is_verified, dist = self.ensemble_service.verify_identity(face_crop, self.known_ids[max_sim_idx])
            #     if is_verified:
            #         print(f"✨ Ensemble Rescue: InsightFace {max_sim:.4f} -> DeepFace Verified (Dist: {dist:.4f})")
            #         max_sim = threshold + 0.02
            #     else:
            #         print(f"🚫 Ensemble Reject: InsightFace {max_sim:.4f} -> DeepFace Rejected (Dist: {dist:.4f})")
            
            if max_sim > threshold:
                name = self.known_names[max_sim_idx]
                emp_id = self.known_ids[max_sim_idx]
                results.append((name, face.bbox, float(max_sim), emp_id, kps, liveness_score))
                
                # Trigger Adaptive Training if DB session is provided
                if db is not None:
                    self.adaptive_training_service.process_recognition(
                        db, emp_id, face_emb, float(max_sim), liveness_score
                    )
            else:
                results.append(("Unknown", face.bbox, float(max_sim), None, kps, liveness_score))
        
        return results
    
    def calculate_adaptive_threshold(self, liveness_score):
        """
        Calculate adaptive recognition threshold based on liveness score.
        Higher liveness = lower threshold (more tolerant)
        Lower liveness = higher threshold (more strict)
        
        Args:
            liveness_score: Score from 0.0 to 1.0
            
        Returns:
            float: Threshold for face recognition
        """
        base_threshold = 0.85
        
        # If liveness is very high, we can be more tolerant
        if liveness_score > 0.85:
            return 0.80  # Reduce threshold by 5%
        elif liveness_score > 0.70:
            return 0.83  # Reduce threshold by 2%
        elif liveness_score > 0.50:
            return 0.85  # Keep base threshold
        else:
            # Low liveness = be more strict
            return 0.88  # Increase threshold by 3%

    def is_face_strictly_centered(self, bbox, img_w, img_h):
        # bbox: [x1, y1, x2, y2]
        x1, y1, x2, y2 = bbox
        
        # Calculate face center
        face_cx = (x1 + x2) / 2
        face_cy = (y1 + y2) / 2
        
        # Image center
        img_cx = img_w / 2
        img_cy = img_h / 2
        
        # Define "Central Zone" (e.g., middle 50% of the screen)
        zone_w = img_w * 0.5
        zone_h = img_h * 0.5
        
        zone_x1 = img_cx - zone_w / 2
        zone_y1 = img_cy - zone_h / 2
        zone_x2 = img_cx + zone_w / 2
        zone_y2 = img_cy + zone_h / 2
        
        # Check if face center is within the zone
        if (face_cx >= zone_x1 and face_cx <= zone_x2 and
            face_cy >= zone_y1 and face_cy <= zone_y2):
            return True
            
        return False

    def check_face_quality(self, image_bytes):
        """Check if face is large enough and clear."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        faces = self.app.get(img)
        
        if not faces:
            return False, "No face detected"
        
        # Sort by size
        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
        target_face = faces[0]
        
        # Check size (width and height > 100px)
        w = target_face.bbox[2] - target_face.bbox[0]
        h = target_face.bbox[3] - target_face.bbox[1]
        
        if w < 100 or h < 100:
            return False, f"Face too small ({int(w)}x{int(h)}). Please get closer."
            
        return True, "Quality OK"

    def process_profile_image(self, image_bytes):
        """
        Process the image: Keep face in color, make background grayscale.
        Returns processed image bytes.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Calculate circle parameters
        x1, y1, x2, y2 = map(int, face.bbox)
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        # Radius is half the diagonal of the bbox, or just half max dim
        radius = int(max(x2-x1, y2-y1) * 0.6) # Slightly larger than face
        
        cv2.circle(mask, (center_x, center_y), radius, 255, -1)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        # Combine
        # Where mask is 255 (white), use img. Where 0 (black), use gray_bgr
        result = np.where(mask[:, :, None] == 255, img, gray_bgr)
        
        # Encode back to bytes
        ret, buffer = cv2.imencode('.jpg', result)
        return buffer.tobytes()

face_service = FaceService()

import insightface
from insightface.app import FaceAnalysis
import numpy as np
import cv2
import pickle

class FaceService:
    def __init__(self):
        # Initialize InsightFace
        # providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if GPU available
        self.app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        self.known_embeddings = []
        self.known_names = []
        self.known_ids = []

    def load_embeddings(self, db_employees):
        """Load all 3 embeddings from database into memory for fast lookup."""
        self.known_embeddings = []
        self.known_names = []
        self.known_ids = []
        
        for emp in db_employees:
            # Load all 3 embeddings for each employee
            for i, emb_field in enumerate([emp.embedding1, emp.embedding2, emp.embedding3], 1):
                if emb_field:
                    emb = pickle.loads(emb_field)
                    self.known_embeddings.append(emb)
                    self.known_names.append(emp.name)
                    self.known_ids.append(emp.id)
        
        # Convert to numpy array for matrix operations
        if self.known_embeddings:
            self.known_embeddings = np.array(self.known_embeddings)

    def register_face(self, image_bytes):
        """Detect face in image and return embedding."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        faces = self.app.get(img)
        if not faces:
            return None
        
        # Assume the largest face is the target
        # Sort by area (bbox width * height)
        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
        target_face = faces[0]
        
        return pickle.dumps(target_face.embedding)

    def recognize_faces(self, frame):
        """
        Detect and recognize faces in a frame.
        Returns list of (name, bbox, confidence, employee_id, landmarks)
        """
        faces = self.app.get(frame)
        results = []

        if len(self.known_embeddings) == 0:
            for face in faces:
                # Return landmarks even if unknown
                kps = face.kps if hasattr(face, 'kps') else None
                results.append(("Unknown", face.bbox, 0.0, None, kps))
            return results

        # Normalize known embeddings
        norm_known = np.linalg.norm(self.known_embeddings, axis=1, keepdims=True)
        known_embeddings_norm = self.known_embeddings / (norm_known + 1e-10)

        for face in faces:
            kps = face.kps if hasattr(face, 'kps') else None
            
            # 1. Check Strict Position
            # If the ENTIRE face bbox is not within the central zone, skip recognition.
            if not self.is_face_strictly_centered(face.bbox, frame.shape[1], frame.shape[0]):
                results.append(("Positioning...", face.bbox, 0.0, None, kps))
                continue

            # Normalize face embedding
            face_emb = face.embedding
            face_emb_norm = face_emb / (np.linalg.norm(face_emb) + 1e-10)

            # Compute cosine similarity
            sims = np.dot(known_embeddings_norm, face_emb_norm)
            max_sim_idx = np.argmax(sims)
            max_sim = sims[max_sim_idx]
            
            print(f"Detected Face. Best Match: {self.known_names[max_sim_idx]} with Score: {max_sim:.4f}")

            if max_sim > 0.90:  # 90% confidence threshold
                name = self.known_names[max_sim_idx]
                emp_id = self.known_ids[max_sim_idx]
                results.append((name, face.bbox, float(max_sim), emp_id, kps))
            else:
                results.append(("Unknown", face.bbox, float(max_sim), None, kps))
        
        return results

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
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        faces = self.app.get(img)
        if not faces:
            return image_bytes # Return original if no face found
            
        # Use the largest face
        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
        face = faces[0]
        
        # Create mask
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        
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

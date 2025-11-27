"""
Service de détection de landmarks précis utilisant MediaPipe Face Mesh (468 points)
Compatible Python 3.10+ et optimisé pour CPU
"""
import numpy as np
import cv2
import mediapipe as mp
from typing import Optional, Tuple, List


class LandmarkService:
    """
    Service pour extraire et analyser les landmarks faciaux avec MediaPipe
    Utilise Face Mesh pour 468 points 3D ultra-précis
    """
    
    def __init__(self):
        # Initialiser MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,  # Active iris tracking (10 points par iris)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Indices des landmarks MediaPipe pour différentes parties du visage
        # Basé sur la documentation MediaPipe Face Mesh
        # https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
        
        # Yeux (contours complets)
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]  # 6 points principaux
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]  # 6 points principaux
        
        # Iris (si refine_landmarks=True)
        self.LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]  # 5 points
        self.RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]  # 5 points
        
        # Nez
        self.NOSE_INDICES = [1, 2, 98, 327, 168, 6, 197, 195, 5]  # 9 points
        
        # Bouche (contours externe et interne)
        self.MOUTH_OUTER_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308]
        self.MOUTH_INNER_INDICES = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415]
        
        # Cache pour les landmarks précédents (pour tracking)
        self.previous_landmarks = None
        
    def extract_landmarks_from_frame(self, frame: np.ndarray, bbox: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """
        Extrait les landmarks MediaPipe d'une frame
        
        Args:
            frame: Image BGR (OpenCV format)
            bbox: Bounding box optionnelle [x1, y1, x2, y2] pour cropping
            
        Returns:
            np.ndarray: Array de landmarks (468, 3) [x, y, z] ou None
        """
        # Convertir BGR en RGB pour MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Si bbox fournie, cropper pour améliorer la performance
        if bbox is not None:
            x1, y1, x2, y2 = map(int, bbox)
            h, w = frame.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            rgb_frame = rgb_frame[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1
        else:
            offset_x, offset_y = 0, 0
            h, w = frame.shape[:2]
        
        # Détecter avec MediaPipe
        results = self.mp_face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None
            
        # Extraire les 468 landmarks (+ 10 iris si refine_landmarks=True)
        face_landmarks = results.multi_face_landmarks[0]
        
        landmarks_3d = []
        for landmark in face_landmarks.landmark:
            # Convertir coordonnées normalisées en pixels
            x = int(landmark.x * (x2 - x1 if bbox is not None else w)) + offset_x
            y = int(landmark.y * (y2 - y1 if bbox is not None else h)) + offset_y
            z = landmark.z  # Profondeur relative
            landmarks_3d.append([x, y, z])
            
        landmarks_array = np.array(landmarks_3d, dtype=np.float32)
        
        # Mettre en cache
        self.previous_landmarks = landmarks_array
        
        return landmarks_array
    
    def extract_landmarks_from_face(self, face) -> Optional[np.ndarray]:
        """
        Méthode de compatibilité avec InsightFace
        Essaie d'abord MediaPipe, puis fallback sur InsightFace landmarks
        
        Args:
            face: Objet face retourné par InsightFace
            
        Returns:
            np.ndarray: Array de landmarks ou None
        """
        # Si on a des landmarks précédents de MediaPipe, les utiliser
        if self.previous_landmarks is not None:
            return self.previous_landmarks
        
        # Fallback: utiliser les landmarks InsightFace
        if hasattr(face, 'landmark_2d_106') and face.landmark_2d_106 is not None:
            return face.landmark_2d_106
        elif hasattr(face, 'kps') and face.kps is not None:
            return face.kps
            
        return None
    
    def get_eye_landmarks(self, landmarks: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Extrait les landmarks des yeux
        
        Args:
            landmarks: Array de landmarks complet
            
        Returns:
            Tuple[left_eye, right_eye]: Arrays de landmarks pour chaque œil
        """
        if landmarks is None:
            return None, None
        
        # Si MediaPipe (468+ points)
        if len(landmarks) >= 468:
            left_eye = landmarks[self.LEFT_EYE_INDICES]
            right_eye = landmarks[self.RIGHT_EYE_INDICES]
            return left_eye, right_eye
        
        # Si InsightFace 106 points
        elif len(landmarks) >= 51:
            LEFT_EYE_INDICES_106 = list(range(33, 42))
            RIGHT_EYE_INDICES_106 = list(range(42, 51))
            left_eye = landmarks[LEFT_EYE_INDICES_106]
            right_eye = landmarks[RIGHT_EYE_INDICES_106]
            return left_eye, right_eye
        
        # Si 5 points basiques
        elif len(landmarks) >= 5:
            left_eye = landmarks[0:1]
            right_eye = landmarks[1:2]
            return left_eye, right_eye
        
        return None, None
    
    def get_mouth_landmarks(self, landmarks: np.ndarray) -> Optional[np.ndarray]:
        """
        Extrait les landmarks de la bouche
        
        Args:
            landmarks: Array de landmarks complet
            
        Returns:
            np.ndarray: Landmarks de la bouche ou None
        """
        if landmarks is None:
            return None
        
        # MediaPipe (468+ points)
        if len(landmarks) >= 468:
            mouth_outer = landmarks[self.MOUTH_OUTER_INDICES]
            mouth_inner = landmarks[self.MOUTH_INNER_INDICES]
            return np.vstack([mouth_outer, mouth_inner])
        
        # InsightFace 106 points
        elif len(landmarks) >= 76:
            MOUTH_OUTER_INDICES_106 = list(range(60, 68))
            MOUTH_INNER_INDICES_106 = list(range(68, 76))
            mouth_outer = landmarks[MOUTH_OUTER_INDICES_106]
            mouth_inner = landmarks[MOUTH_INNER_INDICES_106]
            return np.vstack([mouth_outer, mouth_inner])
        
        # 5 points basiques
        elif len(landmarks) >= 5:
            return landmarks[3:5]
        
        return None
    
    def get_nose_landmarks(self, landmarks: np.ndarray) -> Optional[np.ndarray]:
        """
        Extrait les landmarks du nez
        
        Args:
            landmarks: Array de landmarks complet
            
        Returns:
            np.ndarray: Landmarks du nez ou None
        """
        if landmarks is None:
            return None
        
        # MediaPipe (468+ points)
        if len(landmarks) >= 468:
            return landmarks[self.NOSE_INDICES]
        
        # InsightFace 106 points
        elif len(landmarks) >= 60:
            NOSE_INDICES_106 = list(range(51, 60))
            return landmarks[NOSE_INDICES_106]
        
        # 5 points basiques
        elif len(landmarks) >= 5:
            return landmarks[2:3]
        
        return None
    
    def calculate_eye_aspect_ratio(self, eye_landmarks: np.ndarray) -> float:
        """
        Calcule l'Eye Aspect Ratio (EAR) pour détecter les clignements
        
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Args:
            eye_landmarks: Landmarks d'un œil (au moins 6 points)
            
        Returns:
            float: EAR value (0.0 si pas assez de points)
        """
        if eye_landmarks is None or len(eye_landmarks) < 6:
            return 0.0
        
        # Calculer les distances verticales
        A = np.linalg.norm(eye_landmarks[1][:2] - eye_landmarks[5][:2])
        B = np.linalg.norm(eye_landmarks[2][:2] - eye_landmarks[4][:2])
        
        # Calculer la distance horizontale
        C = np.linalg.norm(eye_landmarks[0][:2] - eye_landmarks[3][:2])
        
        # Éviter division par zéro
        if C == 0:
            return 0.0
        
        # Calculer EAR
        ear = (A + B) / (2.0 * C)
        
        return ear
    
    def calculate_mouth_aspect_ratio(self, mouth_landmarks: np.ndarray) -> float:
        """
        Calcule le Mouth Aspect Ratio (MAR) pour détecter l'ouverture de la bouche
        
        Args:
            mouth_landmarks: Landmarks de la bouche
            
        Returns:
            float: MAR value
        """
        if mouth_landmarks is None or len(mouth_landmarks) < 8:
            return 0.0
        
        # Hauteur de la bouche (distance verticale)
        height = np.linalg.norm(mouth_landmarks[2][:2] - mouth_landmarks[6][:2])
        
        # Largeur de la bouche (distance horizontale)
        width = np.linalg.norm(mouth_landmarks[0][:2] - mouth_landmarks[4][:2])
        
        # Éviter division par zéro
        if width == 0:
            return 0.0
        
        # MAR
        mar = height / width
        
        return mar
    
    def calculate_facial_symmetry(self, landmarks: np.ndarray) -> float:
        """
        Calcule la symétrie faciale (visage réel = plus symétrique)
        
        Args:
            landmarks: Array de landmarks complet
            
        Returns:
            float: Score de symétrie (0.0 à 1.0)
        """
        if landmarks is None or len(landmarks) < 5:
            return 0.5  # Neutre
        
        # Calculer le centre du visage
        if len(landmarks) >= 468:
            # MediaPipe: utiliser le point du nez (index 1)
            center_x = landmarks[1][0]
        elif len(landmarks) >= 60:
            # InsightFace 106: utiliser le nez
            center_x = landmarks[51][0]
        else:
            # 5 points: utiliser la moyenne
            center_x = np.mean(landmarks[:, 0])
        
        # Séparer les points gauche et droite
        left_points = landmarks[landmarks[:, 0] < center_x]
        right_points = landmarks[landmarks[:, 0] >= center_x]
        
        if len(left_points) == 0 or len(right_points) == 0:
            return 0.5
        
        # Calculer les distances moyennes au centre
        left_dist = np.mean(np.abs(left_points[:, 0] - center_x))
        right_dist = np.mean(np.abs(right_points[:, 0] - center_x))
        
        # Calculer la symétrie (1.0 = parfaitement symétrique)
        if max(left_dist, right_dist) == 0:
            return 0.5
        
        symmetry = 1.0 - abs(left_dist - right_dist) / max(left_dist, right_dist)
        
        return symmetry
    
    def draw_landmarks(self, frame: np.ndarray, landmarks: np.ndarray, 
                      color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """
        Dessine les landmarks sur une image pour visualisation
        
        Args:
            frame: Image sur laquelle dessiner
            landmarks: Array de landmarks (N, 2 ou 3)
            color: Couleur BGR des points
            
        Returns:
            np.ndarray: Image avec landmarks dessinés
        """
        if landmarks is None:
            return frame
        
        result = frame.copy()
        
        for point in landmarks:
            x, y = int(point[0]), int(point[1])
            cv2.circle(result, (x, y), 1, color, -1)
        
        return result
    
    def get_landmark_quality_score(self, landmarks: np.ndarray) -> float:
        """
        Évalue la qualité des landmarks détectés
        
        Args:
            landmarks: Array de landmarks
            
        Returns:
            float: Score de qualité (0.0 à 1.0)
        """
        if landmarks is None:
            return 0.0
        
        score = 0.0
        
        # 1. Nombre de points (plus = mieux)
        if len(landmarks) >= 468:
            score += 0.5  # MediaPipe 468 points = excellent
        elif len(landmarks) >= 106:
            score += 0.4
        elif len(landmarks) >= 68:
            score += 0.3
        elif len(landmarks) >= 5:
            score += 0.2
        
        # 2. Symétrie
        symmetry = self.calculate_facial_symmetry(landmarks)
        score += symmetry * 0.3
        
        # 3. Distribution des points (pas tous au même endroit)
        if len(landmarks) > 1:
            std_x = np.std(landmarks[:, 0])
            std_y = np.std(landmarks[:, 1])
            
            # Normaliser (bonne distribution = std > 20 pixels)
            distribution_score = min(1.0, (std_x + std_y) / 100.0)
            score += distribution_score * 0.2
        
        return min(1.0, score)
    
    def close(self):
        """Libère les ressources MediaPipe"""
        if hasattr(self, 'mp_face_mesh'):
            self.mp_face_mesh.close()


# Instance globale
landmark_service = LandmarkService()

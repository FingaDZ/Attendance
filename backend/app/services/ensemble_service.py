"""
Service Ensemble pour la reconnaissance faciale (InsightFace + DeepFace).
Utilise DeepFace (ArcFace) comme expert pour valider les cas incertains.
"""
import numpy as np
import cv2
import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from ..models import Employee

# Configuration du logging
logger = logging.getLogger(__name__)

# Import DeepFace lazily or handle potential import errors
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    logger.error("DeepFace not installed. Ensemble method will be disabled.")
    DEEPFACE_AVAILABLE = False

class EnsembleService:
    """
    Gère la validation par DeepFace (ArcFace).
    """
    
    def __init__(self):
        self.model_name = "ArcFace"
        self.embeddings: Dict[int, List[List[float]]] = {} # {employee_id: [embedding1, ...]}
        self.threshold = 0.68 # Seuil par défaut pour ArcFace (Cosine)
        self.initialized = False

    def initialize(self, db: Session):
        """
        Charge le modèle ArcFace et génère les embeddings pour tous les employés.
        Cette méthode doit être appelée au démarrage de l'application.
        """
        if not DEEPFACE_AVAILABLE:
            logger.warning("DeepFace unavailable. Skipping initialization.")
            return

        if self.initialized:
            return

        logger.info("Initializing Ensemble Service (DeepFace ArcFace)...")
        try:
            # Charger les employés
            employees = db.query(Employee).all()
            count = 0
            
            for emp in employees:
                emp_embeddings = []
                # Traiter chaque photo stockée (jusqu'à 6)
                photos = [emp.photo1, emp.photo2, emp.photo3, emp.photo4, emp.photo5, emp.photo6]
                
                for i, photo_bytes in enumerate(photos):
                    if photo_bytes:
                        try:
                            # Convertir bytes -> numpy image
                            nparr = np.frombuffer(photo_bytes, np.uint8)
                            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if img is None:
                                continue
                                
                            # Générer l'embedding ArcFace
                            # detector_backend="skip" car les photos en BDD sont déjà croppées/traitées
                            embedding_objs = DeepFace.represent(
                                img_path=img, 
                                model_name=self.model_name, 
                                enforce_detection=False,
                                detector_backend="skip"
                            )
                            
                            if embedding_objs:
                                embedding = embedding_objs[0]["embedding"]
                                emp_embeddings.append(embedding)
                                
                        except Exception as e:
                            logger.warning(f"Failed to generate ArcFace embedding for employee {emp.id} photo {i+1}: {e}")
                
                if emp_embeddings:
                    self.embeddings[emp.id] = emp_embeddings
                    count += 1
            
            self.initialized = True
            logger.info(f"Ensemble Service initialized with {count} employees loaded.")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ensemble Service: {e}")

    def verify_identity(self, face_img: np.ndarray, employee_id: int) -> Tuple[bool, float]:
        """
        Vérifie si le visage correspond à l'employé donné en utilisant ArcFace.
        
        Args:
            face_img: Image du visage (numpy array, BGR)
            employee_id: ID de l'employé à vérifier
            
        Returns:
            (is_verified, distance): Tuple (Booléen, Distance Cosinus)
        """
        if not self.initialized or not DEEPFACE_AVAILABLE:
            return False, 1.0
            
        if employee_id not in self.embeddings:
            return False, 1.0

        try:
            # Générer l'embedding pour le visage d'entrée
            # detector_backend="skip" car face_img est déjà le visage croppé par InsightFace
            embedding_objs = DeepFace.represent(
                img_path=face_img,
                model_name=self.model_name,
                enforce_detection=False,
                detector_backend="skip"
            )
            
            if not embedding_objs:
                return False, 1.0
                
            target_embedding = embedding_objs[0]["embedding"]
            
            # Comparer avec tous les embeddings connus pour cet employé
            known_embeddings = self.embeddings[employee_id]
            distances = []
            
            for known_emb in known_embeddings:
                # Calcul de la distance Cosinus
                # DeepFace: distance = 1 - cosine_similarity
                a = np.array(target_embedding)
                b = np.array(known_emb)
                
                norm_a = np.linalg.norm(a)
                norm_b = np.linalg.norm(b)
                
                if norm_a == 0 or norm_b == 0:
                    distances.append(1.0)
                    continue
                    
                cosine_similarity = np.dot(a, b) / (norm_a * norm_b)
                distance = 1 - cosine_similarity
                distances.append(distance)
            
            if not distances:
                return False, 1.0
                
            # Prendre la meilleure distance (la plus petite)
            min_distance = min(distances)
            is_verified = min_distance < self.threshold
            
            logger.info(f"Ensemble Verify: Emp {employee_id} - Dist: {min_distance:.4f} (Thresh: {self.threshold}) -> {is_verified}")
            
            return is_verified, min_distance
            
        except Exception as e:
            logger.error(f"Ensemble verification failed: {e}")
            return False, 1.0

# Instance globale
ensemble_service = EnsembleService()

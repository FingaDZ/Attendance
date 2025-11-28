"""
Service d'entraînement adaptatif pour la mise à jour automatique des profils biométriques.
Permet au système d'apprendre les changements d'apparence (barbe, vieillissement, etc.)
"""
import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from ..models import Employee
import logging

# Configuration du logging
logger = logging.getLogger(__name__)

class AdaptiveTrainingService:
    """
    Gère l'apprentissage continu des embeddings faciaux.
    Utilise une moyenne pondérée pour adapter progressivement les profils.
    """
    
    def __init__(self):
        # Configuration
        self.CONFIDENCE_THRESHOLD = 0.90  # Seuil très strict pour apprendre
        self.LIVENESS_THRESHOLD = 0.80    # Seuil très strict de vivacité
        self.STABILITY_COUNT = 3          # Nombre de reconnaissances consécutives requises
        self.UPDATE_INTERVAL = 86400      # 24 heures en secondes (1 update / jour max)
        self.LEARNING_RATE = 0.1          # Poids du nouvel embedding (10%)
        
        # Cache pour suivre l'historique récent: {employee_id: {'count': int, 'last_update': timestamp}}
        self.history: Dict[int, Dict] = {}
        
    def process_recognition(self, db: Session, employee_id: int, 
                           current_embedding: np.ndarray, 
                           confidence: float, 
                           liveness_score: float) -> bool:
        """
        Traite une reconnaissance réussie et décide si une mise à jour est nécessaire.
        
        Args:
            db: Session de base de données
            employee_id: ID de l'employé reconnu
            current_embedding: Embedding du visage actuel
            confidence: Score de confiance de la reconnaissance
            liveness_score: Score de vivacité
            
        Returns:
            bool: True si une mise à jour a été effectuée, False sinon
        """
        # 1. Vérifier les critères de sécurité de base
        if confidence < self.CONFIDENCE_THRESHOLD or liveness_score < self.LIVENESS_THRESHOLD:
            # Réinitialiser le compteur si la confiance baisse trop (sécurité)
            if confidence < 0.85:
                self._reset_counter(employee_id)
            return False
            
        # 2. Initialiser l'historique si nécessaire
        if employee_id not in self.history:
            self.history[employee_id] = {
                'count': 0,
                'last_update': 0,
                'accumulated_embedding': None
            }
            
        state = self.history[employee_id]
        now = time.time()
        
        # 3. Vérifier l'intervalle de temps (Rate Limiting)
        if now - state['last_update'] < self.UPDATE_INTERVAL:
            return False
            
        # 4. Accumuler pour la stabilité
        state['count'] += 1
        
        # Accumuler l'embedding (moyenne temporaire)
        if state['accumulated_embedding'] is None:
            state['accumulated_embedding'] = current_embedding
        else:
            # Moyenne simple des embeddings candidats
            state['accumulated_embedding'] = (state['accumulated_embedding'] + current_embedding) / 2
            
        logger.info(f"Adaptive Training: Employee {employee_id} - Stability {state['count']}/{self.STABILITY_COUNT}")
        
        # 5. Si stabilité atteinte, effectuer la mise à jour
        if state['count'] >= self.STABILITY_COUNT:
            success = self._update_employee_profile(db, employee_id, state['accumulated_embedding'])
            if success:
                # Mettre à jour l'état
                state['last_update'] = now
                state['count'] = 0
                state['accumulated_embedding'] = None
                return True
                
        return False
    
    def _update_employee_profile(self, db: Session, employee_id: int, new_face_embedding: np.ndarray) -> bool:
        """
        Met à jour l'embedding en base de données avec une moyenne pondérée.
        Choisit l'embedding le plus proche parmi les 6 disponibles.
        """
        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return False
                
            import pickle
            
            # Find the closest embedding to update
            best_idx = -1
            best_sim = -1.0
            best_embedding = None
            
            embeddings = []
            # Load all 6 embeddings
            for i in range(1, 7):
                emb_field = getattr(employee, f'embedding{i}', None)
                if emb_field:
                    try:
                        emb = pickle.loads(emb_field)
                        embeddings.append((i, emb))
                    except:
                        pass
            
            if not embeddings:
                return False
                
            # Normalize new embedding
            new_emb_norm = new_face_embedding / (np.linalg.norm(new_face_embedding) + 1e-10)
            
            # Find closest
            for idx, emb in embeddings:
                emb_norm = emb / (np.linalg.norm(emb) + 1e-10)
                sim = np.dot(emb_norm, new_emb_norm)
                if sim > best_sim:
                    best_sim = sim
                    best_idx = idx
                    best_embedding = emb
            
            if best_idx == -1:
                return False
                
            # Update the best matching embedding
            # New = (Old * 0.9) + (New * 0.1)
            updated_embedding = (best_embedding * (1.0 - self.LEARNING_RATE)) + (new_face_embedding * self.LEARNING_RATE)
            
            # Normaliser à nouveau
            updated_embedding = updated_embedding / np.linalg.norm(updated_embedding)
            
            # Encoder et sauvegarder
            setattr(employee, f'embedding{best_idx}', pickle.dumps(updated_embedding))
            
            db.commit()
            logger.info(f"✅ PROFILE UPDATED: Employee {employee_id} (Embedding {best_idx}) adapted to new appearance.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update employee profile: {e}")
            db.rollback()
            return False
            
    def _reset_counter(self, employee_id: int):
        """Réinitialise le compteur de stabilité pour un employé."""
        if employee_id in self.history:
            self.history[employee_id]['count'] = 0
            self.history[employee_id]['accumulated_embedding'] = None

# Instance globale
adaptive_training_service = AdaptiveTrainingService()

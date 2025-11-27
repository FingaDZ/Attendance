"""
Service de détection de vivacité (liveness detection)
Détecte si l'utilisateur est une personne réelle et non une photo/vidéo
"""
import numpy as np
import cv2
from typing import List, Tuple, Optional
from .landmark_service import LandmarkService


class LivenessService:
    """
    Service de détection de vivacité utilisant plusieurs techniques:
    1. Détection de clignement d'yeux (Eye Aspect Ratio)
    2. Analyse de mouvement de tête
    3. Analyse de texture et profondeur
    4. Symétrie faciale
    """
    
    def __init__(self, landmark_service: LandmarkService):
        self.landmark_service = landmark_service
        
        # Seuils de détection
        self.EAR_THRESHOLD = 0.21  # Seuil pour détecter un clignement
        self.EAR_CONSEC_FRAMES = 2  # Nombre de frames consécutives pour confirmer un clignement
        
        # Historique pour détection de mouvement
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_counter = 0
        
        # Historique de landmarks pour mouvement
        self.landmark_history: List[np.ndarray] = []
        self.max_history = 30  # Garder 30 frames d'historique
        
    def detect_blink(self, left_eye: np.ndarray, right_eye: np.ndarray) -> Tuple[bool, float]:
        """
        Détecte un clignement d'yeux en utilisant l'Eye Aspect Ratio (EAR)
        
        Args:
            left_eye: Landmarks de l'œil gauche
            right_eye: Landmarks de l'œil droit
            
        Returns:
            Tuple[is_blink, avg_ear]: (True si clignement détecté, EAR moyen)
        """
        # Calculer EAR pour chaque œil
        left_ear = self.landmark_service.calculate_eye_aspect_ratio(left_eye)
        right_ear = self.landmark_service.calculate_eye_aspect_ratio(right_eye)
        
        # EAR moyen
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Clignement détecté si EAR < seuil
        is_blink = avg_ear < self.EAR_THRESHOLD
        
        return is_blink, avg_ear
    
    def track_blinks(self, left_eye: np.ndarray, right_eye: np.ndarray) -> int:
        """
        Suit les clignements au fil du temps
        
        Args:
            left_eye: Landmarks de l'œil gauche
            right_eye: Landmarks de l'œil droit
            
        Returns:
            int: Nombre total de clignements détectés
        """
        is_blink, ear = self.detect_blink(left_eye, right_eye)
        
        if is_blink:
            self.blink_counter += 1
        else:
            # Si les yeux étaient fermés et sont maintenant ouverts
            if self.blink_counter >= self.EAR_CONSEC_FRAMES:
                self.total_blinks += 1
            self.blink_counter = 0
        
        self.frame_counter += 1
        
        return self.total_blinks
    
    def detect_head_movement(self, landmarks: np.ndarray) -> Tuple[bool, float]:
        """
        Détecte le mouvement de tête en analysant l'historique des landmarks
        
        Args:
            landmarks: Landmarks actuels du visage
            
        Returns:
            Tuple[has_movement, movement_score]: (True si mouvement détecté, score de mouvement)
        """
        # Ajouter à l'historique
        self.landmark_history.append(landmarks.copy())
        
        # Limiter la taille de l'historique
        if len(self.landmark_history) > self.max_history:
            self.landmark_history.pop(0)
        
        # Besoin d'au moins 10 frames pour détecter le mouvement
        if len(self.landmark_history) < 10:
            return False, 0.0
        
        # Calculer le mouvement en comparant la position du nez
        nose_landmarks = [self.landmark_service.get_nose_landmarks(lm) for lm in self.landmark_history]
        
        # Filtrer les None
        nose_landmarks = [n for n in nose_landmarks if n is not None and len(n) > 0]
        
        if len(nose_landmarks) < 10:
            return False, 0.0
        
        # Extraire les positions centrales du nez
        nose_positions = np.array([n[0] if len(n) > 0 else [0, 0] for n in nose_landmarks])
        
        # Calculer la variation de position
        x_variation = np.std(nose_positions[:, 0])
        y_variation = np.std(nose_positions[:, 1])
        
        total_variation = x_variation + y_variation
        
        # Mouvement détecté si variation > 5 pixels
        has_movement = total_variation > 5.0
        
        # Score normalisé (0.0 à 1.0)
        movement_score = min(1.0, total_variation / 20.0)
        
        return has_movement, movement_score
    
    def calculate_texture_score(self, frame: np.ndarray, bbox: np.ndarray) -> float:
        """
        Analyse la texture de la peau pour détecter les photos/écrans
        Les photos ont souvent une texture plus lisse ou des motifs de moiré
        
        Args:
            frame: Image complète
            bbox: Bounding box du visage [x1, y1, x2, y2]
            
        Returns:
            float: Score de texture (0.0 à 1.0, plus élevé = plus réel)
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # Assurer que bbox est dans l'image
        h, w = frame.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        
        face_img = frame[y1:y2, x1:x2]
        
        if face_img.size == 0:
            return 0.0
        
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        
        # 1. Netteté (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(1.0, laplacian_var / 200.0)
        
        # 2. Variation de couleur (HSV)
        hsv = cv2.cvtColor(face_img, cv2.COLOR_BGR2HSV)
        h_channel, s_channel, v_channel = cv2.split(hsv)
        
        # Les visages réels ont plus de variation de couleur
        color_variation = (np.std(h_channel) + np.std(s_channel)) / 2.0
        color_score = min(1.0, color_variation / 30.0)
        
        # 3. Détection de moiré (motifs répétitifs des écrans)
        # Utiliser FFT pour détecter les fréquences régulières
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # Les écrans ont des pics de fréquence réguliers
        # Un visage réel a un spectre plus distribué
        spectrum_std = np.std(magnitude_spectrum)
        moire_score = min(1.0, spectrum_std / 10000.0)
        
        # Score combiné
        texture_score = (sharpness_score * 0.4 + color_score * 0.3 + moire_score * 0.3)
        
        return texture_score
    
    def calculate_liveness_score(self, frame: np.ndarray, landmarks: np.ndarray, 
                                 bbox: np.ndarray) -> float:
        """
        Calcule un score de vivacité global combinant plusieurs métriques
        
        Args:
            frame: Image complète
            landmarks: Landmarks du visage
            bbox: Bounding box du visage
            
        Returns:
            float: Score de vivacité (0.0 à 1.0)
        """
        score = 0.0
        
        # 1. Qualité des landmarks (20%)
        landmark_quality = self.landmark_service.get_landmark_quality_score(landmarks)
        score += landmark_quality * 0.2
        
        # 2. Symétrie faciale (15%)
        symmetry = self.landmark_service.calculate_facial_symmetry(landmarks)
        score += symmetry * 0.15
        
        # 3. Texture de peau (25%)
        texture_score = self.calculate_texture_score(frame, bbox)
        score += texture_score * 0.25
        
        # 4. Mouvement de tête (20%)
        has_movement, movement_score = self.detect_head_movement(landmarks)
        score += movement_score * 0.2
        
        # 5. État des yeux (20%)
        left_eye, right_eye = self.landmark_service.get_eye_landmarks(landmarks)
        if left_eye is not None and right_eye is not None:
            is_blink, ear = self.detect_blink(left_eye, right_eye)
            
            # Yeux ouverts normalement = bon signe
            if 0.2 < ear < 0.4:
                score += 0.2
            elif ear >= 0.15:  # Yeux partiellement ouverts
                score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def challenge_blink_sequence(self, video_frames: List[np.ndarray], 
                                 face_service) -> Tuple[bool, int, str]:
        """
        Challenge de vivacité: demander à l'utilisateur de cligner des yeux
        Analyse une séquence de frames vidéo
        
        Args:
            video_frames: Liste de frames vidéo
            face_service: Service de reconnaissance faciale pour détecter les visages
            
        Returns:
            Tuple[success, blink_count, message]: (Succès, nombre de clignements, message)
        """
        blink_count = 0
        was_open = True
        consecutive_closed = 0
        
        for frame in video_frames:
            # Détecter le visage
            faces = face_service.app.get(frame)
            
            if not faces:
                continue
            
            face = faces[0]
            landmarks = self.landmark_service.extract_landmarks_from_face(face)
            
            if landmarks is None:
                continue
            
            # Obtenir les landmarks des yeux
            left_eye, right_eye = self.landmark_service.get_eye_landmarks(landmarks)
            
            if left_eye is None or right_eye is None:
                continue
            
            # Détecter le clignement
            is_blink, ear = self.detect_blink(left_eye, right_eye)
            
            # Détecter la transition ouvert -> fermé -> ouvert
            if is_blink:
                consecutive_closed += 1
                if was_open and consecutive_closed >= 2:  # Yeux fermés pendant au moins 2 frames
                    was_open = False
            else:
                if not was_open and consecutive_closed >= 2:  # Yeux étaient fermés
                    blink_count += 1
                was_open = True
                consecutive_closed = 0
        
        # Succès si au moins 1 clignement détecté
        success = blink_count >= 1
        
        if success:
            message = f"Vivacité confirmée: {blink_count} clignement(s) détecté(s)"
        else:
            message = "Aucun clignement détecté. Veuillez cligner des yeux."
        
        return success, blink_count, message
    
    def reset_tracking(self):
        """Réinitialise les compteurs de suivi"""
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_counter = 0
        self.landmark_history.clear()
    
    def get_liveness_report(self) -> dict:
        """
        Retourne un rapport détaillé de vivacité
        
        Returns:
            dict: Rapport avec toutes les métriques
        """
        blink_rate = 0.0
        if self.frame_counter > 0:
            # Taux de clignement par seconde (en supposant 30 fps)
            blink_rate = (self.total_blinks / self.frame_counter) * 30.0
        
        return {
            'total_blinks': self.total_blinks,
            'frame_count': self.frame_counter,
            'blink_rate_per_second': blink_rate,
            'has_movement': len(self.landmark_history) > 10,
            'tracking_duration_seconds': self.frame_counter / 30.0  # Approximation 30 fps
        }


# Instance globale (sera initialisée avec landmark_service)
liveness_service = None

def get_liveness_service(landmark_service: LandmarkService) -> LivenessService:
    """Factory function pour obtenir l'instance de LivenessService"""
    global liveness_service
    if liveness_service is None:
        liveness_service = LivenessService(landmark_service)
    return liveness_service

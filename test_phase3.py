"""
Script de test pour la Phase 3: Méthode Ensemble (InsightFace + DeepFace)
"""
import sys
import numpy as np
from unittest.mock import MagicMock, patch

# Ajouter le chemin backend
sys.path.append('backend')

# Mock DeepFace avant l'import du service si nécessaire
with patch.dict('sys.modules', {'deepface': MagicMock()}):
    from app.services.ensemble_service import ensemble_service
    from app.services.face_service import face_service

def test_ensemble_logic():
    print("=== Test EnsembleService Logic ===")
    
    # 1. Test Initialization
    mock_db = MagicMock()
    mock_employee = MagicMock()
    mock_employee.id = 1
    # Simuler une photo (bytes)
    mock_employee.photo1 = b'fake_image_bytes'
    mock_employee.photo2 = None
    
    mock_db.query.return_value.all.return_value = [mock_employee]
    
    # Mock cv2.imdecode to return a fake image
    with patch('cv2.imdecode', return_value=np.zeros((100, 100, 3), dtype=np.uint8)):
        # Mock DeepFace.represent
        with patch('deepface.DeepFace.represent') as mock_represent:
            mock_represent.return_value = [{"embedding": [0.1] * 512}]
            
            # Initialize
            ensemble_service.initialized = False # Force init
            ensemble_service.initialize(mock_db)
            
            print(f"Service Initialized: {ensemble_service.initialized}")
            print(f"Embeddings loaded: {len(ensemble_service.embeddings)}")
            
            if ensemble_service.initialized and 1 in ensemble_service.embeddings:
                print("✅ Initialization Successful")
            else:
                print("❌ Initialization Failed")

    # 2. Test Verification
    print("\n=== Test Verification Logic ===")
    
    # Cas 1: Match (Distance < Threshold)
    with patch('deepface.DeepFace.represent') as mock_represent:
        # Target embedding is same as stored (distance 0)
        mock_represent.return_value = [{"embedding": [0.1] * 512}]
        
        fake_face = np.zeros((100, 100, 3), dtype=np.uint8)
        is_verified, dist = ensemble_service.verify_identity(fake_face, 1)
        
        print(f"Test Match -> Verified: {is_verified}, Dist: {dist:.4f}")
        if is_verified:
            print("✅ Verification Logic (Match) Works")
        else:
            print("❌ Verification Logic (Match) Failed")

    # Cas 2: No Match (Distance > Threshold)
    with patch('deepface.DeepFace.represent') as mock_represent:
        # Target embedding is different (distance high)
        mock_represent.return_value = [{"embedding": [0.9] * 512}]
        
        is_verified, dist = ensemble_service.verify_identity(fake_face, 1)
        
        print(f"Test No Match -> Verified: {is_verified}, Dist: {dist:.4f}")
        if not is_verified:
            print("✅ Verification Logic (No Match) Works")
        else:
            print("❌ Verification Logic (No Match) Failed")

    # 3. Test FaceService Integration (Grey Zone)
    print("\n=== Test FaceService Integration (Grey Zone) ===")
    
    # Setup FaceService with known embeddings
    face_service.known_ids = [1]
    face_service.known_names = ["TestUser"]
    # Mock known embeddings (normalized)
    face_service.known_embeddings = np.array([[1.0, 0.0]]) 
    
    # Mock FaceAnalysis result
    mock_face = MagicMock()
    mock_face.bbox = [0, 0, 100, 100]
    mock_face.embedding = np.array([0.8, 0.6]) # Similarity ~0.8 (Grey Zone)
    mock_face.kps = np.zeros((5, 2))
    
    face_service.app.get = MagicMock(return_value=[mock_face])
    face_service.landmark_service.extract_landmarks_from_frame = MagicMock(return_value=np.zeros((468, 3)))
    face_service.liveness_service.calculate_liveness_score = MagicMock(return_value=0.9)
    face_service.calculate_adaptive_threshold = MagicMock(return_value=0.85) # Threshold 0.85
    
    # Mock EnsembleService verify_identity to return True
    face_service.ensemble_service.verify_identity = MagicMock(return_value=(True, 0.3))
    
    # Run recognition
    # Similarity is 0.8. Threshold is 0.85. 
    # 0.8 < 0.85 AND 0.8 > (0.85 - 0.10 = 0.75). So it IS in Grey Zone.
    
    results = face_service.recognize_faces(np.zeros((200, 200, 3), dtype=np.uint8))
    
    if results:
        name, _, conf, _, _, _ = results[0]
        print(f"Result Name: {name}, Confidence: {conf:.4f}")
        
        if name == "TestUser" and conf > 0.85:
            print("✅ Ensemble Rescue Successful (Confidence Boosted)")
        else:
            print(f"❌ Ensemble Rescue Failed (Name: {name}, Conf: {conf})")
    else:
        print("❌ No results returned")

if __name__ == "__main__":
    try:
        test_ensemble_logic()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")

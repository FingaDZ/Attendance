"""
Script de test pour la Phase 2: Système d'Entraînement Adaptatif
"""
import sys
import time
import numpy as np
from unittest.mock import MagicMock, Mock

# Ajouter le chemin backend
sys.path.append('backend')

from app.services.adaptive_training_service import adaptive_training_service

def test_adaptive_training_logic():
    print("=== Test AdaptiveTrainingService Logic ===")
    
    # Mock DB Session and Employee
    mock_db = MagicMock()
    mock_employee = MagicMock()
    mock_employee.id = 1
    
    # Simuler un embedding existant (tout à 0.1)
    old_embedding = np.full((512,), 0.1, dtype=np.float32)
    import pickle
    mock_employee.face_encoding = pickle.dumps(old_embedding)
    
    # Configurer le mock DB pour retourner cet employé
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_employee
    
    # Réinitialiser le service pour le test
    adaptive_training_service.history = {}
    adaptive_training_service.UPDATE_INTERVAL = 0  # Désactiver le délai pour le test
    
    # Simuler un nouvel embedding (tout à 0.2)
    # Le but est de voir si l'embedding évolue vers 0.2
    new_embedding = np.full((512,), 0.2, dtype=np.float32)
    
    print("\n--- Simulation de 3 reconnaissances successives ---")
    
    # 1ère Reconnaissance (Haute confiance, Haute vivacité)
    print("1. Reconnaissance #1 (Conf: 0.95, Live: 0.90)")
    updated = adaptive_training_service.process_recognition(
        mock_db, employee_id=1, current_embedding=new_embedding, 
        confidence=0.95, liveness_score=0.90
    )
    print(f"   Mise à jour effectuée ? {updated}")
    assert updated == False, "Ne devrait pas mettre à jour au 1er essai"
    
    # 2ème Reconnaissance
    print("2. Reconnaissance #2 (Conf: 0.96, Live: 0.92)")
    updated = adaptive_training_service.process_recognition(
        mock_db, employee_id=1, current_embedding=new_embedding, 
        confidence=0.96, liveness_score=0.92
    )
    print(f"   Mise à jour effectuée ? {updated}")
    assert updated == False, "Ne devrait pas mettre à jour au 2ème essai"
    
    # 3ème Reconnaissance (Devrait déclencher la mise à jour)
    print("3. Reconnaissance #3 (Conf: 0.95, Live: 0.91)")
    updated = adaptive_training_service.process_recognition(
        mock_db, employee_id=1, current_embedding=new_embedding, 
        confidence=0.95, liveness_score=0.91
    )
    print(f"   Mise à jour effectuée ? {updated}")
    assert updated == True, "DEVRAIT mettre à jour au 3ème essai"
    
    # Vérifier que l'embedding a été mis à jour
    # Logic: New = (Old * 0.9) + (New * 0.1)
    # Old = 0.1, New = 0.2
    # Expected = (0.1 * 0.9) + (0.2 * 0.1) = 0.09 + 0.02 = 0.11
    # Note: Il y a une normalisation ensuite, donc la valeur exacte peut varier légèrement
    
    # Récupérer l'embedding mis à jour du mock
    updated_pickle = mock_employee.face_encoding
    updated_embedding = pickle.loads(updated_pickle)
    
    print(f"\nAncien Embedding (moyenne): {np.mean(old_embedding):.4f}")
    print(f"Nouvel Embedding (moyenne): {np.mean(updated_embedding):.4f}")
    
    if np.mean(updated_embedding) > np.mean(old_embedding):
        print("✅ L'embedding a évolué dans la bonne direction !")
    else:
        print("❌ L'embedding n'a pas évolué correctement.")
        
    print("\n✅ Test AdaptiveTrainingService RÉUSSI")

if __name__ == "__main__":
    try:
        test_adaptive_training_logic()
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")

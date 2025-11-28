
import unittest
from unittest.mock import MagicMock
import numpy as np
import pickle
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.adaptive_training_service import AdaptiveTrainingService

class TestAdaptiveFix(unittest.TestCase):
    def test_update_profile(self):
        service = AdaptiveTrainingService()
        db = MagicMock()
        
        # Mock Employee
        employee = MagicMock()
        employee.id = 1
        
        # Create a dummy embedding (512 dim for insightface)
        emb = np.random.rand(512).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        emb_bytes = pickle.dumps(emb)
        
        # Set embeddings on employee
        employee.embedding1 = emb_bytes
        employee.embedding2 = None
        employee.embedding3 = None
        employee.embedding4 = None
        employee.embedding5 = None
        employee.embedding6 = None
        
        db.query.return_value.filter.return_value.first.return_value = employee
        
        # New embedding (close to original)
        new_emb = emb + np.random.normal(0, 0.01, 512).astype(np.float32)
        new_emb = new_emb / np.linalg.norm(new_emb)
        
        # Run update
        # We need to ensure the service can access the attributes
        # Since we are mocking, getattr(employee, 'embedding1') works if we set it.
        
        result = service._update_employee_profile(db, 1, new_emb)
        
        if not result:
            print("Update returned False")
            
        self.assertTrue(result)
        self.assertTrue(db.commit.called)
        
        print("Test passed: Embedding updated successfully")

if __name__ == '__main__':
    unittest.main()

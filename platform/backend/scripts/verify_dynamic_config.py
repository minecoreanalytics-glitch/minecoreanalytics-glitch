import sys
import os
from unittest.mock import MagicMock

# Add the backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# --- MOCKING SETUP ---

# 1. Mock External Dependencies
sys.modules["google"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.bigquery"] = MagicMock()
sys.modules["yaml"] = MagicMock()
sys.modules["pydantic"] = MagicMock()

# 2. Mock Entity Models with Real Classes
# typing.Optional[MagicMock] causes SyntaxError in Python 3.13
class Customer: pass
class Invoice: pass
class Contact: pass
class Interaction: pass

mock_entities = MagicMock()
mock_entities.Customer = Customer
mock_entities.Invoice = Invoice
mock_entities.Contact = Contact
mock_entities.Interaction = Interaction
sys.modules["core.models.entities"] = mock_entities
# Also mock relative import path if needed (though sys.path trick usually handles it)
sys.modules["backend.core.models.entities"] = mock_entities

# 3. Mock Configuration
mock_config = MagicMock()
mock_config.bigquery.project_id = "default-project"
mock_config.bigquery.dataset = "default-dataset"

def mock_get_entity(entity_name):
    if entity_name == "customer":
        entity = MagicMock()
        entity.table = "customers"
        return entity
    return None

mock_config.get_entity.side_effect = mock_get_entity

# 4. Mock Config Loader
mock_config_loader = MagicMock()
mock_config_loader.get_config.return_value = mock_config
sys.modules["core.config.config_loader"] = mock_config_loader

# --- IMPORT AFTER MOCKING ---
from core.engines.data_engine import DataEngine

def verify_dynamic_config():
    print("Starting DataEngine Configuration Verification (Isolated Mode)...")
    
    # Defaults from our mock
    default_project = "default-project"
    default_dataset = "default-dataset"
    
    print(f"Mock Default Config - Project: {default_project}, Dataset: {default_dataset}")
    
    # Test Case 1: Default Configuration (No Overrides)
    print("\nTest Case 1: Default Configuration")
    engine_default = DataEngine()
    
    try:
        table_name = engine_default._get_full_table_name("customer")
        expected_name = f"{default_project}.{default_dataset}.customers"
        
        if table_name == expected_name:
            print(f"✅ SUCCESS: Default table name matches: {table_name}")
        else:
            print(f"❌ FAILURE: Default table name mismatch.")
            print(f"   Expected: {expected_name}")
            print(f"   Actual:   {table_name}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Test Case 1 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test Case 2: With Overrides
    print("\nTest Case 2: With Overrides")
    override_project = "test-project-override"
    override_dataset = "test-dataset-override"
    
    engine_override = DataEngine(project_id=override_project, dataset_id=override_dataset)
    
    try:
        table_name = engine_override._get_full_table_name("customer")
        expected_name = f"{override_project}.{override_dataset}.customers"
        
        if table_name == expected_name:
            print(f"✅ SUCCESS: Overridden table name matches: {table_name}")
        else:
            print(f"❌ FAILURE: Overridden table name mismatch.")
            print(f"   Expected: {expected_name}")
            print(f"   Actual:   {table_name}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Test Case 2 failed with exception: {e}")
        return False

    # Test Case 3: Partial Override (Project only)
    print("\nTest Case 3: Partial Override (Project only)")
    engine_partial = DataEngine(project_id=override_project)
    
    try:
        table_name = engine_partial._get_full_table_name("customer")
        expected_name = f"{override_project}.{default_dataset}.customers"
        
        if table_name == expected_name:
            print(f"✅ SUCCESS: Partial override table name matches: {table_name}")
        else:
            print(f"❌ FAILURE: Partial override table name mismatch.")
            print(f"   Expected: {expected_name}")
            print(f"   Actual:   {table_name}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Test Case 3 failed with exception: {e}")
        return False

    print("\nAll verification tests passed!")
    return True

if __name__ == "__main__":
    success = verify_dynamic_config()
    sys.exit(0 if success else 1)
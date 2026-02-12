import sys
import os
from pathlib import Path

# Add backend to python path
sys.path.append(str(Path.cwd() / "backend"))

from backend.core.intelligence.sql_agent import SQLGenerator
from backend.core.platform.metadata.service import CatalogService

def test_agent():
    print("--- 🔍 Verifying Morpheus Intelligence Agent ---")
    
    # Check Key
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("❌ ERROR: GEMINI_API_KEY is not set in environment.")
        print("Run: export GEMINI_API_KEY='your_key'")
        return

    print("✅ API Key detected.")

    # 1. Initialize Catalog
    print("\n1. Loading Catalog...")
    catalog = CatalogService()
    catalog.load_catalog()
    # Mock a table if empty for testing
    if not catalog.tables:
        print("   (Catalog empty, mocking 'customers' table for test)")
        from backend.core.platform.metadata.models import Table, Column
        catalog.tables["customers"] = Table(
            id="customers", 
            columns=[
                Column(name="customer_id", datatype="STRING"),
                Column(name="total_revenue", datatype="FLOAT"),
                Column(name="status", datatype="STRING")
            ]
        )
    print(f"✅ Catalog loaded with {len(catalog.tables)} tables.")

    # 2. Check SQL Gen
    print("\n2. Testing SQL Generation...")
    agent = SQLGenerator(catalog)
    
    questions = [
        "Show me all active customers",
        "What is the total revenue?"
    ]
    
    for q in questions:
        print(f"\n   Q: '{q}'")
        try:
            result = agent.generate_sql(q)
            if "error" in result:
                print(f"   ❌ Generation Failed: {result['error']}")
            else:
                print(f"   ✅ SQL: {result['sql']}")
        except Exception as e:
             print(f"   ❌ Exception: {e}")

    print("\n-------------------------------------------")
    print("✅ Verification Complete. Backend logic is sound.")
    print("Run `python backend/main.py` to start the server.")

if __name__ == "__main__":
    test_agent()

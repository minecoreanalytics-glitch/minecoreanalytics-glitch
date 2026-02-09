#!/usr/bin/env python3
"""
Test OAuth BigQuery connection
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

from services.bigquery_service import BigQueryService

def test_oauth_connection():
    print("=" * 60)
    print("Testing BigQuery OAuth Connection")
    print("=" * 60)
    
    # Get environment variables
    project_id = os.getenv('GCP_PROJECT_ID')
    oauth_token = os.getenv('BIGQUERY_OAUTH_TOKEN')
    
    print(f"\n1. Environment Variables:")
    print(f"   Project ID: {project_id}")
    print(f"   OAuth Token: {'*' * 20}...{oauth_token[-10:] if oauth_token else 'NOT SET'}")
    
    if not project_id or not oauth_token:
        print("\n❌ ERROR: Missing environment variables!")
        print("   Please ensure .env file contains:")
        print("   - GCP_PROJECT_ID")
        print("   - BIGQUERY_OAUTH_TOKEN")
        return False
    
    # Initialize service
    print("\n2. Initializing BigQueryService...")
    bq_service = BigQueryService()
    
    # Test connection
    print("\n3. Testing connection...")
    if bq_service.is_connected():
        print(f"   ✓ Connected to project: {bq_service.project_id}")
        print(f"   ✓ Connection name: {bq_service.connection_name}")
    else:
        print("   ❌ Not connected - attempting manual connection...")
        success = bq_service.connect(
            project_id=project_id,
            oauth_token=oauth_token,
            connection_name="BigQuery OAuth Test"
        )
        if not success:
            print("   ❌ Manual connection failed!")
            return False
        print("   ✓ Manual connection successful!")
    
    # List datasets
    print("\n4. Listing datasets...")
    try:
        datasets = bq_service.list_datasets()
        print(f"   ✓ Found {len(datasets)} datasets:")
        for i, dataset in enumerate(datasets[:10], 1):
            print(f"      {i}. {dataset}")
        if len(datasets) > 10:
            print(f"      ... and {len(datasets) - 10} more")
    except Exception as e:
        print(f"   ❌ Error listing datasets: {e}")
        return False
    
    # Test a simple query
    print("\n5. Testing query execution...")
    try:
        # Use the first dataset if available
        if datasets:
            test_dataset = datasets[0]
            query = f"SELECT table_name FROM `{project_id}.{test_dataset}.INFORMATION_SCHEMA.TABLES` LIMIT 5"
            print(f"   Query: {query}")
            results = bq_service.execute_query(query, max_results=5)
            print(f"   ✓ Query executed successfully! Found {len(results)} tables:")
            for i, row in enumerate(results, 1):
                print(f"      {i}. {row.get('table_name', 'N/A')}")
        else:
            print("   ⚠ No datasets available to test query")
    except Exception as e:
        print(f"   ❌ Error executing query: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_oauth_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

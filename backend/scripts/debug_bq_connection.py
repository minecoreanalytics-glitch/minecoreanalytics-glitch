import os
import sys
import json
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import List, Dict, Any

def get_credentials():
    """Get credentials from command line arg, user input, or environment."""
    print("\n--- BigQuery Connection Debugger ---\n")
    
    # 0. Check command line args
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.isfile(arg_path):
            print(f"Using credentials from argument: {arg_path}")
            return None, arg_path
        else:
            print(f"Warning: Argument '{arg_path}' is not a valid file.")

    # 1. Try environment variable first
    env_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if env_creds:
        print(f"Found GOOGLE_APPLICATION_CREDENTIALS: {env_creds}")
        # Auto-use if no interactive input possible or just default to yes for debug
        return None, env_creds 

    # 2. Ask for JSON content or file path
    print("\nPlease provide your Service Account Credentials.")
    print("You can paste the path to the JSON file OR paste the JSON content directly.")
    try:
        user_input = input("Credentials (path or JSON): ").strip()
    except EOFError:
        print("Error: No input provided.")
        return None, None

    # Check if it's a file path
    if os.path.isfile(user_input):
        return None, user_input
    
    # Check if it's JSON content
    try:
        creds_dict = json.loads(user_input)
        return creds_dict, None
    except json.JSONDecodeError:
        print("Error: Input is neither a valid file path nor valid JSON.")
        return None, None

def check_permissions(client: bigquery.Client, project_id: str):
    """Check if we can list datasets (requires Viewer/Editor/Owner or BigQuery User)."""
    print(f"\nChecking permissions for project: {project_id}...")
    try:
        datasets = list(client.list_datasets())
        print(f"✅ Connection Successful! Found {len(datasets)} datasets.")
        return datasets
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return None

def check_schema(client: bigquery.Client, datasets: List[Any]):
    """Check for required tables based on standard Morpheus config."""
    # Standard tables expected by Phase 0
    REQUIRED_TABLES = ['customers', 'invoices', 'interactions']
    
    print("\nChecking for required tables...")
    
    found_tables = {}
    
    for dataset in datasets:
        dataset_id = dataset.dataset_id
        print(f"  Scanning dataset: {dataset_id}")
        
        try:
            tables = list(client.list_tables(dataset))
            table_ids = [t.table_id for t in tables]
            
            for required in REQUIRED_TABLES:
                if required in table_ids:
                    if required not in found_tables:
                        found_tables[required] = []
                    found_tables[required].append(dataset_id)
                    
        except Exception as e:
            print(f"  ⚠️ Could not scan dataset {dataset_id}: {e}")

    # Report results
    print("\n--- Schema Verification Results ---")
    all_found = True
    for table in REQUIRED_TABLES:
        if table in found_tables:
            locations = ", ".join(found_tables[table])
            print(f"✅ Table '{table}' found in: {locations}")
        else:
            print(f"❌ Table '{table}' NOT found in any accessible dataset.")
            all_found = False
            
    if not all_found:
        print("\n⚠️  WARNING: Missing tables will cause the application to crash or show empty data.")
        print("Please ensure your BigQuery dataset contains the required tables.")

def main():
    creds_dict, creds_path = get_credentials()
    
    if not creds_dict and not creds_path:
        print("Aborting: No valid credentials provided.")
        return

    try:
        if creds_dict:
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            project_id = creds_dict.get('project_id')
        else:
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            # Extract project ID from the file
            with open(creds_path, 'r') as f:
                data = json.load(f)
                project_id = data.get('project_id')

        if not project_id:
            print("Error: Could not determine Project ID from credentials.")
            return

        client = bigquery.Client(credentials=credentials, project=project_id)
        
        datasets = check_permissions(client, project_id)
        
        if datasets:
            check_schema(client, datasets)
            
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")

if __name__ == "__main__":
    main()

"""
Debug script to check the catalog state and understand the dataset lookup issue.
"""
import requests
import json

def check_catalog_state():
    """Check the current state of the catalog."""
    
    base_url = "http://localhost:8000/api/v1/platform"
    
    print("=" * 60)
    print("CHECKING CATALOG STATE")
    print("=" * 60)
    
    # 1. List all datasources
    print("\n1. Datasources:")
    print("-" * 60)
    response = requests.get(f"{base_url}/catalog/datasources")
    if response.status_code == 200:
        datasources = response.json()
        print(f"Found {len(datasources)} datasource(s):")
        for ds in datasources:
            print(f"  - ID: {ds['id']}")
            print(f"    Name: {ds['name']}")
            print(f"    Type: {ds['type']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    # 2. For each datasource, list datasets
    if response.status_code == 200 and datasources:
        print("\n2. Datasets per Datasource:")
        print("-" * 60)
        for ds in datasources:
            print(f"\nDatasource: {ds['id']}")
            ds_response = requests.get(f"{base_url}/catalog/{ds['id']}/datasets")
            if ds_response.status_code == 200:
                datasets = ds_response.json()
                print(f"  Found {len(datasets)} dataset(s):")
                for dataset in datasets:
                    print(f"    - ID: {dataset['id']}")
                    print(f"      Name: {dataset['name']}")
                    
                    # List tables in this dataset
                    tables_response = requests.get(f"{base_url}/catalog/{dataset['id']}/tables")
                    if tables_response.status_code == 200:
                        tables = tables_response.json()
                        print(f"      Tables: {len(tables)}")
                        for table in tables[:3]:  # Show first 3 tables
                            print(f"        - {table['name']}")
                        if len(tables) > 3:
                            print(f"        ... and {len(tables) - 3} more")
                    else:
                        print(f"      Error listing tables: {tables_response.status_code}")
            else:
                print(f"  Error: {ds_response.status_code} - {ds_response.text}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    
    # Check if billing_data_dataset exists
    target_dataset = "billing_data_dataset"
    print(f"\nLooking for dataset: '{target_dataset}'")
    
    if response.status_code == 200 and datasources:
        found = False
        for ds in datasources:
            ds_response = requests.get(f"{base_url}/catalog/{ds['id']}/datasets")
            if ds_response.status_code == 200:
                datasets = ds_response.json()
                for dataset in datasets:
                    if dataset['id'] == target_dataset or dataset['name'] == target_dataset:
                        found = True
                        print(f"✓ Found dataset!")
                        print(f"  Dataset ID: {dataset['id']}")
                        print(f"  Dataset Name: {dataset['name']}")
                        print(f"  Parent Datasource: {ds['id']}")
                        break
                if found:
                    break
        
        if not found:
            print(f"✗ Dataset '{target_dataset}' NOT FOUND in catalog")
            print("\nPossible issues:")
            print("1. Dataset was not scanned after connection")
            print("2. Dataset ID format mismatch")
            print("3. Catalog service not persisting datasets")

if __name__ == "__main__":
    check_catalog_state()
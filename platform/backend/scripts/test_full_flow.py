"""
Test script to verify the full flow: datasource -> scan -> graph build.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_full_flow():
    """Test the complete flow from datasource to graph build."""
    
    # Step 1: Check datasources
    print("1. Checking datasources...")
    response = requests.get(f"{BASE_URL}/api/v1/platform/catalog/datasources")
    if response.status_code != 200:
        print(f"❌ Failed to get datasources: {response.status_code}")
        return
    
    datasources = response.json()
    print(f"✓ Found {len(datasources)} datasource(s)")
    
    if not datasources:
        print("❌ No datasources found. Please connect a datasource first.")
        return
    
    source_id = datasources[0]["id"]
    print(f"  Source ID: {source_id}")
    print(f"  Source Name: {datasources[0]['name']}")
    print(f"  Source Type: {datasources[0]['type']}")
    
    # Step 2: Scan the datasource
    print(f"\n2. Scanning datasource: {source_id}")
    response = requests.post(f"{BASE_URL}/api/v1/platform/catalog/scan/{source_id}")
    if response.status_code != 200:
        print(f"❌ Failed to scan datasource: {response.status_code}")
        print(f"Error: {response.text}")
        return
    
    scan_result = response.json()
    print(f"✓ Scan completed successfully!")
    print(f"  - Datasets: {scan_result['stats']['datasets']}")
    print(f"  - Tables: {scan_result['stats']['tables']}")
    print(f"  - Columns: {scan_result['stats']['columns']}")
    
    # Step 3: Get datasets
    print(f"\n3. Getting datasets for source: {source_id}")
    response = requests.get(f"{BASE_URL}/api/v1/platform/catalog/{source_id}/datasets")
    if response.status_code != 200:
        print(f"❌ Failed to get datasets: {response.status_code}")
        return
    
    datasets = response.json()
    print(f"✓ Found {len(datasets)} dataset(s)")
    
    if not datasets:
        print("❌ No datasets found after scan.")
        return
    
    # Step 4: Build graph from first dataset
    dataset_id = datasets[0]["id"]
    print(f"\n4. Building graph from dataset: {dataset_id}")
    
    payload = {"dataset_id": dataset_id}
    response = requests.post(
        f"{BASE_URL}/api/v1/platform/graph/build-from-dataset",
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Graph built successfully!")
        print(f"  - Total nodes: {result['stats']['total_nodes']}")
        print(f"  - Total edges: {result['stats']['total_edges']}")
        print(f"  - Tables: {result['stats']['tables']}")
        print(f"  - Columns: {result['stats']['columns']}")
        print(f"  - Relationships: {result['stats']['relationships']}")
        print("\n✅ FULL FLOW TEST PASSED - All systems working!")
    else:
        print(f"❌ Graph build failed with status {response.status_code}")
        print(f"Error: {response.text}")
        print("\n❌ Test FAILED")

if __name__ == "__main__":
    test_full_flow()
"""
Test script to verify the graph build endpoint works correctly.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_graph_build():
    """Test the graph build from dataset endpoint."""
    
    # First, check if we have any datasources
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
    
    # Get datasets for the first datasource
    source_id = datasources[0]["id"]
    print(f"\n2. Getting datasets for source: {source_id}")
    response = requests.get(f"{BASE_URL}/api/v1/platform/catalog/{source_id}/datasets")
    if response.status_code != 200:
        print(f"❌ Failed to get datasets: {response.status_code}")
        return
    
    datasets = response.json()
    print(f"✓ Found {len(datasets)} dataset(s)")
    
    if not datasets:
        print("❌ No datasets found. Please scan the datasource first.")
        return
    
    # Try to build graph from the first dataset
    dataset_id = datasets[0]["id"]
    print(f"\n3. Building graph from dataset: {dataset_id}")
    
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
        print("\n✅ Test PASSED - Graph build endpoint is working!")
    else:
        print(f"❌ Graph build failed with status {response.status_code}")
        print(f"Error: {response.text}")
        print("\n❌ Test FAILED")

if __name__ == "__main__":
    test_graph_build()
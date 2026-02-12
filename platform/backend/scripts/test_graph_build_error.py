"""
Test script to trigger the graph build endpoint and capture the error.
"""
import requests
import json

def test_graph_build():
    """Test the graph build endpoint."""
    
    # The dataset_id from the logs
    dataset_id = "billing_data_dataset"
    
    url = "http://localhost:8000/api/v1/platform/graph/build-from-dataset"
    
    payload = {
        "dataset_id": dataset_id
    }
    
    print(f"Testing graph build for dataset: {dataset_id}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 60)
        
        if response.status_code == 200:
            print("✓ Success!")
            result = response.json()
            print(json.dumps(result, indent=2))
        else:
            print("✗ Error!")
            print(f"Response: {response.text}")
            
            # Try to parse as JSON
            try:
                error_detail = response.json()
                print(f"\nError Detail: {json.dumps(error_detail, indent=2)}")
            except:
                pass
                
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_graph_build()
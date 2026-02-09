#!/usr/bin/env python3
"""
Test script to trigger the graph build endpoint and see debug logs
"""
import requests
import json

def test_graph_build():
    """Test the graph build endpoint with the dataset ID from the error"""
    
    # The dataset ID that the frontend is sending (from the error log)
    dataset_id = "billing_data_dataset"
    
    url = "http://localhost:8000/api/v1/platform/graph/build-from-dataset"
    
    payload = {
        "dataset_id": dataset_id
    }
    
    print(f"Testing graph build with dataset_id: {dataset_id}")
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n" + "="*60 + "\n")
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response'):
            print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    test_graph_build()
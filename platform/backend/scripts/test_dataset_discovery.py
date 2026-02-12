#!/usr/bin/env python3
"""
Test script for BigQuery dataset discovery endpoints.
This script tests the new dataset and table listing functionality.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_datasets_endpoint():
    """Test the /integrations/bigquery/datasets endpoint"""
    print("\n" + "="*60)
    print("Testing Dataset Discovery Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/integrations/bigquery/datasets")
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Successfully retrieved datasets!")
            print(f"  Project ID: {data.get('projectId')}")
            print(f"  Dataset Count: {data.get('count')}")
            print(f"\n  Datasets:")
            for dataset in data.get('datasets', []):
                print(f"    - {dataset.get('datasetId')}")
                print(f"      Location: {dataset.get('location')}")
                print(f"      Created: {dataset.get('created')}")
                if dataset.get('description'):
                    print(f"      Description: {dataset.get('description')}")
            return True
        elif response.status_code == 400:
            print(f"\n⚠ BigQuery not connected")
            print(f"  Message: {response.json().get('detail')}")
            return False
        else:
            print(f"\n✗ Error: {response.json()}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to backend server")
        print("  Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

def test_tables_endpoint(dataset_id: str):
    """Test the /integrations/bigquery/datasets/{dataset_id}/tables endpoint"""
    print("\n" + "="*60)
    print(f"Testing Tables Endpoint for Dataset: {dataset_id}")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/integrations/bigquery/datasets/{dataset_id}/tables")
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Successfully retrieved tables!")
            print(f"  Dataset ID: {data.get('datasetId')}")
            print(f"  Project ID: {data.get('projectId')}")
            print(f"  Table Count: {data.get('count')}")
            print(f"\n  Tables:")
            for table in data.get('tables', []):
                print(f"    - {table.get('tableId')}")
                print(f"      Rows: {table.get('numRows'):,}")
                print(f"      Size: {table.get('numBytes') / (1024*1024):.2f} MB")
                print(f"      Type: {table.get('type')}")
                print(f"      Modified: {table.get('modifiedAt')}")
            return True
        elif response.status_code == 400:
            print(f"\n⚠ BigQuery not connected")
            print(f"  Message: {response.json().get('detail')}")
            return False
        else:
            print(f"\n✗ Error: {response.json()}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to backend server")
        print("  Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("BigQuery Dataset Discovery Test")
    print("="*60)
    print("\nThis script tests the new dataset discovery endpoints.")
    print("Make sure you have:")
    print("  1. Backend running on http://localhost:8000")
    print("  2. BigQuery connection established")
    
    # Test datasets endpoint
    datasets_success = test_datasets_endpoint()
    
    if datasets_success:
        # If datasets were retrieved, test tables endpoint with first dataset
        print("\n" + "="*60)
        print("Testing Tables Endpoint")
        print("="*60)
        
        # Get datasets again to extract first dataset ID
        try:
            response = requests.get(f"{BASE_URL}/integrations/bigquery/datasets")
            if response.status_code == 200:
                data = response.json()
                datasets = data.get('datasets', [])
                if datasets:
                    first_dataset = datasets[0].get('datasetId')
                    test_tables_endpoint(first_dataset)
                else:
                    print("\n⚠ No datasets found to test tables endpoint")
        except Exception as e:
            print(f"\n✗ Could not test tables endpoint: {e}")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    main()
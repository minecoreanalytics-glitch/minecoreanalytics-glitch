#!/usr/bin/env python3
"""
Test script to verify BigQuery connection persistence functionality.
This script tests:
1. Connection status endpoint
2. Connection persistence after restart
3. Connection restoration on startup
"""

import requests
import json
import sys
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"

def test_connection_status():
    """Test the connection status endpoint"""
    print("\n=== Testing Connection Status Endpoint ===")
    
    try:
        response = requests.get(f"{API_BASE}/integrations/connection-status")
        response.raise_for_status()
        
        status = response.json()
        print(f"✓ Connection Status Endpoint Working")
        print(f"  Connected: {status['connected']}")
        print(f"  Project ID: {status['project_id']}")
        print(f"  Connection Name: {status['connection_name']}")
        print(f"  Active Dataset: {status['active_dataset']}")
        
        return status
    except Exception as e:
        print(f"✗ Connection Status Endpoint Failed: {e}")
        return None

def check_persistence_file():
    """Check if the persistence file exists"""
    print("\n=== Checking Persistence File ===")
    
    config_file = Path(__file__).parent.parent / "data" / "active_connection.json"
    
    if config_file.exists():
        print(f"✓ Persistence file exists: {config_file}")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"  Project ID: {config.get('project_id')}")
            print(f"  Connection Name: {config.get('connection_name')}")
            print(f"  Active Dataset: {config.get('active_dataset')}")
            print(f"  Saved At: {config.get('saved_at')}")
            return True
        except Exception as e:
            print(f"✗ Could not read persistence file: {e}")
            return False
    else:
        print(f"ℹ No persistence file found (no connection has been made yet)")
        return False

def main():
    print("=" * 60)
    print("BigQuery Connection Persistence Test")
    print("=" * 60)
    
    # Test 1: Connection Status Endpoint
    status = test_connection_status()
    
    # Test 2: Check Persistence File
    has_persistence = check_persistence_file()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if status:
        print("✓ Connection status endpoint is working")
        if status['connected']:
            print("✓ BigQuery is currently connected")
            if has_persistence:
                print("✓ Connection is persisted to disk")
            else:
                print("⚠ Connection not persisted (this is unexpected)")
        else:
            print("ℹ No active BigQuery connection")
            print("  To test persistence:")
            print("  1. Connect to BigQuery via the DataNexus page")
            print("  2. Restart the backend server")
            print("  3. Run this test again to verify restoration")
    else:
        print("✗ Connection status endpoint failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
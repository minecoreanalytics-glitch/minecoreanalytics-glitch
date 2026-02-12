#!/usr/bin/env python3
"""
Verify that automatic catalog scanning is working after connection.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.platform.api import catalog_service

def verify_catalog():
    """Check if catalog has been populated."""
    print("\n=== Catalog State After Auto-Scan ===\n")
    
    # Check datasources
    datasources = catalog_service.list_datasources()
    print(f"Datasources: {len(datasources)}")
    for ds in datasources:
        print(f"  - {ds.id} ({ds.type}): {ds.name}")
    
    # Check datasets
    print(f"\nDatasets: {len(catalog_service.datasets)}")
    for ds_id, ds in catalog_service.datasets.items():
        print(f"  - {ds_id}")
    
    # Check tables
    print(f"\nTables: {len(catalog_service.tables)}")
    for table_id, table in list(catalog_service.tables.items())[:10]:  # Show first 10
        print(f"  - {table_id} ({table.num_rows} rows)")
    
    if len(catalog_service.tables) > 10:
        print(f"  ... and {len(catalog_service.tables) - 10} more tables")
    
    # Check columns
    print(f"\nColumns: {len(catalog_service.columns)}")
    
    # Summary
    print("\n=== Summary ===")
    if len(catalog_service.tables) > 0:
        print("✓ Catalog is populated - auto-scan is working!")
        return True
    else:
        print("✗ Catalog is empty - auto-scan may have failed")
        return False

if __name__ == "__main__":
    success = verify_catalog()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test script for the BigQuery → Knowledge Graph pipeline.
This script tests the complete flow from dataset to graph visualization.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from core.platform.metadata.service import CatalogService
from core.platform.metadata.models import DataSource
from core.platform.semantics.service import SemanticService
from core.platform.graph.builder import PlatformGraphBuilder

def load_active_connection():
    """Load the active BigQuery connection from saved config."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'active_connection.json')
    
    if not os.path.exists(config_path):
        return None
    
    with open(config_path, 'r') as f:
        return json.load(f)

def test_graph_pipeline():
    """Test the complete graph building pipeline."""
    
    print("=" * 80)
    print("Testing BigQuery → Knowledge Graph Pipeline")
    print("=" * 80)
    
    # Load active connection
    print("\n1. Loading active BigQuery connection...")
    connection_config = load_active_connection()
    
    if not connection_config:
        print("❌ No active connection found. Please connect to BigQuery first.")
        return False
    
    print(f"✓ Found connection: {connection_config.get('connection_name')}")
    print(f"   Project: {connection_config.get('project_id')}")
    print(f"   Active dataset: {connection_config.get('active_dataset')}")
    
    # Initialize services
    print("\n2. Initializing catalog service...")
    catalog = CatalogService()
    semantics = SemanticService()
    
    # Register the datasource
    print("\n3. Registering datasource...")
    datasource = DataSource(
        id=connection_config.get('connection_id', 'bigquery-default'),
        type='bigquery',
        name=connection_config.get('connection_name', 'BigQuery'),
        config={
            'project_id': connection_config['project_id'],
            'credentials': connection_config['credentials']
        }
    )
    
    if not catalog.register_datasource(datasource):
        print("❌ Failed to register datasource.")
        return False
    
    print("✓ Datasource registered")
    
    # Scan the datasource
    print("\n4. Scanning datasource...")
    try:
        stats = catalog.scan_source(datasource.id)
        print(f"✓ Scan complete: {stats['datasets']} datasets, {stats['tables']} tables, {stats['columns']} columns")
    except Exception as e:
        print(f"❌ Error scanning datasource: {e}")
        return False
    
    # Check for datasets
    print("\n5. Checking for datasets...")
    datasources = catalog.list_datasources()
    
    if not datasources:
        print("❌ No datasources found.")
        return False
    
    print(f"✓ Found {len(datasources)} datasource(s)")
    
    # Get the first datasource and its datasets
    datasource = datasources[0]
    print(f"   Using datasource: {datasource.name} ({datasource.id})")
    
    datasets = catalog.list_datasets(datasource.id)
    if not datasets:
        print("❌ No datasets found in datasource.")
        return False
    
    print(f"✓ Found {len(datasets)} dataset(s)")
    
    # Use the active dataset if specified, otherwise use first
    active_dataset_name = connection_config.get('active_dataset')
    dataset = None
    
    if active_dataset_name:
        for ds in datasets:
            if ds.name == active_dataset_name:
                dataset = ds
                break
    
    if not dataset:
        dataset = datasets[0]
    
    print(f"   Using dataset: {dataset.name} ({dataset.id})")
    
    # Get connector
    print("\n6. Getting connector...")
    connector = catalog._active_connectors.get(datasource.id)
    if not connector:
        print("❌ No connector found for datasource.")
        return False
    print("✓ Connector retrieved")
    
    # Create graph builder with connector
    print("\n7. Creating graph builder...")
    graph_builder = PlatformGraphBuilder(catalog, semantics, connector)
    print("✓ Graph builder created")
    
    # Detect relationships
    print("\n8. Detecting relationships...")
    try:
        relationships = graph_builder.detect_relationships(dataset.id)
        print(f"✓ Detected {len(relationships)} relationships")
        
        if relationships:
            print("\n   Sample relationships:")
            for i, rel in enumerate(relationships[:5], 1):
                print(f"   {i}. {rel.from_table_id}.{rel.from_column} → "
                      f"{rel.to_table_id}.{rel.to_column} "
                      f"(confidence: {rel.confidence:.2f}, method: {rel.detection_method})")
    except Exception as e:
        print(f"❌ Error detecting relationships: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Build the graph
    print("\n9. Building knowledge graph...")
    try:
        nodes, edges = graph_builder.build_data_graph(dataset.id)
        print(f"✓ Graph built successfully!")
        print(f"   - Total nodes: {len(nodes)}")
        print(f"   - Total edges: {len(edges)}")
        print(f"   - Tables: {len([n for n in nodes if n.type == 'table'])}")
        print(f"   - Columns: {len([n for n in nodes if n.type == 'column'])}")
        print(f"   - Relationships: {len([e for e in edges if e.type == 'RELATED_TO'])}")
        
        # Show sample nodes
        print("\n   Sample nodes:")
        for i, node in enumerate([n for n in nodes if n.type == 'table'][:3], 1):
            print(f"   {i}. {node.label} ({node.type})")
        
        # Show sample edges
        relationship_edges = [e for e in edges if e.type == 'RELATED_TO']
        if relationship_edges:
            print("\n   Sample relationship edges:")
            for i, edge in enumerate(relationship_edges[:3], 1):
                print(f"   {i}. {edge.from_id} → {edge.to_id}")
                if edge.properties:
                    print(f"      Confidence: {edge.properties.get('confidence', 'N/A')}")
                    print(f"      Method: {edge.properties.get('detection_method', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error building graph: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("✓ Pipeline test completed successfully!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_graph_pipeline()
    sys.exit(0 if success else 1)
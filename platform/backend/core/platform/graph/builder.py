from typing import List, Tuple, Optional
from ..metadata.service import CatalogService
from ..semantics.service import SemanticService
from ..connectors.base import BaseConnector
from .models import GraphNode, GraphEdge
from .relationship_detector import RelationshipDetector, DetectedRelationship
from .data_sampler import DataSampler

class PlatformGraphBuilder:
    """
    Constructs the Platform Graph by merging Technical Metadata and Semantic Definitions.
    This graph answers "What data do we have, and what does it mean?"
    """

    def __init__(
        self,
        catalog: CatalogService,
        semantics: SemanticService,
        connector: Optional[BaseConnector] = None
    ):
        self.catalog = catalog
        self.semantics = semantics
        self.connector = connector
        self.relationship_detector = RelationshipDetector()
        self.data_sampler = DataSampler(connector) if connector else None

    def build_graph(self) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """
        Builds the full platform graph.
        
        Returns:
            Tuple containing list of nodes and list of edges.
        """
        nodes = []
        edges = []
        
        # --- 1. Build Technical Graph (from Catalog) ---
        
        # Datasources
        for ds in self.catalog.list_datasources():
            nodes.append(GraphNode(id=ds.id, type="datasource", label=ds.name, properties=ds.model_dump()))
        
        # Datasets
        for source in self.catalog.list_datasources():
            for dataset in self.catalog.list_datasets(source.id):
                nodes.append(GraphNode(id=dataset.id, type="dataset", label=dataset.name, properties=dataset.model_dump()))
                edges.append(GraphEdge(
                    id=f"{source.id}->{dataset.id}",
                    from_id=source.id,
                    to_id=dataset.id,
                    type="HAS_DATASET"
                ))
                
                # Tables
                for table in self.catalog.list_tables(dataset.id):
                    nodes.append(GraphNode(id=table.id, type="table", label=table.name, properties=table.model_dump()))
                    edges.append(GraphEdge(
                        id=f"{dataset.id}->{table.id}",
                        from_id=dataset.id,
                        to_id=table.id,
                        type="HAS_TABLE"
                    ))
                    
                    # Columns
                    for col in self.catalog.list_columns(table.id):
                        nodes.append(GraphNode(id=col.id, type="column", label=col.name, properties=col.model_dump()))
                        edges.append(GraphEdge(
                            id=f"{table.id}->{col.id}",
                            from_id=table.id,
                            to_id=col.id,
                            type="HAS_COLUMN"
                        ))

        # --- 2. Build Semantic Graph (from Semantics) ---
        
        # Entities
        for entity in self.semantics.list_entities():
            entity_id = f"entity:{entity.name}"
            nodes.append(GraphNode(id=entity_id, type="entity", label=entity.label, properties=entity.model_dump()))
            
            # Attributes
            for attr in entity.attributes:
                attr_id = f"{entity_id}.{attr.name}"
                nodes.append(GraphNode(id=attr_id, type="attribute", label=attr.name, properties=attr.model_dump()))
                edges.append(GraphEdge(
                    id=f"{entity_id}->{attr_id}",
                    from_id=entity_id,
                    to_id=attr_id,
                    type="HAS_ATTRIBUTE"
                ))

        # --- 3. Link Semantics to Technical (Mappings) ---
        
        for mapping in self.semantics.mappings.values():
            entity_id = f"entity:{mapping.entity_name}"
            
            # Find the physical table ID
            # Assuming table ID construction matches CatalogService logic: f"{source}.{dataset}.{table}"
            physical_table_id = f"{mapping.datasource_id}.{mapping.dataset}.{mapping.table}"
            
            # Verify table exists in catalog (optional, but good for data integrity)
            if physical_table_id in self.catalog.tables:
                edges.append(GraphEdge(
                    id=f"{physical_table_id}->{entity_id}",
                    from_id=physical_table_id,
                    to_id=entity_id,
                    type="MAPS_TO_ENTITY"
                ))
            
            # Map attributes to columns
            for attr_name, col_name in mapping.attributes.items():
                attr_id = f"{entity_id}.{attr_name}"
                col_id = f"{physical_table_id}.{col_name}"
                
                if col_id in self.catalog.columns:
                     edges.append(GraphEdge(
                        id=f"{col_id}->{attr_id}",
                        from_id=col_id,
                        to_id=attr_id,
                        type="MAPS_TO_ATTRIBUTE"
                    ))

        return nodes, edges

    def build_data_graph(self, dataset_id: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """
        Build a knowledge graph from a BigQuery dataset by detecting relationships.
        
        This method:
        1. Fetches all tables and columns from the dataset
        2. Detects relationships using naming conventions and data types
        3. Creates nodes for tables and columns
        4. Creates edges for detected relationships
        
        Args:
            dataset_id: The dataset ID to build the graph from
            
        Returns:
            Tuple containing list of nodes and list of edges
        """
        nodes = []
        edges = []
        
        # Get all tables in the dataset
        tables = []
        columns_by_table = {}
        
        for table in self.catalog.list_tables(dataset_id):
            tables.append(table)
            
            # Create table node
            nodes.append(GraphNode(
                id=table.id,
                type="table",
                label=table.name,
                properties={
                    "name": table.name,
                    "dataset_id": table.dataset_id,
                    "num_rows": table.num_rows,
                    "type": table.type
                }
            ))
            
            # Get columns for this table
            columns = self.catalog.list_columns(table.id)
            columns_by_table[table.id] = columns
            
            # Create column nodes
            for col in columns:
                nodes.append(GraphNode(
                    id=col.id,
                    type="column",
                    label=col.name,
                    properties={
                        "name": col.name,
                        "datatype": col.datatype,
                        "is_nullable": col.is_nullable,
                        "is_primary_key": col.is_primary_key,
                        "is_foreign_key": col.is_foreign_key
                    }
                ))
                
                # Create edge from table to column
                edges.append(GraphEdge(
                    id=f"{table.id}->{col.id}",
                    from_id=table.id,
                    to_id=col.id,
                    type="HAS_COLUMN",
                    properties={}
                ))
        
        # Detect relationships between tables
        relationships = self.relationship_detector.detect_relationships(
            tables, columns_by_table
        )
        
        # Create edges for detected relationships
        for rel in relationships:
            edge_id = f"{rel.from_table_id}.{rel.from_column}->{rel.to_table_id}.{rel.to_column}"
            
            edges.append(GraphEdge(
                id=edge_id,
                from_id=rel.from_table_id,
                to_id=rel.to_table_id,
                type="RELATED_TO",
                properties={
                    "from_column": rel.from_column,
                    "to_column": rel.to_column,
                    "confidence": rel.confidence,
                    "detection_method": rel.detection_method,
                    "metadata": rel.metadata
                }
            ))
        
        return nodes, edges
    
    def detect_relationships(self, dataset_id: str) -> List[DetectedRelationship]:
        """
        Detect relationships in a dataset without building the full graph.
        
        Args:
            dataset_id: The dataset ID to analyze
            
        Returns:
            List of detected relationships
        """
        tables = []
        columns_by_table = {}
        
        for table in self.catalog.list_tables(dataset_id):
            tables.append(table)
            columns = self.catalog.list_columns(table.id)
            columns_by_table[table.id] = columns
        
        return self.relationship_detector.detect_relationships(tables, columns_by_table)
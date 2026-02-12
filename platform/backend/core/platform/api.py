from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import traceback
import logging

# Configure logging
logger = logging.getLogger(__name__)

from .metadata.service import CatalogService
from .metadata.models import DataSource, Dataset, Table, Column
from .semantics.service import SemanticService
from .semantics.models import EntityDefinition, EntityMapping
from .graph.builder import PlatformGraphBuilder
from .graph.models import GraphNode, GraphEdge

# Initialize Core Services (Singletons for now)
catalog_service = CatalogService()
semantic_service = SemanticService()  # Loads from backend/semantic/ by default
graph_builder = PlatformGraphBuilder(catalog_service, semantic_service)

# Load semantics on startup
semantic_service.load_definitions()

router = APIRouter(prefix="/api/v1/platform", tags=["Platform Core"])

# --- Catalog Endpoints ---

class ConnectSourceRequest(BaseModel):
    id: str
    type: str
    name: str
    config: Dict[str, Any]

@router.post("/catalog/connect")
async def connect_source(request: ConnectSourceRequest):
    """Register and connect a new data source."""
    datasource = DataSource(
        id=request.id,
        type=request.type,
        name=request.name,
        config=request.config
    )
    success = catalog_service.register_datasource(datasource)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to connect to data source")
    return {"status": "connected", "id": datasource.id}

@router.post("/catalog/scan/{source_id}")
async def scan_source(source_id: str):
    """Trigger a metadata scan for a connected source."""
    try:
        stats = catalog_service.scan_source(source_id)
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/catalog/datasources", response_model=List[DataSource])
async def list_datasources():
    return catalog_service.list_datasources()

@router.get("/catalog/{source_id}/datasets", response_model=List[Dataset])
async def list_datasets(source_id: str):
    return catalog_service.list_datasets(source_id)

@router.get("/catalog/{dataset_id}/tables", response_model=List[Table])
async def list_tables(dataset_id: str):
    return catalog_service.list_tables(dataset_id)

@router.get("/catalog/tables/{table_id}/columns", response_model=List[Column])
async def list_columns(table_id: str):
    return catalog_service.list_columns(table_id)

# --- Semantic Endpoints ---

@router.get("/semantic/entities", response_model=List[EntityDefinition])
async def list_entities():
    return semantic_service.list_entities()

@router.get("/semantic/mappings")
async def list_mappings():
    return semantic_service.mappings

# --- Graph Endpoints ---

@router.get("/graph/nodes", response_model=List[GraphNode])
async def get_graph_nodes():
    nodes, _ = graph_builder.build_graph()
    return nodes

@router.get("/graph/edges", response_model=List[GraphEdge])
async def get_graph_edges():
    _, edges = graph_builder.build_graph()
    return edges

@router.get("/graph/full")
async def get_full_graph():
    nodes, edges = graph_builder.build_graph()

class BuildDataGraphRequest(BaseModel):
    dataset_id: str

class DetectRelationshipsResponse(BaseModel):
    relationships: List[Dict[str, Any]]
    total_count: int

@router.post("/graph/build-from-dataset")
async def build_data_graph(request: BuildDataGraphRequest):
    """
    Build a knowledge graph from a BigQuery dataset by detecting relationships.
    
    This endpoint:
    1. Analyzes all tables and columns in the dataset
    2. Detects relationships using naming conventions
    3. Returns a graph with nodes (tables/columns) and edges (relationships)
    """
    try:
        logger.info(f"Building graph for dataset: {request.dataset_id}")
        
        # DEBUG: Log all available datasets in catalog
        logger.info("=== CATALOG DEBUG ===")
        for ds in catalog_service.list_datasources():
            logger.info(f"Datasource: {ds.id} ({ds.name})")
            datasets = catalog_service.list_datasets(ds.id)
            for dataset in datasets:
                logger.info(f"  - Dataset ID: {dataset.id}, Name: {dataset.name}")
        logger.info("=== END CATALOG DEBUG ===")
        
        # Get the connector from catalog service
        # We need to find the datasource that contains this dataset
        connector = None
        for ds in catalog_service.list_datasources():
            datasets = catalog_service.list_datasets(ds.id)
            logger.info(f"Checking datasource {ds.id} for dataset {request.dataset_id}")
            for dataset in datasets:
                logger.info(f"  Comparing: '{dataset.id}' == '{request.dataset_id}' ? {dataset.id == request.dataset_id}")
            if any(d.id == request.dataset_id for d in datasets):
                connector = catalog_service.connectors.get(ds.id)
                logger.info(f"Found connector for datasource: {ds.id}")
                break
        
        if not connector:
            logger.error(f"No connector found for dataset {request.dataset_id}")
            logger.error(f"Available dataset IDs: {[d.id for ds in catalog_service.list_datasources() for d in catalog_service.list_datasets(ds.id)]}")
            raise HTTPException(
                status_code=404,
                detail=f"No connector found for dataset {request.dataset_id}"
            )
        
        # Create a new graph builder with the connector
        logger.info("Creating graph builder with connector")
        data_graph_builder = PlatformGraphBuilder(
            catalog_service,
            semantic_service,
            connector
        )
        
        # Build the data graph
        logger.info("Building data graph...")
        nodes, edges = data_graph_builder.build_data_graph(request.dataset_id)
        logger.info(f"Graph built successfully: {len(nodes)} nodes, {len(edges)} edges")
        
        # Convert Pydantic models to dicts for JSON serialization
        nodes_dict = [n.model_dump() for n in nodes]
        edges_dict = [e.model_dump() for e in edges]
        
        return {
            "status": "success",
            "dataset_id": request.dataset_id,
            "nodes": nodes_dict,
            "edges": edges_dict,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "tables": len([n for n in nodes if n.type == "table"]),
                "columns": len([n for n in nodes if n.type == "column"]),
                "relationships": len([e for e in edges if e.type == "RELATED_TO"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building data graph: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error building graph: {str(e)}")

@router.get("/graph/detect-relationships/{dataset_id}")
async def detect_relationships(dataset_id: str):
    """
    Detect relationships in a dataset without building the full graph.
    
    Returns a list of detected relationships with confidence scores.
    """
    try:
        # Get the connector
        connector = None
        for ds in catalog_service.list_datasources():
            datasets = catalog_service.list_datasets(ds.id)
            if any(d.id == dataset_id for d in datasets):
                connector = catalog_service.connectors.get(ds.id)
                break
        
        if not connector:
            raise HTTPException(
                status_code=404,
                detail=f"No connector found for dataset {dataset_id}"
            )
        
        # Create graph builder with connector
        data_graph_builder = PlatformGraphBuilder(
            catalog_service,
            semantic_service,
            connector
        )
        
        # Detect relationships
        relationships = data_graph_builder.detect_relationships(dataset_id)
        
        return {
            "status": "success",
            "dataset_id": dataset_id,
            "relationships": [rel.to_dict() for rel in relationships],
            "total_count": len(relationships)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"nodes": nodes, "edges": edges}
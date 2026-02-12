from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
from datetime import datetime
from pathlib import Path
from services.bigquery_service import BigQueryService

# Import Core components
from core.config.config_loader import ConfigLoader
from core.engines.data_engine import get_data_engine

# Import Core Platform API
from core.platform.api import router as platform_router, catalog_service
from core.platform.metadata.models import DataSource

# Import Module routers
from modules.morpheus360.api import router as morpheus360_router
from modules.morpheus360 import graph_api

app = FastAPI(title="Morpheus Intelligence Platform API", version="2.0.0")

# CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:3001",
        "http://localhost:4173",
        "https://morpheus-frontend-78704783250.us-central1.run.app",
        "https://morpheus-backend-78704783250.us-central1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core on startup
@app.on_event("startup")
async def startup_event():
    """Initialize Morpheus Core on application startup."""
    try:
        # Load configuration
        config = ConfigLoader.load()
        print(f"✓ Morpheus Core initialized for: {config.company}")
        print(f"✓ BigQuery Project: {config.bigquery.project_id}")
        print(f"✓ Configured Entities: {', '.join(config.entities.keys())}")
    except Exception as e:
        print(f"⚠ Warning: Could not load Morpheus config: {e}")
        print("  System will run with limited functionality.")
    
    # If BigQuery connection was restored, register it with Platform API catalog
    if bq_service.is_connected():
        try:
            # Load the saved config to get credentials dict
            config_file = Path(__file__).parent / "data" / "active_connection.json"
            saved_config = {}
            if config_file.exists():
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
            
            datasource_id = bq_service.connection_id or "bigquery-main"
            datasource = DataSource(
                id=datasource_id,
                type="bigquery",
                name=bq_service.connection_name or "Google BigQuery",
                config={
                    "project_id": bq_service.project_id,
                    "credentials": saved_config.get("credentials", {}),
                    "dataset_id": bq_service.active_dataset
                }
            )
            
            # Register with catalog service
            catalog_registered = catalog_service.register_datasource(datasource)
            if catalog_registered:
                print(f"✓ Restored BigQuery connection registered with Platform API catalog (ID: {datasource_id})")
                
                # Automatically scan the datasource to populate catalog
                try:
                    scan_stats = catalog_service.scan_source(datasource_id)
                    print(f"✓ Catalog scan completed: {scan_stats['datasets']} datasets, {scan_stats['tables']} tables, {scan_stats['columns']} columns")
                except Exception as scan_error:
                    print(f"⚠ Warning: Catalog scan failed: {scan_error}")
            else:
                print(f"⚠ Warning: Could not register restored BigQuery connection with Platform API catalog")
        except Exception as e:
            print(f"⚠ Warning: Could not register restored connection with Platform API catalog: {e}")

# Mount Core Platform Router
app.include_router(platform_router)

# Mount module routers
app.include_router(morpheus360_router)
app.include_router(graph_api.router)

# Initialize BigQuery service (legacy - for integration endpoints)
bq_service = BigQueryService()

# Request/Response models
class BigQueryConnectionRequest(BaseModel):
    id: Optional[str] = None
    projectId: str
    datasetId: str
    credentials: Dict[str, Any]
    name: Optional[str] = "Google BigQuery"

class IntegrationStatus(BaseModel):
    id: str
    name: str
    type: str
    status: str
    lastSync: str
    latency: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

@app.get("/")
def read_root():
    return {
        "service": "Morpheus Intelligence Platform API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/api/v1/health")
def health_check():
    """Backend health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "bigquery": "ready" if bq_service.is_connected() else "disconnected"
        }
    }

@app.get("/api/v1/integrations/connection-status")
async def get_connection_status():
    """Get current BigQuery connection status"""
    try:
        status = bq_service.get_connection_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/integrations/bigquery/connect")
async def connect_bigquery(request: BigQueryConnectionRequest):
    """Connect to BigQuery with service account credentials"""
    try:
        success = bq_service.connect(
            project_id=request.projectId,
            credentials=request.credentials,
            connection_name=request.name,
            connection_id=request.id,
            dataset_id=request.datasetId
        )

        if success:
            # Initialize data engine with the connected BigQuery client
            try:
                data_engine = get_data_engine(
                    bq_client=bq_service.client,
                    project_id=request.projectId,
                    dataset_id=request.datasetId
                )
                print(f"✓ Data Engine initialized with BigQuery client (Project: {request.projectId}, Dataset: {request.datasetId})")
            except Exception as e:
                print(f"⚠ Warning: Could not initialize Data Engine: {e}")

            # Register connection with Platform API's catalog service
            try:
                datasource_id = request.id or "bigquery-main"
                datasource = DataSource(
                    id=datasource_id,
                    type="bigquery",
                    name=request.name or "Google BigQuery",
                    config={
                        "project_id": request.projectId,
                        "credentials": request.credentials,
                        "dataset_id": request.datasetId
                    }
                )
                
                # Register with catalog service
                catalog_registered = catalog_service.register_datasource(datasource)
                if catalog_registered:
                    print(f"✓ BigQuery connection registered with Platform API catalog (ID: {datasource_id})")
                    
                    # Automatically scan the datasource to populate catalog
                    try:
                        scan_stats = catalog_service.scan_source(datasource_id)
                        print(f"✓ Catalog scan completed: {scan_stats['datasets']} datasets, {scan_stats['tables']} tables, {scan_stats['columns']} columns")
                    except Exception as scan_error:
                        print(f"⚠ Warning: Catalog scan failed: {scan_error}")
                else:
                    print(f"⚠ Warning: Could not register BigQuery connection with Platform API catalog")
            except Exception as e:
                print(f"⚠ Warning: Could not register with Platform API catalog: {e}")

            return {
                "status": "connected",
                "projectId": request.projectId,
                "message": "Successfully connected to BigQuery"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to BigQuery")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/integrations/status")
async def get_integrations_status():
    """Get status of all integrations"""
    integrations = []

    # BigQuery status
    if bq_service.is_connected():
        try:
            datasets = bq_service.list_datasets()
            tables = []

            # Get tables from the first dataset
            if datasets:
                tables = bq_service.list_tables(datasets[0])

            integrations.append({
                "id": bq_service.connection_id or "bigquery-main",
                "name": bq_service.connection_name,
                "type": "bigquery",
                "status": "healthy",
                "lastSync": datetime.utcnow().isoformat(),
                "latency": 120,
                "metadata": {
                    "datasets": len(datasets),
                    "tables": tables,
                    "location": "US"
                }
            })
        except Exception as e:
            integrations.append({
                "id": "bigquery-main",
                "name": "Google BigQuery",
                "type": "bigquery",
                "status": "error",
                "lastSync": datetime.utcnow().isoformat(),
                "metadata": {"error": str(e)}
            })
    else:
        integrations.append({
            "id": bq_service.connection_id or "bigquery-main",
            "name": bq_service.connection_name or "Google BigQuery",
            "type": "bigquery",
            "status": "disconnected",
            "lastSync": None,
            "metadata": {}
        })

    return integrations

@app.get("/api/v1/integrations/bigquery/datasets")
async def list_datasets():
    """List all datasets in the connected BigQuery project"""
    if not bq_service.is_connected():
        raise HTTPException(status_code=400, detail="BigQuery not connected")

    try:
        dataset_ids = bq_service.list_datasets()
        
        # Get detailed information for each dataset
        datasets_info = []
        for dataset_id in dataset_ids:
            try:
                info = bq_service.get_dataset_info(dataset_id)
                datasets_info.append(info)
            except Exception as e:
                # If we can't get info for a dataset, still include it with basic info
                datasets_info.append({
                    "datasetId": dataset_id,
                    "projectId": bq_service.project_id,
                    "error": str(e)
                })
        
        return {
            "projectId": bq_service.project_id,
            "datasets": datasets_info,
            "count": len(datasets_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/integrations/bigquery/datasets/{dataset_id}/tables")
async def list_tables(dataset_id: str):
    """List all tables in a specific dataset"""
    if not bq_service.is_connected():
        raise HTTPException(status_code=400, detail="BigQuery not connected")

    try:
        tables = bq_service.list_tables(dataset_id)
        return {
            "datasetId": dataset_id,
            "projectId": bq_service.project_id,
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/integrations/bigquery/schema/{dataset_id}/{table_id}")
async def get_table_schema(dataset_id: str, table_id: str):
    """Get schema for a specific table"""
    if not bq_service.is_connected():
        raise HTTPException(status_code=400, detail="BigQuery not connected")

    try:
        schema = bq_service.get_table_schema(dataset_id, table_id)
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/integrations/bigquery/set-dataset")
async def set_active_dataset(request: Dict[str, str]):
    """Set the active dataset for queries"""
    if not bq_service.is_connected():
        raise HTTPException(status_code=400, detail="BigQuery not connected")

    dataset_id = request.get("datasetId")
    if not dataset_id:
        raise HTTPException(status_code=400, detail="datasetId is required")

    try:
        success = bq_service.set_active_dataset(dataset_id)
        if success:
            return {
                "status": "success",
                "activeDataset": dataset_id,
                "message": f"Active dataset set to {dataset_id}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to set active dataset")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/data/query")
async def execute_query(query: Dict[str, str]):
    """Execute a BigQuery SQL query"""
    if not bq_service.is_connected():
        raise HTTPException(status_code=400, detail="BigQuery not connected")

    try:
        sql = query.get("sql")
        if not sql:
            raise HTTPException(status_code=400, detail="SQL query is required")

        results = bq_service.execute_query(sql)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Customer 360 endpoint moved to Morpheus360 module
# See modules/morpheus360/api.py

@app.get("/api/v1/system/logs")
async def get_system_logs():
    """Get recent system logs"""
    # Return logs in the format expected by frontend
    # Frontend expects: id, source, event, time, status
    return {
        "logs": [
            {
                "id": 1,
                "source": "BigQuery Sync",
                "event": "Dataset synchronized",
                "time": "2m ago",
                "status": "success"
            },
            {
                "id": 2,
                "source": "API Gateway",
                "event": "Health check completed",
                "time": "5m ago",
                "status": "success"
            },
            {
                "id": 3,
                "source": "Data Pipeline",
                "event": "Processing batch jobs",
                "time": "8m ago",
                "status": "running"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

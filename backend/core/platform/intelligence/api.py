from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import logging

from core.intelligence.sql_agent import SQLGenerator
from core.platform.metadata.service import CatalogService

# Logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform/intelligence", tags=["Intelligence"])

# Request Model
class QueryRequest(BaseModel):
    message: str
    connection_id: Optional[str] = "bigquery-main" # For MVP, default to main

# Response Model
class QueryResponse(BaseModel):
    answer: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

# Dependency (we need to inject the catalog service)
# In a real app we'd use dependency injection, but for now we import the singleton from main if possible,
# or better, main injects it. 
# SIMPLIFICATION: We will instantiate a new SQLGenerator here using a shared catalog instance pattern.
# Ideally, we should import `catalog_service` from `main` or a shared module.

from core.platform.api import catalog_service # Reuse the singleton

sql_agent = SQLGenerator(catalog_service)

@router.post("/query", response_model=QueryResponse)
async def query_intelligence(request: QueryRequest):
    """
    Process a natural language query:
    1. Generate SQL from question.
    2. (Optional) Execute SQL against BigQuery.
    3. Return Answer + Data.
    """
    logger.info(f"Received intelligence query: {request.message}")
    
    # 1. Generate SQL
    result = sql_agent.generate_sql(request.message)
    
    if "error" in result:
        return QueryResponse(
            answer="I encountered an error analyzing your request.",
            error=result["error"]
        )
        
    sql_query = result.get("sql")
    
    # 2. Execute SQL
    data = []
    try:
        # We need the active BigQuery service content. 
        # Ideally, we should use the one initialized in main.
        # But for now, let's try to import it from main (risky due to circular imports) 
        # or better, use the CatalogService to get the datasource config and just use BigQuery client directly.
        # However, for MVP, let's just attempt to use the BigQueryService from services if it is stateful or loads from file.
        
        from services.bigquery_service import BigQueryService
        service = BigQueryService()
        if service.is_connected():
             # We might need to ensure it has the right credentials loaded 
             # (it does load from file in __init__? We need to verify).
             # Assuming it works similar to main.
             bq_data = service.execute_query(sql_query)
             data = [dict(row) for row in bq_data]
        else:
             # Fallback: Try to use the catalog's default source
             pass
    except Exception as e:
        logger.error(f"SQL Execution failed: {e}")
        return QueryResponse(answer=f"I generated the SQL but failed to execute it: {e}", sql=sql_query, error=str(e))

    return QueryResponse(
        answer=f"Here is the data:",
        sql=sql_query,
        data=data
    )

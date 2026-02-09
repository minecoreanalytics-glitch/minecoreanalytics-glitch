from typing import Dict, Any, List
from pydantic import BaseModel

class GraphNode(BaseModel):
    """Represents a node in the Platform Graph."""
    id: str
    type: str  # "datasource", "dataset", "table", "column", "entity", "attribute"
    label: str
    properties: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    """Represents a relationship in the Platform Graph."""
    id: str
    from_id: str
    to_id: str
    type: str  # "HAS_DATASET", "HAS_TABLE", "HAS_COLUMN", "MAPS_TO", "RELATED_TO"
    properties: Dict[str, Any] = {}
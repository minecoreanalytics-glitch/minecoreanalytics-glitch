from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field

class AttributeDefinition(BaseModel):
    """Defines a property of a business entity."""
    name: str
    type: str  # e.g., "string", "number", "boolean", "datetime"
    description: Optional[str] = None

class EntityDefinition(BaseModel):
    """Defines a business concept (e.g., 'Customer', 'Invoice')."""
    name: str
    label: str
    description: Optional[str] = None
    attributes: List[AttributeDefinition]

class RelationDefinition(BaseModel):
    """Defines a relationship between two entities."""
    name: str
    from_entity: str
    to_entity: str
    cardinality: str  # e.g., "1:1", "1:N", "N:N"
    description: Optional[str] = None

class EntityMapping(BaseModel):
    """Maps a semantic entity to a physical table."""
    entity_name: str
    datasource_id: str
    dataset: str
    table: str
    keys: List[str]  # Physical columns acting as primary keys
    attributes: Dict[str, str]  # Map: entity_attribute -> physical_column_name
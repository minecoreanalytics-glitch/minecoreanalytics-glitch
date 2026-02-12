"""
Pydantic schemas for Morpheus configuration.
These models validate and type the YAML configuration.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional


class EntityConfig(BaseModel):
    """Configuration for a single entity (table mapping)."""
    table: str
    id_field: Optional[str] = None
    name_field: Optional[str] = None
    foreign_keys: Optional[Dict[str, str]] = None
    fields: List[str]


class BigQueryConfig(BaseModel):
    """BigQuery connection configuration."""
    project_id: str
    dataset: str


class MorpheusConfig(BaseModel):
    """Root configuration for Morpheus platform."""
    company: str
    bigquery: BigQueryConfig
    entities: Dict[str, EntityConfig]

    def get_entity(self, entity_name: str) -> Optional[EntityConfig]:
        """Get entity config by name."""
        return self.entities.get(entity_name)

    def get_table_name(self, entity_name: str) -> Optional[str]:
        """Get the table name for an entity."""
        entity = self.get_entity(entity_name)
        return entity.table if entity else None

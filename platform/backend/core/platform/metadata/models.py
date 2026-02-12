from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DataSource(BaseModel):
    """Represents a connection to an external data system (e.g. BigQuery project)."""
    id: str
    type: str = Field(..., description="Connector type (e.g., 'bigquery', 'snowflake')")
    name: str
    config: Dict[str, Any] = Field(default_factory=dict, description="Connection configuration")
    description: Optional[str] = None

class Dataset(BaseModel):
    """Represents a logical grouping of tables (e.g. BigQuery Dataset, Postgres Schema)."""
    id: str
    name: str
    datasource_id: str
    description: Optional[str] = None

class Table(BaseModel):
    """Represents a physical table in the data source."""
    id: str
    name: str
    dataset_id: str
    datasource_id: str
    description: Optional[str] = None
    num_rows: Optional[int] = None
    type: str = "TABLE"

class Column(BaseModel):
    """Represents a column within a table."""
    id: str
    name: str
    table_id: str
    datatype: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: Optional[str] = None  # Format: "table_id.column_name"
    description: Optional[str] = None
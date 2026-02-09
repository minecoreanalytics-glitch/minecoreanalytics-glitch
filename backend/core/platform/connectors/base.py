from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class TableMetadata(BaseModel):
    """Metadata for a database table."""
    id: str
    name: str
    dataset_id: str
    num_rows: Optional[int] = None
    num_bytes: Optional[int] = None
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    type: str = "TABLE"

class ColumnMetadata(BaseModel):
    """Metadata for a table column."""
    name: str
    type: str
    is_nullable: bool = True
    description: Optional[str] = None

class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.
    Defines the standard interface for interacting with any database.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration.
        
        Args:
            config: Dictionary containing connection parameters (credentials, project_id, etc.)
        """
        self.config = config

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the data source.
        
        Returns:
            bool: True if connection initialized successfully
        """
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test if the connection is working.
        
        Returns:
            Dict containing 'connected' (bool) and optional diagnostic info.
        """
        pass

    @abstractmethod
    def list_datasets(self) -> List[str]:
        """
        List all datasets (or schemas) in the source.
        
        Returns:
            List of dataset IDs/names.
        """
        pass

    @abstractmethod
    def list_tables(self, dataset_id: str) -> List[TableMetadata]:
        """
        List all tables in a specific dataset.
        
        Args:
            dataset_id: The ID of the dataset/schema to scan.
            
        Returns:
            List of TableMetadata objects.
        """
        pass

    @abstractmethod
    def get_schema(self, dataset_id: str, table_id: str) -> List[ColumnMetadata]:
        """
        Get the schema (columns) for a specific table.
        
        Args:
            dataset_id: The dataset/schema ID.
            table_id: The table ID.
            
        Returns:
            List of ColumnMetadata objects.
        """
        pass

    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query against the source.
        
        Args:
            query: The SQL query string.
            
        Returns:
            List of rows (as dictionaries).
        """
        pass
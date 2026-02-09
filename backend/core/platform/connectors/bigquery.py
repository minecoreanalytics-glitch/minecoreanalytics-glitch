from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.credentials import Credentials
from datetime import datetime

from .base import BaseConnector, TableMetadata, ColumnMetadata

class OAuth2Credentials(Credentials):
    """Simple OAuth2 credentials wrapper for user tokens."""
    
    def __init__(self, token: str):
        super().__init__()
        self.token = token
        self._expiry = None
    
    def refresh(self, request):
        """OAuth tokens need to be refreshed externally."""
        pass
    
    def apply(self, headers, token=None):
        """Apply the token to the authentication header."""
        headers['authorization'] = f'Bearer {self.token}'
    
    def before_request(self, request, method, url, headers):
        """Apply credentials before making a request."""
        self.apply(headers)
    
    @property
    def expired(self):
        """Check if the token is expired."""
        return False
    
    @property
    def valid(self):
        """Check if credentials are valid."""
        return self.token is not None

class BigQueryConnector(BaseConnector):
    """
    BigQuery implementation of the BaseConnector.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client: Optional[bigquery.Client] = None
        self.project_id: Optional[str] = config.get("project_id")
        self._credentials_info = config.get("credentials")
        self._oauth_token = config.get("oauth_token")

    def connect(self) -> bool:
        """
        Connect to BigQuery using provided credentials (service account or OAuth token).
        """
        try:
            if self._oauth_token:
                # Use OAuth token for authentication
                credentials = OAuth2Credentials(self._oauth_token)
                self.client = bigquery.Client(
                    project=self.project_id,
                    credentials=credentials
                )
                print(f"Connected to BigQuery using OAuth token (Project: {self.project_id})")
            elif self._credentials_info:
                # Use service account credentials
                credentials = service_account.Credentials.from_service_account_info(
                    self._credentials_info,
                    scopes=["https://www.googleapis.com/auth/bigquery"]
                )
                self.client = bigquery.Client(
                    project=self.project_id,
                    credentials=credentials
                )
                print(f"Connected to BigQuery using service account (Project: {self.project_id})")
            else:
                # Fallback to default environment credentials
                self.client = bigquery.Client(project=self.project_id)
                print(f"Connected to BigQuery using default credentials (Project: {self.project_id})")
            
            return True
        except Exception as e:
            print(f"BigQuery connection failed: {e}")
            self.client = None
            return False

    def test_connection(self) -> Dict[str, Any]:
        if not self.client:
            return {"connected": False, "error": "Client not initialized"}
        
        try:
            # simple lightweight call
            list(self.client.list_datasets(max_results=1))
            return {
                "connected": True,
                "project_id": self.project_id
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    def list_datasets(self) -> List[str]:
        if not self.client:
            raise ConnectionError("Client not connected")
        
        datasets = list(self.client.list_datasets())
        return [d.dataset_id for d in datasets]

    def list_tables(self, dataset_id: str) -> List[TableMetadata]:
        if not self.client:
            raise ConnectionError("Client not connected")
            
        dataset_ref = self.client.dataset(dataset_id)
        tables_iter = self.client.list_tables(dataset_ref)
        
        result = []
        for table_item in tables_iter:
            # list_tables only returns summary info, for details like num_rows we need get_table
            # However, for performance, we might want to skip get_table for every single table 
            # if the list is huge. For Phase 0, let's do the full fetch to populate metadata.
            
            table_ref = dataset_ref.table(table_item.table_id)
            full_table = self.client.get_table(table_ref)
            
            result.append(TableMetadata(
                id=full_table.table_id,
                name=full_table.table_id,
                dataset_id=dataset_id,
                num_rows=full_table.num_rows,
                num_bytes=full_table.num_bytes,
                created_at=full_table.created.isoformat() if full_table.created else None,
                last_modified=full_table.modified.isoformat() if full_table.modified else None,
                type=full_table.table_type
            ))
            
        return result

    def get_schema(self, dataset_id: str, table_id: str) -> List[ColumnMetadata]:
        if not self.client:
            raise ConnectionError("Client not connected")
            
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = self.client.get_table(table_ref)
        
        columns = []
        for field in table.schema:
            columns.append(ColumnMetadata(
                name=field.name,
                type=field.field_type,
                is_nullable=field.is_nullable,
                description=field.description
            ))
            
        return columns

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if not self.client:
            raise ConnectionError("Client not connected")
            
        query_job = self.client.query(query)
        results = query_job.result()
        
        rows = []
        for row in results:
            # Convert Row object to dict and handle datetime serialization if needed
            row_dict = dict(row)
            # Basic serialization helper
            for k, v in row_dict.items():
                if isinstance(v, datetime):
                    row_dict[k] = v.isoformat()
            rows.append(row_dict)
            
        return rows
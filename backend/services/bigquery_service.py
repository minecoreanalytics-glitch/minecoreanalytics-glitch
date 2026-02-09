from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.credentials import Credentials
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path
from datetime import datetime

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

class BigQueryService:
    def __init__(self):
        self.client: Optional[bigquery.Client] = None
        self.project_id: Optional[str] = None
        self.connection_name: Optional[str] = "Google BigQuery"
        self.connection_id: Optional[str] = "bigquery-main"
        self.active_dataset: Optional[str] = None
        self.credentials = None
        self.config_file = Path(__file__).parent.parent / "data" / "active_connection.json"
        
        # Attempt to restore connection on initialization
        self._restore_connection()

    def connect(self, project_id: str, credentials: Dict[str, Any] = None, oauth_token: str = None, connection_name: str = "Google BigQuery", connection_id: str = "bigquery-main", dataset_id: Optional[str] = None) -> bool:
        """
        Connect to BigQuery using service account credentials or OAuth token

        Args:
            project_id: GCP project ID
            credentials: Service account JSON credentials as dict (optional)
            oauth_token: OAuth 2.0 access token (optional)
            connection_name: Display name for connection
            connection_id: Unique identifier for connection
            dataset_id: Default dataset ID

        Returns:
            bool: True if connection successful
        """
        try:
            # Load OAuth token from environment if not provided
            if not oauth_token and not credentials:
                oauth_token = os.getenv('BIGQUERY_OAUTH_TOKEN')
            
            if oauth_token:
                # Use OAuth token for authentication
                self.credentials = OAuth2Credentials(oauth_token)
                self.client = bigquery.Client(
                    project=project_id,
                    credentials=self.credentials
                )
                print(f"✓ Connected to BigQuery using OAuth token (Project: {project_id})")
                
            elif credentials:
                # Create credentials from service account info
                self.credentials = service_account.Credentials.from_service_account_info(
                    credentials,
                    scopes=["https://www.googleapis.com/auth/bigquery"]
                )
                self.client = bigquery.Client(
                    project=project_id,
                    credentials=self.credentials
                )
                print(f"✓ Connected to BigQuery using service account (Project: {project_id})")
            else:
                raise Exception("Either credentials or oauth_token must be provided")

            self.project_id = project_id
            self.connection_name = connection_name
            self.connection_id = connection_id
            self.active_dataset = dataset_id

            # Test connection by listing datasets
            list(self.client.list_datasets(max_results=1))
            
            # Persist connection configuration (only for service account)
            if credentials:
                self._save_connection_config(credentials)
            elif oauth_token:
                self._save_oauth_connection_config(oauth_token)

            return True

        except Exception as e:
            print(f"BigQuery connection error: {str(e)}")
            self.client = None
            self.project_id = None
            return False

    def is_connected(self) -> bool:
        """Check if BigQuery client is connected"""
        return self.client is not None

    def list_datasets(self) -> List[str]:
        """List all datasets in the project"""
        if not self.client:
            raise Exception("BigQuery client not connected")

        try:
            datasets = list(self.client.list_datasets())
            return [dataset.dataset_id for dataset in datasets]
        except Exception as e:
            raise Exception(f"Error listing datasets: {str(e)}")

    def list_tables(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        List all tables in a dataset with metadata

        Args:
            dataset_id: Dataset ID

        Returns:
            List of table metadata dictionaries
        """
        if not self.client:
            raise Exception("BigQuery client not connected")

        try:
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))

            table_info = []
            for table in tables:
                # Get full table info
                table_ref = dataset_ref.table(table.table_id)
                full_table = self.client.get_table(table_ref)

                table_info.append({
                    "tableId": table.table_id,
                    "numRows": full_table.num_rows,
                    "numBytes": full_table.num_bytes,
                    "createdAt": full_table.created.isoformat() if full_table.created else None,
                    "modifiedAt": full_table.modified.isoformat() if full_table.modified else None,
                    "type": full_table.table_type
                })

            return table_info

        except Exception as e:
            raise Exception(f"Error listing tables: {str(e)}")

    def get_table_schema(self, dataset_id: str, table_id: str) -> List[Dict[str, Any]]:
        """
        Get schema for a specific table

        Args:
            dataset_id: Dataset ID
            table_id: Table ID

        Returns:
            List of schema field dictionaries
        """
        if not self.client:
            raise Exception("BigQuery client not connected")

        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)

            schema = []
            for field in table.schema:
                schema.append({
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description or ""
                })

            return schema

        except Exception as e:
            raise Exception(f"Error getting table schema: {str(e)}")

    def execute_query(self, sql: str, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results

        Args:
            sql: SQL query string
            max_results: Maximum number of results to return

        Returns:
            List of result rows as dictionaries
        """
        if not self.client:
            raise Exception("BigQuery client not connected")

        try:
            query_job = self.client.query(sql)
            results = query_job.result(max_results=max_results)

            # Convert to list of dicts
            rows = []
            for row in results:
                row_dict = {}
                for key, value in row.items():
                    # Convert datetime objects to ISO format strings
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    else:
                        row_dict[key] = value
                rows.append(row_dict)

            return rows

        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    def get_customer_360(self, customer_id: str) -> Dict[str, Any]:
        """
        Get unified customer 360 view

        This is a template method - you'll need to customize the query
        based on your actual BigQuery schema

        Args:
            customer_id: Customer ID

        Returns:
            Customer 360 data dictionary
        """
        if not self.client:
            raise Exception("BigQuery client not connected")

        try:
            # Example query - customize based on your schema
            query = f"""
            SELECT
                customer_id,
                customer_name,
                total_revenue,
                account_status,
                created_date,
                last_interaction_date
            FROM `{self.project_id}.customers.customer_data`
            WHERE customer_id = @customer_id
            LIMIT 1
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)
                ]
            )

            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())

            if not results:
                return {
                    "customerId": customer_id,
                    "error": "Customer not found"
                }

            row = results[0]

            # Transform to expected format
            customer_data = {
                "customerId": row.get("customer_id"),
                "name": row.get("customer_name"),
                "billing": {
                    "totalRevenue": float(row.get("total_revenue", 0)),
                    "status": row.get("account_status", "active")
                },
                "service": {
                    "uptime": 99.5,  # Calculate from your data
                    "activeDevices": 0  # Calculate from your data
                },
                "score": {
                    "cns": 85.0,  # Calculate Client Net Score
                    "healthRisk": "low",
                    "churnProbability": 0.15
                },
                "lastUpdate": datetime.utcnow().isoformat()
            }

            return customer_data

        except Exception as e:
            # Return error but don't crash
            return {
                "customerId": customer_id,
                "error": str(e),
                "note": "Customize the get_customer_360 query based on your BigQuery schema"
            }

    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """Get detailed information about a dataset"""
        if not self.client:
            raise Exception("BigQuery client not connected")

        try:
            dataset = self.client.get_dataset(dataset_id)

            return {
                "datasetId": dataset.dataset_id,
                "projectId": dataset.project,
                "location": dataset.location,
                "created": dataset.created.isoformat() if dataset.created else None,
                "modified": dataset.modified.isoformat() if dataset.modified else None,
                "description": dataset.description or ""
            }

        except Exception as e:
            raise Exception(f"Error getting dataset info: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """Test the BigQuery connection and return diagnostics"""
        if not self.client:
            return {
                "connected": False,
                "error": "Client not initialized"
            }

        try:
            datasets = self.list_datasets()
            return {
                "connected": True,
                "projectId": self.project_id,
                "datasetsCount": len(datasets),
                "datasets": datasets[:5]  # First 5 datasets
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    def _save_connection_config(self, credentials: Dict[str, Any]) -> None:
        """
        Save connection configuration to disk for persistence across restarts.
        
        Args:
            credentials: Service account credentials dictionary
        """
        try:
            # Ensure data directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                "project_id": self.project_id,
                "connection_name": self.connection_name,
                "connection_id": self.connection_id,
                "active_dataset": self.active_dataset,
                "credentials": credentials,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ Connection config saved to {self.config_file}")
            
        except Exception as e:
            print(f"⚠ Warning: Could not save connection config: {e}")
    
    def _save_oauth_connection_config(self, oauth_token: str) -> None:
        """
        Save OAuth connection configuration to disk for persistence.
        
        Args:
            oauth_token: OAuth 2.0 access token
        """
        try:
            # Ensure data directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                "project_id": self.project_id,
                "connection_name": self.connection_name,
                "connection_id": self.connection_id,
                "active_dataset": self.active_dataset,
                "oauth_token": oauth_token,
                "auth_type": "oauth",
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ OAuth connection config saved to {self.config_file}")
            
        except Exception as e:
            print(f"⚠ Warning: Could not save connection config: {e}")
    
    def _restore_connection(self) -> bool:
        """
        Restore connection from saved configuration file.
        
        Returns:
            bool: True if connection was restored successfully
        """
        # First, try to connect using environment variables
        oauth_token = os.getenv('BIGQUERY_OAUTH_TOKEN')
        project_id = os.getenv('GCP_PROJECT_ID')
        
        if oauth_token and project_id:
            try:
                success = self.connect(
                    project_id=project_id,
                    oauth_token=oauth_token,
                    connection_name="Google BigQuery (OAuth)",
                    connection_id="bigquery-oauth"
                )
                if success:
                    print(f"✓ Connected using environment OAuth token: {project_id}")
                    return True
            except Exception as e:
                print(f"⚠ Could not connect using environment OAuth token: {e}")
        
        # Fall back to saved connection file
        if not self.config_file.exists():
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Check if it's an OAuth or service account connection
            auth_type = config.get("auth_type", "service_account")
            
            if auth_type == "oauth" and "oauth_token" in config:
                # Reconnect using saved OAuth token
                success = self.connect(
                    project_id=config["project_id"],
                    oauth_token=config["oauth_token"],
                    connection_name=config.get("connection_name", "Google BigQuery"),
                    connection_id=config.get("connection_id", "bigquery-main"),
                    dataset_id=config.get("active_dataset")
                )
            else:
                # Reconnect using saved service account credentials
                success = self.connect(
                    project_id=config["project_id"],
                    credentials=config["credentials"],
                    connection_name=config.get("connection_name", "Google BigQuery"),
                    connection_id=config.get("connection_id", "bigquery-main"),
                    dataset_id=config.get("active_dataset")
                )
            
            if success:
                print(f"✓ Restored BigQuery connection: {config['project_id']}")
                if self.active_dataset:
                    print(f"  Active dataset: {self.active_dataset}")
                return True
            else:
                print(f"⚠ Failed to restore BigQuery connection")
                return False
                
        except Exception as e:
            print(f"⚠ Could not restore connection: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status information.
        
        Returns:
            Dictionary with connection status details
        """
        return {
            "connected": self.is_connected(),
            "project_id": self.project_id,
            "connection_name": self.connection_name,
            "connection_id": self.connection_id,
            "active_dataset": self.active_dataset
        }
    
    def set_active_dataset(self, dataset_id: str) -> bool:
        """
        Set the active dataset for queries.
        
        Args:
            dataset_id: Dataset ID to set as active
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            return False
        
        try:
            # Verify dataset exists
            self.client.get_dataset(dataset_id)
            self.active_dataset = dataset_id
            
            # Update saved configuration
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                config['active_dataset'] = dataset_id
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"✓ Active dataset set to: {dataset_id}")
            
            return True
        except Exception as e:
            print(f"⚠ Failed to set active dataset: {e}")
            return False

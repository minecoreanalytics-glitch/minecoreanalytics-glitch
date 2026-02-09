"""
Data Engine - Core service for fetching data from BigQuery.
This is the main interface between the Morpheus Core and data sources.
"""

from typing import List, Optional, Dict, Any
from google.cloud import bigquery
from datetime import datetime

from ..config.config_loader import get_config
from ..models.entities import Customer, Invoice, Contact, Interaction


class DataEngine:
    """
    Core data engine for fetching entities from BigQuery.
    Uses configuration to map entity names to actual tables.
    """

    def __init__(self, bq_client: Optional[bigquery.Client] = None, project_id: Optional[str] = None, dataset_id: Optional[str] = None):
        """
        Initialize the data engine.

        Args:
            bq_client: Optional BigQuery client. If None, will create one from config.
            project_id: Optional override for project ID
            dataset_id: Optional override for dataset ID
        """
        self.config = get_config()
        self.bq_client = bq_client
        self.override_project_id = project_id
        self.override_dataset_id = dataset_id

        # Initialize client if not provided
        if self.bq_client is None:
            try:
                # Use override if available, otherwise config
                project = self.override_project_id or self.config.bigquery.project_id
                self.bq_client = bigquery.Client(
                    project=project
                )
            except Exception as e:
                print(f"Warning: Could not initialize BigQuery client: {e}")
                self.bq_client = None

    def _get_full_table_name(self, entity_name: str) -> str:
        """Get the fully qualified table name for an entity."""
        entity_config = self.config.get_entity(entity_name)
        if not entity_config:
            raise ValueError(f"Entity '{entity_name}' not found in configuration")

        project = self.override_project_id or self.config.bigquery.project_id
        dataset = self.override_dataset_id or self.config.bigquery.dataset
        return f"{project}.{dataset}.{entity_config.table}"

    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a BigQuery query and return results.

        Args:
            query: SQL query to execute

        Returns:
            List of row dictionaries

        Raises:
            Exception if query fails or client is not initialized
        """
        if self.bq_client is None:
            raise Exception("BigQuery client not initialized. Cannot fetch data.")

        try:
            query_job = self.bq_client.query(query)
            results = query_job.result()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Query execution error: {e}")
            raise

    def fetch_customer(self, customer_id: str) -> Optional[Customer]:
        """
        Fetch a single customer by ID.

        Args:
            customer_id: The customer ID to fetch

        Returns:
            Customer object or None if not found
        """
        try:
            table_name = self._get_full_table_name("customer")
            entity_config = self.config.get_entity("customer")

            query = f"""
                SELECT {', '.join(entity_config.fields)}
                FROM `{table_name}`
                WHERE {entity_config.id_field} = '{customer_id}'
                LIMIT 1
            """

            results = self._execute_query(query)
            if not results:
                return None

            return Customer(**results[0])

        except Exception as e:
            print(f"Error fetching customer {customer_id}: {e}")
            return None

    def fetch_customers(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """
        Fetch multiple customers with pagination.

        Args:
            limit: Maximum number of customers to fetch
            offset: Number of customers to skip

        Returns:
            List of Customer objects
        """
        try:
            table_name = self._get_full_table_name("customer")
            entity_config = self.config.get_entity("customer")

            query = f"""
                SELECT {', '.join(entity_config.fields)}
                FROM `{table_name}`
                LIMIT {limit}
                OFFSET {offset}
            """

            results = self._execute_query(query)
            return [Customer(**row) for row in results]

        except Exception as e:
            print(f"Error fetching customers: {e}")
            return []

    def fetch_invoices_for_customer(self, customer_id: str) -> List[Invoice]:
        """
        Fetch all invoices for a specific customer.

        Args:
            customer_id: The customer ID

        Returns:
            List of Invoice objects
        """
        try:
            table_name = self._get_full_table_name("invoice")
            entity_config = self.config.get_entity("invoice")

            query = f"""
                SELECT {', '.join(entity_config.fields)}
                FROM `{table_name}`
                WHERE customer_id = '{customer_id}'
                ORDER BY created_at DESC
            """

            results = self._execute_query(query)
            return [Invoice(**row) for row in results]

        except Exception as e:
            print(f"Error fetching invoices for customer {customer_id}: {e}")
            return []

    def fetch_contacts_for_customer(self, customer_id: str) -> List[Contact]:
        """
        Fetch all contacts for a specific customer.

        Args:
            customer_id: The customer ID

        Returns:
            List of Contact objects
        """
        try:
            table_name = self._get_full_table_name("contact")
            entity_config = self.config.get_entity("contact")

            query = f"""
                SELECT {', '.join(entity_config.fields)}
                FROM `{table_name}`
                WHERE customer_id = '{customer_id}'
                ORDER BY created_at DESC
            """

            results = self._execute_query(query)
            return [Contact(**row) for row in results]

        except Exception as e:
            print(f"Error fetching contacts for customer {customer_id}: {e}")
            return []

    def fetch_interactions_for_customer(self, customer_id: str, limit: int = 50) -> List[Interaction]:
        """
        Fetch recent interactions for a specific customer.

        Args:
            customer_id: The customer ID
            limit: Maximum number of interactions to fetch

        Returns:
            List of Interaction objects
        """
        try:
            table_name = self._get_full_table_name("interaction")
            entity_config = self.config.get_entity("interaction")

            query = f"""
                SELECT {', '.join(entity_config.fields)}
                FROM `{table_name}`
                WHERE customer_id = '{customer_id}'
                ORDER BY created_at DESC
                LIMIT {limit}
            """

            results = self._execute_query(query)
            return [Interaction(**row) for row in results]

        except Exception as e:
            print(f"Error fetching interactions for customer {customer_id}: {e}")
            return []


# Global instance (will be initialized on first use)
_data_engine_instance: Optional[DataEngine] = None


def get_data_engine(bq_client: Optional[bigquery.Client] = None, project_id: Optional[str] = None, dataset_id: Optional[str] = None) -> DataEngine:
    """
    Get the global DataEngine instance.

    Args:
        bq_client: Optional BigQuery client
        project_id: Optional override for project ID
        dataset_id: Optional override for dataset ID

    Returns:
        DataEngine instance
    """
    global _data_engine_instance
    if _data_engine_instance is None or bq_client is not None or project_id is not None or dataset_id is not None:
        _data_engine_instance = DataEngine(bq_client, project_id, dataset_id)
    return _data_engine_instance

from typing import Dict, List, Optional, Any
import json
import os
from .models import DataSource, Dataset, Table, Column
from ..connectors.base import BaseConnector
from ..connectors.bigquery import BigQueryConnector

class CatalogService:
    """
    Central service for managing technical metadata.
    Coordinates between Connectors and the Metadata Store (in-memory for Phase 0).
    """

    def __init__(self):
        # In-memory storage for Phase 0
        self.datasources: Dict[str, DataSource] = {}
        self.datasets: Dict[str, Dataset] = {}
        self.tables: Dict[str, Table] = {}
        self.columns: Dict[str, Column] = {}
        
        # Registry of active connectors
        self._active_connectors: Dict[str, BaseConnector] = {}

    @property
    def connectors(self) -> Dict[str, BaseConnector]:
        """Public accessor for active connectors."""
        return self._active_connectors

    def register_datasource(self, datasource: DataSource) -> bool:
        """
        Register a new data source and initialize its connector.
        """
        self.datasources[datasource.id] = datasource
        
        # Initialize connector based on type
        connector = None
        if datasource.type == "bigquery":
            connector = BigQueryConnector(datasource.config)
        
        if connector:
            if connector.connect():
                self._active_connectors[datasource.id] = connector
                return True
        
        return False

    def scan_source(self, source_id: str) -> Dict[str, int]:
        """
        Scan a registered data source and populate the catalog.
        
        Returns:
            Dict with stats on what was scanned (datasets, tables, columns count).
        """
        if source_id not in self.datasources:
            raise ValueError(f"Source {source_id} not registered")
            
        connector = self._active_connectors.get(source_id)
        if not connector:
            raise ConnectionError(f"Connector for {source_id} not initialized")

        stats = {"datasets": 0, "tables": 0, "columns": 0}

        # 1. List Datasets
        dataset_ids = connector.list_datasets()
        stats["datasets"] = len(dataset_ids)
        
        for ds_id in dataset_ids:
            dataset_obj = Dataset(
                id=f"{source_id}.{ds_id}",
                name=ds_id,
                datasource_id=source_id
            )
            self.datasets[dataset_obj.id] = dataset_obj

            # 2. List Tables
            tables_meta = connector.list_tables(ds_id)
            stats["tables"] += len(tables_meta)
            
            for table_meta in tables_meta:
                table_obj = Table(
                    id=f"{source_id}.{ds_id}.{table_meta.name}",
                    name=table_meta.name,
                    dataset_id=dataset_obj.id,
                    datasource_id=source_id,
                    num_rows=table_meta.num_rows,
                    type=table_meta.type
                )
                self.tables[table_obj.id] = table_obj

                # 3. Get Columns
                columns_meta = connector.get_schema(ds_id, table_meta.name)
                stats["columns"] += len(columns_meta)
                
                for col_meta in columns_meta:
                    col_obj = Column(
                        id=f"{table_obj.id}.{col_meta.name}",
                        name=col_meta.name,
                        table_id=table_obj.id,
                        datatype=col_meta.type,
                        is_nullable=col_meta.is_nullable,
                        description=col_meta.description
                    )
                    self.columns[col_obj.id] = col_obj

        return stats

    def get_datasource(self, source_id: str) -> Optional[DataSource]:
        return self.datasources.get(source_id)

    def save_catalog(self):
        """Persist catalog to disk."""
        try:
            data = {
                "datasources": [d.model_dump() for d in self.datasources.values()],
                "datasets": [d.model_dump() for d in self.datasets.values()],
                "tables": [t.model_dump() for t in self.tables.values()],
                "columns": [c.model_dump() for c in self.columns.values()]
            }
            with open("catalog_store.json", "w") as f:
                json.dump(data, f, indent=2)
            print("Catalog saved to catalog_store.json")
        except Exception as e:
            print(f"Failed to save catalog: {e}")

    def load_catalog(self):
        """Load catalog from disk."""
        if not os.path.exists("catalog_store.json"):
            print("No catalog store found. Starting empty.")
            return

        try:
            with open("catalog_store.json", "r") as f:
                data = json.load(f)

            # Restore objects
            for ds_data in data.get("datasources", []):
                ds = DataSource(**ds_data)
                self.datasources[ds.id] = ds
                # Re-initialize connector
                self.register_datasource(ds)

            for d_data in data.get("datasets", []):
                d = Dataset(**d_data)
                self.datasets[d.id] = d
            
            for t_data in data.get("tables", []):
                t = Table(**t_data)
                self.tables[t.id] = t
            
            for c_data in data.get("columns", []):
                c = Column(**c_data)
                self.columns[c.id] = c
                
            print(f"Catalog loaded: {len(self.datasources)} sources, {len(self.datasets)} datasets")
        except Exception as e:
            print(f"Failed to load catalog: {e}")

    def auto_discover(self):
        """Auto-discover environments connections (e.g. ADC)."""
        # If no BigQuery source exists, try to add one from env
        bq_sources = [ds for ds in self.datasources.values() if ds.type == "bigquery"]
        if not bq_sources:
             # Check if we have ADC or credentials
             # For MVP, just try to add a default one and see if it connects
             print("Auto-discovering Data Sources...")
             project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "looker-studio-htv")
             
             default_bq = DataSource(
                 id="bq-default",
                 type="bigquery",
                 name="Default BigQuery",
                 config={"project_id": project_id}
             )
             
             if self.register_datasource(default_bq):
                 print(f"Auto-connected to BigQuery project: {project_id}")
                 self.save_catalog()
             else:
                 print("Could not auto-connect to BigQuery (no credentials found?)")

    def list_datasources(self) -> List[DataSource]:
        return list(self.datasources.values())

    def list_datasets(self, source_id: str) -> List[Dataset]:
        return [d for d in self.datasets.values() if d.datasource_id == source_id]

    def list_tables(self, dataset_id: str) -> List[Table]:
        return [t for t in self.tables.values() if t.dataset_id == dataset_id]

    def list_columns(self, table_id: str) -> List[Column]:
        return [c for c in self.columns.values() if c.table_id == table_id]
# Phase 0: Morpheus Core Foundations Architecture

## Overview
This document outlines the architectural shift from a "Customer 360 App" to a "Universal Data Intelligence Platform". The goal is to build the foundational layers that allow Morpheus to connect to any data source, map it, and understand it, *before* building specific applications like 360 views or Action Engines.

## Core Components

### 1. Data Source Abstraction Layer (`backend/core/platform/connectors`)
**Purpose:** Decouple the platform from specific database technologies.

*   **`BaseConnector` (Abstract Class):**
    *   `connect(config: dict) -> bool`: Establish connection.
    *   `test_connection() -> dict`: Verify connectivity.
    *   `list_datasets() -> List[str]`: Discover schemas/datasets.
    *   `list_tables(dataset: str) -> List[TableMetadata]`: Discover tables.
    *   `get_schema(dataset: str, table: str) -> List[ColumnMetadata]`: Get column details.
    *   `execute_query(query: str) -> List[dict]`: Run raw SQL.

*   **`BigQueryConnector`:** Implementation for Google BigQuery.
*   **`SnowflakeConnector`:** (Stub) Implementation for Snowflake.
*   **`PostgresConnector`:** (Stub) Implementation for PostgreSQL.

### 2. Metadata Catalog Layer (`backend/core/platform/metadata`)
**Purpose:** The system of record for technical metadata. It knows *where* data lives and *what* it looks like.

*   **Models:**
    *   `DataSource`: Represents a connection (e.g., "Prod BigQuery").
    *   `Dataset`: Logical grouping (e.g., "finance_data").
    *   `Table`: Physical table definition.
    *   `Column`: Field definition (name, type, is_nullable, is_pk, etc.).
*   **`CatalogService`:**
    *   `scan_source(source_id: str)`: Crawls a connector and populates the catalog.
    *   `get_table_info(table_id: str)`: Returns technical details.
    *   `infer_relationships()`: (Future) Heuristic-based FK detection.

### 3. Semantic Layer (`backend/core/platform/semantics`)
**Purpose:** The business logic layer. It maps "Business Concepts" to "Technical Metadata".

*   **Models:**
    *   `EntityDefinition`: Abstract concept (e.g., "Customer", "Invoice").
    *   `Attribute`: Property of an entity (e.g., "Customer Name").
    *   `Relation`: Link between entities (e.g., "Customer HAS_MANY Invoices").
    *   `Mapping`: Connects an `EntityDefinition` to a `Table` in the Catalog.

## Directory Structure
```
backend/
├── core/
│   ├── platform/           # <-- NEW CORE
│   │   ├── connectors/     # Data Source Adapters
│   │   ├── metadata/       # Technical Catalog
│   │   ├── semantics/      # Business Logic / Ontology
│   │   └── graph/          # Knowledge Graph Builder
│   ├── engines/            # Processing (Query, Scoring)
│   └── models/             # Legacy Models (Refactor later)
```

## Migration Strategy
1.  Build the `connectors` and `metadata` layers first.
2.  Prove they work by scanning the existing BigQuery environment.
3.  Refactor `DataEngine` to use the new `CatalogService` instead of hardcoded config lookups.
4.  Deprecate the old `BigQueryService` and `htv_config.yaml` entity mappings in favor of the Semantic Layer.
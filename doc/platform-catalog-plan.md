# Phase 0 – `/platform/catalog` Implementation Plan

## 1. Objectives & Scope
- Expose read-only catalog APIs under `/api/v1/platform/catalog/*` that mirror the contract defined in the Phase 0 specification.
- Treat OpenMetadata as the single source of truth for datasources, datasets, tables, columns, and lineage; Morpheus only normalizes identifiers and response shapes.
- Keep the implementation pluggable so a future catalog provider can swap in via the same adapter interface.
- Provide fast responses for UI modules (e.g., Morpheus360) via Redis caching without duplicating catalog data permanently in Postgres.

## 2. Component Layout
1. **Catalog API Router (`/platform/catalog`)**  
   - FastAPI router exposing the six endpoints described in the spec.  
   - Depends on a `CatalogService` interface that hides OpenMetadata details.

2. **OpenMetadata Adapter Layer**  
   - Responsible for translating Morpheus requests into OpenMetadata REST calls and back into normalized DTOs.  
   - Handles authentication, pagination, query parameter translation, and error normalization.

3. **Cache Layer (Redis)**  
   - Provides short-lived caches for list-oriented endpoints (`datasources`, `datasets`, `tables`, `columns`).  
   - Each cache entry stores the JSON payload plus a checksum/version to detect invalidation events.

4. **Configuration & Secrets**  
   - Adapter pulls its base URL, API token, timeout, and paging defaults from `settings.catalog` (to be added in the config loader).  
   - No secrets are hardcoded; tokens are read from environment variables/secret store.

## 3. OpenMetadata Adapter Interface

### 3.1 Interface Definition
Logical interface (no code yet):

- `list_datasources(*, type: str | None = None) -> list[DatasourceSummary]`
- `list_datasets(datasource_id: str) -> list[DatasetSummary]`
- `list_tables(dataset_id: str, *, table_type: str | None = None, search: str | None = None) -> list[TableSummary]`
- `get_table(table_id: str) -> TableDetail`
- `list_columns(table_id: str) -> list[ColumnSummary]`
- `search(q: str, *, type_filter: str | None = None, limit: int = 25) -> list[CatalogSearchHit]`
- `get_lineage(table_id: str, direction: Literal["upstream","downstream","both"], depth: int) -> LineageGraph` *(needed later by `/platform/graph` but provided here for reuse).*

### 3.2 Data Transfer Objects
- `DatasourceSummary`: `{id, name, type, connectorId, description, location, tags}`  
- `DatasetSummary`: `{id, name, datasourceId, qualifiedName, description, tableCount, lastProfiledAt}`  
- `TableSummary`: `{id, name, datasetId, datasourceId, type, rows, columns, owner}`  
- `TableDetail`: `TableSummary + {description, columns: [ColumnDetail], serviceFullyQualifiedName, lineage (optional)}`  
- `ColumnSummary`: `{id, name, datatype, description, isNullable, isPrimaryKey, tags}`  
- `CatalogSearchHit`: `{id, type, name, displayName, datasourceId?, datasetId?, path, relevance}`  
- `LineageGraph`: `nodes[], edges[]` in a thin structure that the Graph builder can consume.

DTOs reference existing Pydantic models where possible (e.g., `[DataSource](backend/core/platform/metadata/models.py:4)`), but adapter-specific DTOs live under `backend/core/platform/catalog/dto.py` to avoid tight coupling.

### 3.3 Error Model
- All adapter methods raise `CatalogAdapterError` with `kind` (`auth`, `not_found`, `timeout`, `upstream`) and `details`.  
- API layer maps these to HTTP responses (401/404/504/502).  
- Errors include OpenMetadata request identifiers (if provided) to aid support.

## 4. FastAPI Endpoint Contracts

| Endpoint | Purpose | Request | Response | Cache Key | Source |
|----------|---------|---------|----------|-----------|--------|
| `GET /api/v1/platform/catalog/datasources` | List datasources | Query: `type?`, `status?` (future) | `{ items: [DatasourceSummary], page?, pageSize?, total? }` | `catalog:datasources` | OpenMetadata services |
| `GET /api/v1/platform/catalog/datasources/{datasourceId}/datasets` | List datasets for a datasource | Path `datasourceId` (Morpheus ID) | `{ items: [DatasetSummary] }` | `catalog:datasets:{datasourceId}` | OpenMetadata databases |
| `GET /api/v1/platform/catalog/datasets/{datasetId}/tables` | List tables/views in dataset | Query: `type?`, `search?` | `{ items: [TableSummary] }` | `catalog:tables:{datasetId}:{type}:{searchHash}` | OpenMetadata tables endpoint |
| `GET /api/v1/platform/catalog/tables/{tableId}` | Table details w/ columns & lineage stub | Path `tableId` | `TableDetail` | none (always fresh to show latest lineage) | OpenMetadata table + lineage |
| `GET /api/v1/platform/catalog/tables/{tableId}/columns` | Light column list | Path `tableId`; Query `includeTags? bool` | `{ items: [ColumnSummary] }` | `catalog:columns:{tableId}` | OpenMetadata column data |
| `GET /api/v1/platform/catalog/search` | Search catalog assets | Query: `q`, `type?`, `limit?` | `{ items: [CatalogSearchHit] }` | none | OpenMetadata search API |

Notes:
- Morpheus IDs are stable slugs derived from OpenMetadata FQNs (`service.database.schema.table`). The adapter handles conversion in both directions.
- Pagination for datasources/datasets/tables is optional for phase 0; we can support simple `page`/`pageSize` query params and let the adapter fetch pages lazily.

## 5. Config, Caching, Error Handling

### 5.1 Configuration Keys (to add in `settings.py`)
```
catalog:
  provider: "openmetadata"
  base_url: "https://openmetadata.company.com/api"
  auth_token_env: "OPENMETADATA_TOKEN"
  request_timeout_seconds: 10
  page_size: 100
```
- Tokens read from the specified env var or secret backend.
- Adapter adds `Authorization: Bearer <token>` header automatically.

### 5.2 Redis Cache Strategy
| Key | Value | TTL | Invalidated When |
|-----|-------|-----|------------------|
| `catalog:datasources` | JSON payload | 300s | Manual refresh endpoint or connector changes |
| `catalog:datasets:{datasourceId}` | JSON payload | 300s | when connector/datasource updates |
| `catalog:tables:{datasetId}:{type}:{searchHash}` | JSON payload | 300s | dataset rescan |
| `catalog:columns:{tableId}` | JSON payload | 300s | semantic mapping edit referencing the table |

Cache middleware responsibilities:
- Hash query params to build stable keys (e.g., `search` queries).  
- Provide `X-Morpheus-Cache: hit|miss` header for observability.

### 5.3 Error Handling Rules
- `CatalogAdapterError(kind="auth")` → HTTP 401 with message `"OpenMetadata authentication failed"`  
- `kind="not_found"` → HTTP 404  
- `kind="timeout"` → HTTP 504  
- `kind="upstream"` (default) → HTTP 502  
- Unexpected errors bubble up to FastAPI global handler with error ID for tracing.

## 6. Implementation Steps

1. **Create `catalog` module structure**  
   - `backend/core/platform/catalog/adapter.py` (interface + error classes)  
   - `.../catalog/openmetadata_adapter.py` (implementation)  
   - `.../catalog/dto.py` (Pydantic models for responses)

2. **Wire configuration**  
   - Extend config loader to surface catalog settings & token env var lookups.

3. **Implement Redis cache helper**  
   - Shared `CacheClient` wrapper with `get_json/set_json/invalidate(pattern)` utilities.

4. **Build OpenMetadata adapter**  
   - Implement each interface method with REST calls, pagination, and ID translation.  
   - Add retry/backoff via `httpx` or `requests` with exponential backoff for transient failures.

5. **Add FastAPI router**  
   - New `backend/core/platform/api/catalog_router.py` that injects adapter + cache via dependency.  
   - Responses reuse DTOs to ensure consistent JSON schema.

6. **Testing Plan**  
   - Unit tests using `respx` (or similar) to mock OpenMetadata responses.  
   - Cache tests verifying TTL behavior and invalidation triggers.  
   - Contract tests for ID translation (OpenMetadata FQN ↔ Morpheus ID).

7. **Observability**  
   - Add structured logging for adapter calls: method, duration, status, cache hit/miss.  
   - Emit metrics (later) for call counts and failure rates.

This plan satisfies the remaining Phase 0 tasks for `/platform/catalog` by defining the adapter interface, DTOs, endpoint contracts, and operational dependencies (config, caching, error handling).
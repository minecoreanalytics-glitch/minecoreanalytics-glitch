# BigQuery Dataset Discovery Feature

## Overview

The platform now includes dynamic dataset discovery that lists all available datasets and tables from your connected BigQuery project, eliminating the need for hardcoded dataset names.

## API Endpoints

### 1. List All Datasets

**Endpoint:** `GET /api/v1/integrations/bigquery/datasets`

**Description:** Lists all datasets available in the connected BigQuery project with detailed metadata.

**Prerequisites:** BigQuery connection must be established first via `/api/v1/integrations/bigquery/connect`

**Response Format:**
```json
{
  "projectId": "your-project-id",
  "datasets": [
    {
      "datasetId": "customers",
      "projectId": "your-project-id",
      "location": "US",
      "created": "2024-01-15T10:30:00Z",
      "modified": "2024-11-30T14:20:00Z",
      "description": "Customer data warehouse"
    },
    {
      "datasetId": "billing",
      "projectId": "your-project-id",
      "location": "US",
      "created": "2024-02-01T09:00:00Z",
      "modified": "2024-12-01T08:15:00Z",
      "description": "Billing and invoicing data"
    }
  ],
  "count": 2
}
```

**Error Responses:**
- `400 Bad Request` - BigQuery not connected
- `500 Internal Server Error` - Error listing datasets

**Example Usage:**
```bash
curl http://localhost:8000/api/v1/integrations/bigquery/datasets
```

---

### 2. List Tables in a Dataset

**Endpoint:** `GET /api/v1/integrations/bigquery/datasets/{dataset_id}/tables`

**Description:** Lists all tables in a specific dataset with metadata including row counts, sizes, and modification times.

**Path Parameters:**
- `dataset_id` (string, required) - The ID of the dataset to query

**Prerequisites:** BigQuery connection must be established

**Response Format:**
```json
{
  "datasetId": "customers",
  "projectId": "your-project-id",
  "tables": [
    {
      "tableId": "customer_data",
      "numRows": 25553,
      "numBytes": 130023424,
      "createdAt": "2024-01-15T10:30:00Z",
      "modifiedAt": "2024-12-01T08:00:00Z",
      "type": "TABLE"
    },
    {
      "tableId": "customer_interactions",
      "numRows": 1240500,
      "numBytes": 2580234240,
      "createdAt": "2024-01-20T14:00:00Z",
      "modifiedAt": "2024-12-01T09:30:00Z",
      "type": "TABLE"
    }
  ],
  "count": 2
}
```

**Error Responses:**
- `400 Bad Request` - BigQuery not connected
- `500 Internal Server Error` - Error listing tables or dataset not found

**Example Usage:**
```bash
curl http://localhost:8000/api/v1/integrations/bigquery/datasets/customers/tables
```

---

## Frontend Integration

### TypeScript/JavaScript Usage

The frontend `DataService` now includes methods to call these endpoints:

```typescript
import { DataService } from './services/dataService';

// List all datasets
const datasetsResponse = await DataService.listBigQueryDatasets();
console.log('Datasets:', datasetsResponse.datasets);

// List tables in a specific dataset
const tablesResponse = await DataService.listBigQueryTables('customers');
console.log('Tables:', tablesResponse.tables);
```

### Mock Data Support

Both methods include mock data fallback for development/testing when the backend is unavailable or in mock mode.

---

## Backend Implementation

### BigQuery Service Methods

Located in [`backend/services/bigquery_service.py`](backend/services/bigquery_service.py):

```python
def list_datasets(self) -> List[str]:
    """List all datasets in the project"""
    datasets = list(self.client.list_datasets())
    return [dataset.dataset_id for dataset in datasets]

def list_tables(self, dataset_id: str) -> List[Dict[str, Any]]:
    """List all tables in a dataset with metadata"""
    dataset_ref = self.client.dataset(dataset_id)
    tables = list(self.client.list_tables(dataset_ref))
    
    table_info = []
    for table in tables:
        table_ref = dataset_ref.table(table.table_id)
        full_table = self.client.get_table(table_ref)
        
        table_info.append({
            "tableId": table.table_id,
            "numRows": full_table.num_rows,
            "numBytes": full_table.num_bytes,
            "createdAt": full_table.created.isoformat(),
            "modifiedAt": full_table.modified.isoformat(),
            "type": full_table.table_type
        })
    
    return table_info
```

---

## Testing

### Automated Test Script

Run the test script to verify the endpoints:

```bash
cd backend
python scripts/test_dataset_discovery.py
```

The script will:
1. Test the datasets endpoint
2. Test the tables endpoint with the first available dataset
3. Display detailed information about datasets and tables

### Manual Testing

1. **Connect to BigQuery first:**
```bash
curl -X POST http://localhost:8000/api/v1/integrations/bigquery/connect \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "your-project-id",
    "datasetId": "your-dataset",
    "credentials": {...},
    "name": "My BigQuery Connection"
  }'
```

2. **List datasets:**
```bash
curl http://localhost:8000/api/v1/integrations/bigquery/datasets
```

3. **List tables in a dataset:**
```bash
curl http://localhost:8000/api/v1/integrations/bigquery/datasets/customers/tables
```

---

## Migration from Hardcoded Datasets

### Before (Hardcoded)
```yaml
# backend/core/config/htv_config.yaml
entities:
  customer:
    source:
      dataset: "customers"  # Hardcoded
      table: "customer_data"
```

### After (Dynamic Discovery)
```typescript
// Discover available datasets
const { datasets } = await DataService.listBigQueryDatasets();

// Let user select a dataset
const selectedDataset = datasets[0].datasetId;

// Discover tables in that dataset
const { tables } = await DataService.listBigQueryTables(selectedDataset);

// Let user select a table
const selectedTable = tables[0].tableId;
```

---

## Benefits

1. **No Hardcoding:** Automatically discovers all available datasets and tables
2. **Enterprise Ready:** Works with any BigQuery project structure
3. **Real-time Discovery:** Always shows current state of BigQuery project
4. **Metadata Rich:** Provides row counts, sizes, and modification times
5. **Error Handling:** Graceful degradation with clear error messages
6. **Mock Support:** Works in development mode without BigQuery connection

---

## Next Steps

1. **UI Integration:** Build a dataset/table selector in the frontend
2. **Schema Inspection:** Use existing `/api/v1/integrations/bigquery/schema/{dataset_id}/{table_id}` endpoint
3. **Dynamic Configuration:** Allow users to configure entity mappings through UI
4. **Caching:** Consider caching dataset/table lists for performance

---

## Related Endpoints

- `POST /api/v1/integrations/bigquery/connect` - Establish BigQuery connection
- `GET /api/v1/integrations/status` - Check connection status
- `GET /api/v1/integrations/bigquery/schema/{dataset_id}/{table_id}` - Get table schema
- `POST /api/v1/data/query` - Execute SQL queries

---

## Support

For issues or questions:
1. Check that BigQuery connection is established
2. Verify service account has `bigquery.datasets.get` and `bigquery.tables.list` permissions
3. Review backend logs for detailed error messages
4. Run the test script for diagnostics
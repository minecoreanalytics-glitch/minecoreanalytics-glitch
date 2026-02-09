# Morpheus Intelligence Platform - Backend API

FastAPI backend service for the Morpheus Intelligence Platform with Google BigQuery integration.

## Features

- FastAPI REST API with automatic OpenAPI documentation
- Google BigQuery integration for data warehousing
- Customer 360 unified view
- Real-time data synchronization
- CORS-enabled for frontend communication

## Prerequisites

- Python 3.10+
- Google Cloud Platform account with BigQuery enabled
- Service account credentials with BigQuery access

## Installation

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

## Configuration

### Option 1: Using Environment Variables

Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Set your GCP project ID and service account credentials path:
```
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Option 2: Using the Connection API (Recommended)

Connect to BigQuery via the frontend UI or API endpoint by providing:
- Project ID
- Service account JSON credentials (as a dictionary)

## Running the Server

Start the FastAPI server:
```bash
python3 main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /api/v1/health` - Check API and BigQuery connection status

### BigQuery Integration
- `POST /api/v1/integrations/bigquery/connect` - Connect to BigQuery with credentials
- `GET /api/v1/integrations/status` - Get all integrations status
- `GET /api/v1/integrations/bigquery/datasets` - List all datasets
- `GET /api/v1/integrations/bigquery/tables/{dataset_id}` - List tables in a dataset
- `GET /api/v1/integrations/bigquery/schema/{dataset_id}/{table_id}` - Get table schema

### Data Queries
- `POST /api/v1/data/query` - Execute a BigQuery SQL query
- `GET /api/v1/customer/{customer_id}/360` - Get unified customer view

### System
- `GET /api/v1/system/logs` - Get recent system logs

## Example Usage

### Connect to BigQuery

```bash
curl -X POST http://localhost:8000/api/v1/integrations/bigquery/connect \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "your-project-id",
    "datasetId": "your-dataset",
    "credentials": {
      "type": "service_account",
      "project_id": "your-project-id",
      "private_key_id": "...",
      "private_key": "...",
      "client_email": "...",
      "client_id": "...",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "...",
      "client_x509_cert_url": "..."
    }
  }'
```

### Execute a Query

```bash
curl -X POST http://localhost:8000/api/v1/data/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM `project.dataset.table` LIMIT 10"
  }'
```

## BigQuery Service Account Setup

1. Go to Google Cloud Console
2. Navigate to IAM & Admin > Service Accounts
3. Create a new service account
4. Grant BigQuery roles:
   - BigQuery Admin (or)
   - BigQuery Data Editor + BigQuery Job User
5. Create and download JSON key
6. Use the JSON key to connect via the API

## Development

### Project Structure

```
backend/
├── main.py                    # FastAPI application
├── services/
│   ├── __init__.py
│   └── bigquery_service.py   # BigQuery integration service
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md               # This file
```

### Adding New Endpoints

1. Define the endpoint in `main.py`
2. Add business logic in `services/bigquery_service.py`
3. Test via Swagger UI at `/docs`

## Troubleshooting

### Connection Issues

- Verify service account has BigQuery permissions
- Check project ID is correct
- Ensure credentials JSON is valid
- Check network connectivity to Google Cloud

### Query Errors

- Validate SQL syntax
- Ensure tables exist in the specified dataset
- Check data types match schema
- Verify query permissions

## Production Deployment

For production deployment:

1. Use environment variables for configuration
2. Enable HTTPS/TLS
3. Set up proper logging
4. Implement rate limiting
5. Add authentication middleware
6. Use connection pooling
7. Monitor with Cloud Monitoring

## License

Proprietary - Morpheus Intelligence Platform

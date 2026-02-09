# BigQuery OAuth Connection Status

## Summary
Your Morpheus platform is now configured to support OAuth token authentication for BigQuery, and is successfully connected to project **looker-studio-htv**.

## Current Status: ✅ CONNECTED

- **Project ID**: looker-studio-htv
- **Authentication Method**: Service Account (OAuth token expired, fell back to service account)
- **Datasets Available**: 8
- **Connection Status**: Ready

## Available Datasets

1. **HTVallproductssales** - HTV products and sales data
2. **billing_data_dataset** - Billing data 
3. **data_integration** - Data integration platform
4. **htv_analytics** - HTV Analytics - Subscriber and Revenue Data
5. **kommo_data** - Kommo CRM data
6. **prepaid_alez** - Prepaid Alez data
7. **revenue_htv** - Revenue tracking
8. **telehaiti_dataset** - Telehaiti operational data

## OAuth Token Issue

The OAuth token you provided appears to be **invalid or expired**:
```
Token: ya29.a0AUMWg_KIGmlWdwriFmb5FSBmqzne32RQha40iFcvwNhRn8VStHsvWYWOkcS18l19T5MOUfcMTaE9RxccjFyvnUZxe8uQANfDjG2hflx-ynX8GzFvfZslybl-qicLTxtVn6oAcko1oUxfhA8wfLmaBM9BwaO6qne9uhPM5wmSRD2cPpy3LNPFeSZ7xKVOJOU4zLqAZ_OWICwcaCgYKAR0SARYSFQHGX2Mitw72wYH-5Dp9MLAzZx0qKg0211
```

**Error**: `401 Request had invalid authentication credentials. Expected OAuth 2 access token`

### Why OAuth Tokens Expire
OAuth 2.0 access tokens typically expire after 1 hour for security reasons. This token likely expired before you provided it.

## How to Get a Fresh OAuth Token

### Option 1: Using gcloud CLI (Recommended)
```bash
# Login to your Google account
gcloud auth login

# Get a fresh access token
gcloud auth print-access-token

# Copy the token and update .env file
```

### Option 2: Using OAuth 2.0 Playground
1. Go to https://developers.google.com/oauthplayground/
2. Select "BigQuery API v2"
3. Click "Authorize APIs"
4. Click "Exchange authorization code for tokens"
5. Copy the access token
6. Update the .env file

### Option 3: Continue Using Service Account (Current Setup)
Your platform is currently using the service account credentials, which don't expire and work perfectly. This is the recommended approach for production systems.

## Configuration Files

### 1. Backend .env file
Location: `/Users/thierrybijou/Documents/minecore_dev/morpheus-intelligence-platform/backend/.env`

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=looker-studio-htv

# OAuth Token for BigQuery access (refresh when expired)
BIGQUERY_OAUTH_TOKEN=<your-fresh-token-here>

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. Active Connection
Location: `backend/data/active_connection.json`
- Contains the service account credentials
- Automatically restored on backend restart
- Currently using service account authentication

## How OAuth Support Works

The platform now supports both OAuth tokens and service account credentials:

1. **OAuth Token** (Priority 1): Uses `BIGQUERY_OAUTH_TOKEN` from .env
2. **Service Account** (Priority 2): Uses saved credentials from active_connection.json
3. **Default Credentials** (Priority 3): Uses gcloud default credentials

### Fallback Mechanism
If the OAuth token fails (expired/invalid), the system automatically falls back to service account credentials, ensuring uninterrupted service.

## Testing the Connection

Run the test script:
```bash
cd backend
python test_oauth_connection.py
```

Or check via API:
```bash
# Health check
curl http://localhost:8000/api/v1/health

# List datasets
curl http://localhost:8000/api/v1/integrations/bigquery/datasets
```

## Frontend Access

Your frontend at **http://localhost:3000** can now access:
- All 8 datasets in looker-studio-htv project
- Real-time data queries
- Table schemas and metadata
- Customer 360 views
- Graph relationships

## Recommendations

1. **For Development**: Continue using the service account (current setup)
   - No token expiration issues
   - Reliable and consistent
   - Already configured and working

2. **For User Authentication**: Implement OAuth flow
   - Requires OAuth consent screen
   - Token refresh mechanism
   - User-specific permissions

3. **Update OAuth Token**: If you need to use OAuth instead of service account:
   ```bash
   # Get fresh token
   gcloud auth print-access-token
   
   # Update .env file
   # Restart backend server
   ```

## Support

- Test script: `backend/test_oauth_connection.py`
- Backend logs: `tail -f /tmp/backend.log`
- Connection status: `http://localhost:8000/api/v1/integrations/connection-status`

---

**Generated**: January 23, 2026, 11:17 AM
**Status**: Platform connected and operational with service account credentials

# BigQuery Setup Guide

## Step 1: Create or Select a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Either:
   - Select an existing project, OR
   - Click **"New Project"**
     - Name: `morpheus-intelligence` (or your choice)
     - Click **Create**
     - Note the **Project ID** (auto-generated, like `morpheus-intelligence-123456`)

## Step 2: Enable BigQuery API

1. In the search bar, type "BigQuery API"
2. Click on **BigQuery API**
3. Click **Enable** (if not already enabled)
4. Wait for activation (usually instant)

## Step 3: Create a BigQuery Dataset

1. Go to [BigQuery Console](https://console.cloud.google.com/bigquery)
2. In the **Explorer** panel (left sidebar), find your project
3. Click the **⋮** (three dots) next to your project name
4. Select **"Create dataset"**
5. Fill in:
   - **Dataset ID**: `morpheus_data` (or `customers`, `analytics`, etc.)
   - **Location**: Choose based on your needs:
     - `US (multiple regions)` - Most common, best for general use
     - `EU (multiple regions)` - For GDPR compliance
     - Or choose a specific region
   - **Default table expiration**: Leave unchecked (for now)
6. Click **Create dataset**

## Step 4: Create a Service Account

1. Navigate to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Enter details:
   - **Name**: `morpheus-bigquery-service`
   - **Description**: "Service account for Morpheus Platform BigQuery access"
4. Click **Create and Continue**
5. Grant roles:
   - Select **BigQuery Admin** (or)
   - Select both **BigQuery Data Editor** + **BigQuery Job User**
6. Click **Continue**, then **Done**

## Step 5: Create JSON Key

1. Click on your newly created service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Choose **JSON**
5. Click **Create**
6. Save the downloaded JSON file securely

## Step 6: Load Sample Data (Optional)

To test the connection, load some sample data:

1. In BigQuery Console, select your dataset
2. Click **Create Table**
3. Choose:
   - **Create table from**: Upload
   - **Select file**: Upload a CSV file, or
   - **Create table from**: Google Cloud Storage (for larger files)
4. Set:
   - **Table name**: `customers` (or any name)
   - **Schema**: Auto-detect or define manually
5. Click **Create table**

### Or Use Public Datasets:

BigQuery has free public datasets you can query:
- Project ID: `bigquery-public-data`
- Datasets: `usa_names`, `covid19_public`, `google_analytics_sample`, etc.

## Step 7: Your Connection Details

After completing the setup, you'll have:

```
✓ Project ID: morpheus-intelligence-123456
✓ Dataset ID: morpheus_data
✓ Service Account Key: morpheus-bigquery-service-abc123.json
```

## Step 8: Connect to Morpheus Platform

Use these values in the Morpheus platform:

### Via Frontend:
1. Open http://localhost:3000/integration
2. Click **Add Data Source**
3. Select **BigQuery**
4. Enter:
   - Project ID: `morpheus-intelligence-123456`
   - Dataset ID: `morpheus_data`
5. Upload your JSON key file
6. Click **Connect**

### Via API:
```bash
curl -X POST http://localhost:8000/api/v1/integrations/bigquery/connect \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "morpheus-intelligence-123456",
    "datasetId": "morpheus_data",
    "credentials": {PASTE_JSON_KEY_CONTENTS_HERE}
  }'
```

## Verify Connection

Test that everything works:

```bash
# Check health
curl http://localhost:8000/api/v1/health

# List datasets
curl http://localhost:8000/api/v1/integrations/bigquery/datasets

# List tables
curl http://localhost:8000/api/v1/integrations/bigquery/tables/morpheus_data
```

## Costs

- BigQuery free tier: **10 GB storage** + **1 TB queries/month** (free)
- Most small-to-medium applications stay within free tier
- [View pricing](https://cloud.google.com/bigquery/pricing)

## Troubleshooting

### "Access Denied" Error
- Verify service account has BigQuery permissions
- Check that BigQuery API is enabled
- Ensure JSON key is valid and not expired

### "Dataset not found"
- Verify dataset exists in BigQuery console
- Check that dataset ID matches exactly (case-sensitive)
- Ensure dataset is in the same project

### "Permission denied" when querying tables
- Grant additional roles to service account:
  - BigQuery Data Viewer
  - BigQuery Job User

## Security Best Practices

1. **Never commit credentials to Git** (already in .gitignore)
2. **Rotate keys regularly** (every 90 days recommended)
3. **Use least privilege** (grant only necessary permissions)
4. **Monitor usage** in Google Cloud Console
5. **Set up billing alerts** to avoid surprises

## Next Steps

Once connected:
- Import your data into BigQuery tables
- Create views for common queries
- Set up scheduled queries
- Build Customer 360 views
- Enable real-time data streaming

## Resources

- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [BigQuery Sandbox](https://cloud.google.com/bigquery/docs/sandbox) - Free tier details
- [Loading Data](https://cloud.google.com/bigquery/docs/loading-data)
- [Public Datasets](https://cloud.google.com/bigquery/public-data)

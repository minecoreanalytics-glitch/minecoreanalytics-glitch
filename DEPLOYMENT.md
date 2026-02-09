# Morpheus Intelligence Platform - Deployment Guide

## Overview
This guide covers deploying the Morpheus Intelligence Platform to Google Cloud using Cloud Run.

## Prerequisites
- Google Cloud Platform account with billing enabled
- Google Cloud SDK (gcloud CLI) installed and authenticated
- BigQuery dataset and service account key configured
- Docker installed (for local testing)

## Quick Start

### 1. Configure Google Cloud Project
```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Authenticate and set project
gcloud auth login
gcloud config set project $PROJECT_ID
```

### 2. Enable Required APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerydatatransfer.googleapis.com
```

### 3. Configure BigQuery Permissions
Ensure your service account has the following BigQuery roles:
- `BigQuery Data Viewer`
- `BigQuery Job User`
- `BigQuery Read Session User`

### 4. Deploy Using the Script
```bash
# Make script executable (if not already)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## Manual Deployment

### Backend Deployment
```bash
cd backend

# Build and submit backend image
gcloud builds submit --tag gcr.io/$PROJECT_ID/morpheus-backend .

# Deploy backend
gcloud run deploy morpheus-backend \
    --image gcr.io/$PROJECT_ID/morpheus-backend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json" \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10
```

### Frontend Deployment
```bash
# Build and submit frontend image
gcloud builds submit --tag gcr.io/$PROJECT_ID/morpheus-frontend .

# Deploy frontend
gcloud run deploy morpheus-frontend \
    --image gcr.io/$PROJECT_ID/morpheus-frontend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10
```

## Local Development with Docker

### Using Docker Compose
```bash
# Build and run both services
docker-compose up --build

# Access the application at http://localhost
```

### Individual Container Testing
```bash
# Backend only
cd backend
docker build -t morpheus-backend .
docker run -p 8000:8000 -v $(pwd):/app morpheus-backend

# Frontend only
docker build -t morpheus-frontend .
docker run -p 80:80 morpheus-frontend
```

## Environment Configuration

### Backend Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key (set to `/app/service-account-key.json` in container)

### Frontend Configuration
The frontend automatically detects the backend URL in production. For local development, update the API base URL in `services/dataService.ts`.

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Ensure all dependencies are properly listed in `requirements.txt` and `package.json`
   - Check that the service account key is properly mounted

2. **BigQuery Connection Issues**
   - Verify service account has correct BigQuery permissions
   - Check that the key file path is correct in the environment variables

3. **CORS Issues**
   - Ensure the backend CORS settings include the frontend URL
   - For local development, add `http://localhost:3000` to allowed origins

4. **Memory/CPU Limits**
   - Adjust Cloud Run memory and CPU settings based on your usage
   - Monitor usage in Google Cloud Console

### Logs and Monitoring
```bash
# View Cloud Run logs
gcloud logs read --service=morpheus-backend --region=$REGION
gcloud logs read --service=morpheus-frontend --region=$REGION

# View in Cloud Console
open https://console.cloud.google.com/run
```

## Security Considerations

1. **Service Account Keys**
   - Never commit service account keys to version control
   - Use Google Cloud Secret Manager for sensitive credentials in production

2. **Network Security**
   - Cloud Run services are publicly accessible by default
   - Implement authentication if needed
   - Use VPC networking for private services

3. **Data Security**
   - Ensure BigQuery datasets have appropriate access controls
   - Use encrypted connections for sensitive data

## Cost Optimization

- **Cloud Run**: Pay only for actual usage (CPU time and memory)
- **BigQuery**: Costs based on data processed and stored
- **Cloud Build**: Free tier available for builds

Monitor costs in the Google Cloud Console billing section.

## Support

For issues or questions:
1. Check the logs using `gcloud logs read`
2. Review the troubleshooting section above
3. Check the GitHub repository for known issues
4. Contact the development team
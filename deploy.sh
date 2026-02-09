#!/bin/bash

# Morpheus Intelligence Platform - Google Cloud Deployment Script
# This script builds and deploys the backend and frontend to Google Cloud Run

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-gcp-project-id"}
REGION=${REGION:-"us-central1"}
BACKEND_SERVICE_NAME="morpheus-backend"
FRONTEND_SERVICE_NAME="morpheus-frontend"

echo "🚀 Starting Morpheus Intelligence Platform deployment to Google Cloud..."

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ Not authenticated with Google Cloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
echo "📋 Setting Google Cloud project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerydatatransfer.googleapis.com

# Build and deploy backend
echo "🏗️  Building and deploying backend..."
cd backend

# Build the backend image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME .

# Deploy backend to Cloud Run
gcloud run deploy $BACKEND_SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json" \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --region=$REGION --format="value(status.url)")

cd ..

# Build and deploy frontend
echo "🏗️  Building and deploying frontend..."

# Build the frontend image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME .

# Deploy frontend to Cloud Run
gcloud run deploy $FRONTEND_SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10

FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: $BACKEND_URL"
echo ""
echo "📝 Next steps:"
echo "1. Update your frontend environment variables to point to the backend URL"
echo "2. Configure BigQuery permissions for the service account"
echo "3. Test the deployed application"
echo "4. Set up custom domain if needed"
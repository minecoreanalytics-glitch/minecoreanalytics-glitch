# Deployment Permissions Guide for Cloud Run (Project: morpheus-485203)

## Objective
Enable `minecoreanalytics@gmail.com` to run Cloud Build and deploy backend/frontend to Cloud Run in project **morpheus-485203**.

## Required IAM Roles (project-level unless noted)
- **Service Usage Admin** (includes `serviceusage.services.use`)
- **Cloud Build Editor** (or higher) **and** **Storage Admin** (or bucket-level write on `morpheus-485203_cloudbuild`)
- **Cloud Run Admin** (or Cloud Run Developer with deploy permissions)
- **IAM Service Account User** on the deploy service account (if using a dedicated SA)

## Console Steps
1) Open IAM: https://console.cloud.google.com/iam-admin/iam?project=morpheus-485203
2) Click **Grant Access**.
3) Principal: `minecoreanalytics@gmail.com`.
4) Add roles:
   - Service Usage Admin
   - Cloud Build Editor
   - Storage Admin (or bucket-level write on `morpheus-485203_cloudbuild`)
   - Cloud Run Admin
   - (If using a dedicated deploy SA) IAM Service Account User on that SA
5) Save.
6) Enable APIs (if not already): Cloud Run Admin API, Cloud Build API, Artifact Registry API.

## gcloud Role Binding (if you have org rights)
```bash
gcloud projects add-iam-policy-binding morpheus-485203 \
  --member="user:minecoreanalytics@gmail.com" \
  --role="roles/serviceusage.serviceUsageAdmin"

gcloud projects add-iam-policy-binding morpheus-485203 \
  --member="user:minecoreanalytics@gmail.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding morpheus-485203 \
  --member="user:minecoreanalytics@gmail.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding morpheus-485203 \
  --member="user:minecoreanalytics@gmail.com" \
  --role="roles/run.admin"

# If a dedicated deploy service account is used (replace DEPLOY-SA):
gcloud iam service-accounts add-iam-policy-binding DEPLOY-SA@MORPHEUS-485203.iam.gserviceaccount.com \
  --member="user:minecoreanalytics@gmail.com" \
  --role="roles/iam.serviceAccountUser"
```

## Post-Grant Verification & Deploy Steps
1) Set quota project: `gcloud auth application-default set-quota-project morpheus-485203`
2) Backend build: `gcloud builds submit --tag gcr.io/morpheus-485203/morpheus-backend ./backend`
3) Backend deploy: `gcloud run deploy morpheus-backend --image gcr.io/morpheus-485203/morpheus-backend --region us-central1 --allow-unauthenticated --set-secrets=/app/temp_creds.json=bigquery-credentials:latest --memory 1Gi --cpu 1 --max-instances 10`
4) Frontend build: `gcloud builds submit --tag gcr.io/morpheus-485203/morpheus-frontend .`
5) Frontend deploy: `gcloud run deploy morpheus-frontend --image gcr.io/morpheus-485203/morpheus-frontend --region us-central1 --allow-unauthenticated --memory 512Mi --cpu 1 --max-instances 10`

## Notes
- If org policy restricts broad roles, ensure at minimum: `serviceusage.services.use`, Cloud Build write to the build bucket, Cloud Run deploy, and SA User on the deploy SA.
- Confirm required APIs are enabled before retrying builds.

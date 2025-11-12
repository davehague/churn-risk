# 08 - Cloud Run Deployment

**Estimated Time:** 20-30 minutes
**Cost:** ~$5/month (within free tier), auto-scales with traffic
**Prerequisites:** Guides 01-07 completed

---

## Overview

Deploy your FastAPI backend to Cloud Run using source-based deployment. Cloud Run will automatically containerize your Python application.

**What You'll Deploy:**
- Python application using Cloud Run buildpacks (no Dockerfile needed)
- Cloud Run service with auto-scaling
- Environment variables and secret references
- Cloud SQL connection via Unix socket
- Public HTTPS endpoint with automatic SSL

**Result:** Your API live at `https://your-service-xyz.run.app`

---

## Step 1: Prepare Application Files

### 1.1 Generate requirements.txt

Cloud Run's Python buildpack uses `requirements.txt` for dependencies.

```bash
cd backend

# Generate requirements.txt from Poetry
poetry run pip freeze > requirements.txt
```

**Verify:**
```bash
wc -l requirements.txt
# Should show ~80-90 lines
```

### 1.2 Create Procfile

Create a `Procfile` to tell Cloud Run how to start your application:

```bash
cat > Procfile << 'EOF'
web: cd /workspace && PYTHONPATH=/workspace uvicorn src.main:app --host 0.0.0.0 --port $PORT
EOF
```

**What this does:**
- `cd /workspace` - Changes to Cloud Run's default directory
- `PYTHONPATH=/workspace` - Ensures Python can find your `src` module
- `uvicorn src.main:app` - Starts your FastAPI application
- `--port $PORT` - Uses Cloud Run's dynamically assigned port

### 1.3 Rename Dockerfiles (If Present)

If you have Dockerfiles, rename them so Cloud Run uses buildpacks instead:

```bash
# Only run if Dockerfiles exist
[ -f Dockerfile ] && mv Dockerfile Dockerfile.backup
[ -f Dockerfile.simple ] && mv Dockerfile.simple Dockerfile.simple.backup
```

---

## Step 2: Deploy to Cloud Run

### 2.1 Initial Deployment (No Configuration)

First, deploy without secrets/env vars to create the service:

```bash
gcloud run deploy churn-risk-api \
  --source . \
  --region=us-east1 \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=512Mi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10
```

**What happens:**
1. Cloud Run creates an Artifact Registry repository (first time only)
2. Uploads your source code
3. Builds container using Python buildpack
4. Deploys the service

**Time:** 5-10 minutes (first deployment)

**Expected output:**
```
Building using Buildpacks and deploying container to Cloud Run service [churn-risk-api]
Building Container...done
Creating Revision...done
Service [churn-risk-api] revision [churn-risk-api-00001-xxx] has been deployed
Service URL: https://churn-risk-api-XXX.us-east1.run.app
```

**Save the Service URL!**

### 2.2 Test Initial Deployment

```bash
SERVICE_URL=$(gcloud run services describe churn-risk-api --region=us-east1 --format="value(status.url)")

curl ${SERVICE_URL}/health
```

**Expected response:**
```json
{"status":"healthy","environment":"production"}
```

---

## Step 3: Configure Environment Variables and Secrets

### 3.1 Get Required Values

```bash
# Project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"

# Cloud SQL Connection Name
INSTANCE_CONN=$(gcloud sql instances describe churn-risk-db --format="value(connectionName)")
echo "Instance Connection: $INSTANCE_CONN"

# Region
REGION=$(gcloud config get-value compute/region)
echo "Region: $REGION"

# Service URL (from previous step)
SERVICE_URL=$(gcloud run services describe churn-risk-api --region=us-east1 --format="value(status.url)")
echo "Service URL: $SERVICE_URL"
```

**Save these values - you'll use them in the next command.**

### 3.2 Update Service with Full Configuration

```bash
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --add-cloudsql-instances=${INSTANCE_CONN} \
  --set-env-vars="ENVIRONMENT=production,\
API_V1_PREFIX=/api/v1,\
FIREBASE_PROJECT_ID=your-firebase-project-id,\
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json,\
HUBSPOT_CLIENT_ID=your-hubspot-client-id,\
HUBSPOT_REDIRECT_URI=${SERVICE_URL}/api/v1/integrations/hubspot/callback,\
OPENROUTER_MODEL=google/gemini-2.5-flash,\
GOOGLE_CLOUD_PROJECT=${PROJECT_ID},\
DATABASE_URL=postgresql://churn_risk_app:PLACEHOLDER@/churn_risk_prod?host=/cloudsql/${INSTANCE_CONN}" \
  --update-secrets="/app/firebase-credentials.json=firebase-credentials:latest,\
HUBSPOT_CLIENT_SECRET=hubspot-client-secret:latest,\
OPENROUTER_API_KEY=openrouter-api-key:latest,\
DATABASE_PASSWORD=database-password:latest,\
SECRET_KEY=app-secret-key:latest"
```

**Replace:**
- `your-firebase-project-id` with your actual Firebase project ID
- `your-hubspot-client-id` with your HubSpot OAuth client ID

**Note:** The `DATABASE_PASSWORD` secret will be used instead of `PLACEHOLDER` at runtime.

**Time:** 2-3 minutes

---

## Step 4: Verify Production Deployment

### 4.1 Test Health Endpoint

```bash
SERVICE_URL=$(gcloud run services describe churn-risk-api --region=us-east1 --format="value(status.url)")

curl ${SERVICE_URL}/health
```

**Expected:**
```json
{"status":"healthy","environment":"production"}
```

### 4.2 Test API Root

```bash
curl ${SERVICE_URL}/api/v1/
```

**Expected:**
```json
{"message":"Churn Risk API","version":"0.1.0"}
```

### 4.3 Test API Documentation

Open in browser:
```
https://YOUR-SERVICE-URL.run.app/api/v1/docs
```

**Should show:** Interactive Swagger UI documentation

### 4.4 View Logs

```bash
gcloud run services logs read churn-risk-api \
  --region=us-east1 \
  --limit=50
```

---

## Step 5: Configure Service Account Permissions

### 5.1 Grant Cloud SQL Client Role

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 5.2 Verify Secret Access

The service account should already have `secretmanager.secretAccessor` role from Guide 05.

**Verify:**
```bash
gcloud secrets get-iam-policy firebase-credentials
```

---

## Step 6: Update HubSpot OAuth Redirect URI

### 6.1 Update HubSpot App Configuration

Your HubSpot OAuth app needs to know about the production URL.

**Edit `hs-churn-risk/public-app.json`:**

```json
{
  "name": "Churn Risk App",
  "redirectUrls": [
    "http://localhost:8000/api/v1/integrations/hubspot/callback",
    "https://YOUR-SERVICE-URL.run.app/api/v1/integrations/hubspot/callback"
  ],
  ...
}
```

**Upload updated config:**

```bash
cd hs-churn-risk
hs project upload
```

### 6.2 Test OAuth Flow

1. Get authorization URL from production API
2. Follow OAuth flow
3. Verify callback works with production URL

---

## Step 7: Run Database Migrations (If Needed)

If this is a fresh deployment, run migrations:

```bash
# Connect to Cloud SQL via proxy (in separate terminal)
cloud-sql-proxy ${INSTANCE_CONN}

# Run migrations
cd backend
DATABASE_URL="postgresql://churn_risk_app:YOUR_PASSWORD@localhost:5432/churn_risk_prod" \
  poetry run alembic upgrade head
```

---

## Verification Checklist

Before proceeding:

- [ ] Service deployed successfully
- [ ] Service URL accessible via HTTPS
- [ ] Health endpoint returns 200
- [ ] API docs accessible
- [ ] All environment variables configured
- [ ] Secrets mounted correctly
- [ ] Cloud SQL connection working
- [ ] Service account has correct permissions
- [ ] HubSpot OAuth redirect URI updated
- [ ] Database migrations run (if needed)

---

## Deployment Configuration Summary

**Save these values:**

```
Service Name:     churn-risk-api
Service URL:      _________________________________
Region:           us-east1
Deployment Type:  Source-based (Python buildpack)
CPU:              1
Memory:           512Mi
Min Instances:    0 (scales to zero)
Max Instances:    10
Timeout:          300s (5 minutes)
Cloud SQL:        Connected via Unix socket
```

---

## Costs Incurred

**Cloud Run pricing (per month):**
- CPU: $0.000024/vCPU-second
- Memory: $0.0000025/GiB-second
- Requests: $0.40 per million requests

**Free tier includes:**
- 2 million requests/month
- 360,000 vCPU-seconds/month
- 180,000 GiB-seconds/month

**Estimated cost (low traffic):**
- 100 requests/day = ~$0
- 1,000 requests/day = ~$2/month
- 10,000 requests/day = ~$15/month

**With $300 credits:** Covered for months

---

## Updating Your Deployment

### Deploy New Version

When you update your code:

```bash
cd backend

# Regenerate requirements.txt if dependencies changed
poetry run pip freeze > requirements.txt

# Deploy updated code
gcloud run deploy churn-risk-api \
  --source . \
  --region=us-east1
```

**Traffic automatically shifts to new version** (blue-green deployment).

**Time:** 3-5 minutes (faster than initial deployment)

### Roll Back to Previous Version

```bash
# List revisions
gcloud run revisions list --service=churn-risk-api --region=us-east1

# Route traffic to previous revision
gcloud run services update-traffic churn-risk-api \
  --region=us-east1 \
  --to-revisions=churn-risk-api-00001-xxx=100
```

---

## Troubleshooting

### Problem: Build fails with "Module not found"

**Solution:** Ensure `requirements.txt` is up to date:
```bash
poetry run pip freeze > requirements.txt
```

### Problem: "Secret not found" error

**Solutions:**
- Verify secrets exist: `gcloud secrets list`
- Check secret names match exactly (case-sensitive)
- Ensure service account has secretAccessor role

### Problem: "Memory limit exceeded" / container crashes

**Solution:** Increase memory:
```bash
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --memory=1Gi
```

### Problem: Requests timeout

**Solution:** Increase timeout:
```bash
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --timeout=600
```

### Problem: Database connection fails

**Solutions:**
- Check Cloud SQL instance is running: `gcloud sql instances list`
- Verify connection name: `gcloud sql instances describe churn-risk-db`
- Check service account has Cloud SQL Client role
- Review logs: `gcloud run services logs read churn-risk-api --region=us-east1`

### Problem: Environment variables not set

**Solution:** Update service configuration:
```bash
gcloud run services describe churn-risk-api --region=us-east1
# Review current configuration, then update with correct values
```

---

## What You've Accomplished

✅ Deployed FastAPI backend to Cloud Run using buildpacks
✅ Connected to Cloud SQL via private connection
✅ Configured all environment variables
✅ Mounted secrets from Secret Manager
✅ Enabled public HTTPS access with automatic SSL
✅ Your API is live in production!

---

## Next Steps

With your backend deployed, verify everything works end-to-end.

**→ Next:** [09 - Production Testing](09-production-testing.md)

---

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Buildpacks](https://cloud.google.com/docs/buildpacks/overview)
- [Python Buildpack](https://github.com/GoogleCloudPlatform/buildpacks/tree/main/cmd/python)
- [Cloud Run Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)

---

## Why We Use Buildpacks (Not Dockerfiles)

**Advantages:**
- No Docker expertise required
- Automatic security updates from Google
- Optimized for Cloud Run environment
- Simpler deployment workflow
- Less maintenance overhead

**When to Use Dockerfile:**
- Custom base image requirements
- Special system dependencies not available in buildpack
- Multi-stage builds for optimization
- Full control over container environment

For most Python applications, buildpacks are recommended.

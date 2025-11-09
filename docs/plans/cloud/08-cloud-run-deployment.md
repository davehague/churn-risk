# 08 - Cloud Run Deployment

**Estimated Time:** 30-40 minutes
**Cost:** ~$5/month (within free tier), auto-scales with traffic
**Prerequisites:** Guides 01-07 completed

---

## Overview

Deploy your FastAPI backend to Cloud Run - Google's serverless container platform. This is the main production deployment.

**What You'll Deploy:**
- Docker container to Google Container Registry (GCR)
- Cloud Run service with auto-scaling
- Environment variables and secret references
- Cloud SQL connection via Unix socket
- Public HTTPS endpoint with automatic SSL

**Result:** Your API live at `https://your-service-xyz.run.app`

---

## Step 1: Push Docker Image to Container Registry

### 1.1 Tag Image for GCR

```bash
cd backend

# Get your project ID
PROJECT_ID=$(gcloud config get-value project)

# Tag image for Google Container Registry
docker tag churn-risk-backend:test gcr.io/${PROJECT_ID}/churn-risk-backend:v1
```

**Verify tag:**
```bash
docker images | grep churn-risk
```

**Should show both:**
```
churn-risk-backend    test  abc123...
gcr.io/PROJECT/churn-risk-backend  v1  abc123...
```

### 1.2 Configure Docker for GCR

```bash
gcloud auth configure-docker
```

**Expected output:**
```
Adding credentials for all GCR repositories.
```

**This is a one-time setup.**

### 1.3 Push Image to GCR

```bash
docker push gcr.io/${PROJECT_ID}/churn-risk-backend:v1
```

**Expected output:**
```
The push refers to repository [gcr.io/PROJECT_ID/churn-risk-backend]
v1: digest: sha256:abc123... size: 1234
```

**Time:** 2-5 minutes (first time, faster with cache)

### 1.4 Verify Image in GCR

```bash
gcloud container images list
```

**Should show:**
```
NAME
gcr.io/PROJECT_ID/churn-risk-backend
```

**List versions:**
```bash
gcloud container images list-tags gcr.io/${PROJECT_ID}/churn-risk-backend
```

**Should show:**
```
DIGEST      TAGS  TIMESTAMP
sha256:...  v1    2025-11-09T...
```

---

## Step 2: Create Cloud Run Service

### 2.1 Get Required Values

**You'll need these values:**

```bash
# 1. Project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"

# 2. Cloud SQL Connection Name
INSTANCE_CONN=$(gcloud sql instances describe churn-risk-db --format="value(connectionName)")
echo "Instance Connection: $INSTANCE_CONN"

# 3. Region
REGION=$(gcloud config get-value compute/region)
echo "Region: $REGION"
```

**Save these - you'll use them in the deployment command.**

### 2.2 Deploy to Cloud Run (Initial Deployment)

**Run this command (replace placeholders):**

```bash
gcloud run deploy churn-risk-api \
  --image=gcr.io/${PROJECT_ID}/churn-risk-backend:v1 \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=1 \
  --memory=512Mi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --add-cloudsql-instances=${INSTANCE_CONN} \
  --set-env-vars="ENVIRONMENT=production,API_V1_PREFIX=/api/v1,CORS_ORIGINS=https://churn-risk-api-xyz.run.app,PORT=8080" \
  --set-secrets="FIREBASE_CREDENTIALS=firebase-credentials:latest,HUBSPOT_CLIENT_SECRET=hubspot-client-secret:latest,OPENROUTER_API_KEY=openrouter-api-key:latest,DATABASE_PASSWORD=database-password:latest,SECRET_KEY=app-secret-key:latest"
```

**Wait for deployment:** 2-5 minutes

**Expected output:**
```
Deploying container to Cloud Run service [churn-risk-api] in project [PROJECT_ID] region [REGION]
✓ Deploying new service... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
  ✓ Setting IAM Policy...
Done.
Service [churn-risk-api] revision [churn-risk-api-00001-xyz] has been deployed and is serving 100 percent of traffic.
Service URL: https://churn-risk-api-xyz123.run.app
```

**Save the Service URL!**

---

## Step 3: Configure Environment Variables Properly

### 3.1 Update with All Required Variables

The initial deployment set basic variables. Now add the rest:

```bash
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --update-env-vars="ENVIRONMENT=production,\
API_V1_PREFIX=/api/v1,\
PORT=8080,\
FIREBASE_PROJECT_ID=your-firebase-project-id,\
HUBSPOT_CLIENT_ID=your-hubspot-client-id,\
HUBSPOT_REDIRECT_URI=https://YOUR-SERVICE-URL.run.app/api/v1/integrations/hubspot/callback,\
OPENROUTER_MODEL=google/gemini-2.5-flash"
```

**Replace:**
- `your-firebase-project-id` with your actual Firebase project ID
- `your-hubspot-client-id` with your HubSpot OAuth client ID
- `YOUR-SERVICE-URL` with your actual Cloud Run URL

### 3.2 Configure Database Connection

Update to add database URL environment variable:

```bash
# Construct database URL using secret
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --update-env-vars="DATABASE_URL=postgresql://churn_risk_app:\$(DATABASE_PASSWORD)@/churn_risk_prod?host=/cloudsql/${INSTANCE_CONN}"
```

**Note:** Cloud Run connects to Cloud SQL via Unix socket at `/cloudsql/INSTANCE_CONNECTION_NAME`

---

## Step 4: Update Secret References for Firebase

### 4.1 Modify Startup to Use Secret Manager for Firebase

Since Firebase credentials are JSON (not just a simple string), we need to handle them specially.

**Option A: Mount as Volume (Recommended)**

```bash
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --update-secrets="/app/firebase-credentials.json=firebase-credentials:latest"
```

This mounts the secret as a file at `/app/firebase-credentials.json`.

**Then update environment variable:**

```bash
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --update-env-vars="FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json"
```

---

## Step 5: Configure Service Account Permissions

### 5.1 Verify Default Service Account

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "Service Account: ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
```

### 5.2 Grant Cloud SQL Client Role

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 5.3 Verify Secret Access (Already Done in Guide 05)

The service account should already have `secretmanager.secretAccessor` role from Guide 05.

**Verify:**
```bash
gcloud secrets get-iam-policy firebase-credentials
```

---

## Step 6: Test Production Deployment

### 6.1 Get Service URL

```bash
gcloud run services describe churn-risk-api \
  --region=${REGION} \
  --format="value(status.url)"
```

**Save this URL.**

### 6.2 Test Health Endpoint

```bash
SERVICE_URL=$(gcloud run services describe churn-risk-api --region=${REGION} --format="value(status.url)")

curl ${SERVICE_URL}/health
```

**Expected response:**
```json
{"status":"healthy","environment":"production"}
```

### 6.3 Test API Root

```bash
curl ${SERVICE_URL}/api/v1/
```

**Expected response:**
```json
{"message":"Churn Risk API","version":"1.0.0"}
```

### 6.4 Test API Docs

Open in browser:
```
https://YOUR-SERVICE-URL.run.app/api/v1/docs
```

**Should show:** Interactive API documentation

---

## Step 7: Update HubSpot OAuth Redirect URI

### 7.1 Update HubSpot App Configuration

Your HubSpot OAuth app needs to know about the new production URL.

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

### 7.2 Test OAuth Flow

1. Get authorization URL from production API
2. Follow OAuth flow
3. Verify callback works with production URL

---

## Step 8: Configure CORS for Production

### 8.1 Update CORS Origins

If you have a frontend deployed (or will deploy later):

```bash
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --update-env-vars="CORS_ORIGINS=https://YOUR-SERVICE-URL.run.app,https://your-frontend-domain.com"
```

**For now (backend only):**
```bash
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --update-env-vars="CORS_ORIGINS=https://YOUR-SERVICE-URL.run.app,http://localhost:3000"
```

This allows your local frontend to call the production API.

---

## Step 9: Configure Logging and Monitoring

### 9.1 View Logs

```bash
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=50
```

### 9.2 Enable Request Logging

Cloud Run automatically logs all HTTP requests. View them in Cloud Console:
- **GCP Console → Cloud Run → churn-risk-api → Logs**

---

## Verification Checklist

Before proceeding:

- [ ] Docker image pushed to GCR successfully
- [ ] Cloud Run service deployed
- [ ] Service URL accessible via HTTPS
- [ ] Health endpoint returns 200
- [ ] API docs accessible
- [ ] All environment variables configured
- [ ] Secrets mounted correctly
- [ ] Cloud SQL connection working
- [ ] Service account has correct permissions
- [ ] HubSpot OAuth redirect URI updated

---

## Deployment Configuration Summary

**Save these values:**

```
Service Name:     churn-risk-api
Service URL:      _________________________________
Region:           us-central1 (or your region)
Image:            gcr.io/PROJECT_ID/churn-risk-backend:v1
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

```bash
# Build new image
docker build -t churn-risk-backend:v2 .

# Tag for GCR
docker tag churn-risk-backend:v2 gcr.io/${PROJECT_ID}/churn-risk-backend:v2

# Push to GCR
docker push gcr.io/${PROJECT_ID}/churn-risk-backend:v2

# Deploy to Cloud Run
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --image=gcr.io/${PROJECT_ID}/churn-risk-backend:v2
```

**Traffic automatically shifts to new version** (blue-green deployment).

---

## Troubleshooting

### Problem: Deployment fails with "Cloud SQL connection error"

**Solutions:**
- Verify `--add-cloudsql-instances` matches exactly: `PROJECT:REGION:INSTANCE`
- Check service account has Cloud SQL Client role
- Ensure Cloud SQL instance is running

### Problem: "Secret not found" error

**Solutions:**
- Verify secrets exist: `gcloud secrets list`
- Check secret names match exactly (case-sensitive)
- Ensure service account has secretAccessor role

### Problem: "Memory limit exceeded" / container crashes

**Solutions:**
```bash
# Increase memory
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --memory=1Gi
```

### Problem: Requests timeout

**Solutions:**
```bash
# Increase timeout
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --timeout=600
```

### Problem: Database connection fails

**Solutions:**
- Check DATABASE_URL format for Unix socket
- Verify Cloud SQL instance connection name
- Test connection from Cloud Shell: `gcloud sql connect churn-risk-db`

---

## What You've Accomplished

✅ Deployed Docker image to Google Container Registry
✅ Created Cloud Run service with auto-scaling
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
- [Container Registry](https://cloud.google.com/container-registry/docs)
- [Cloud Run Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)

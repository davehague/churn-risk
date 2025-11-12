# 11 - CI/CD Setup - ✅ COMPLETED

**Status**: ✅ **Working** - Automated tests + deployment on every push to main
**Production URL**: https://churn-risk-api-461448724047.us-east1.run.app
**Latest Build**: 57/57 tests passing, deployed with buildpacks

**Estimated Time:** 30-45 minutes
**Cost:** $0 (first 120 build-minutes/day free)
**Prerequisites:** Guides 01-10 completed

---

## Overview

Set up automated deployments using Google Cloud Build. When you push to GitHub, your app automatically builds and deploys to Cloud Run.

**What We Set Up:**
- ✅ GitHub repository connection (Cloud Build GitHub App)
- ✅ Cloud Build trigger on push to main branch
- ✅ Automatic testing before deployment (57 tests with SQLite)
- ✅ Buildpack deployment to Cloud Run (not Docker)
- ✅ Automatic rollback capability (Cloud Run revisions)

---

## Step 1: Connect GitHub Repository

### 1.1 Enable Cloud Build API

```bash
gcloud services enable cloudbuild.googleapis.com
```

### 1.2 Connect to GitHub

Go to: **GCP Console → Cloud Build → Triggers**

Click **"CONNECT REPOSITORY"**

1. Select source: **GitHub (Cloud Build GitHub App)**
2. Click "CONTINUE"
3. Authenticate with GitHub
4. Select your repository: `yourusername/churn-risk-app`
5. Click "CONNECT"
6. Click "CREATE A TRIGGER" (we'll configure in next step)

---

## Step 2: Create cloudbuild.yaml - ✅ COMPLETED

### 2.1 Final Working Configuration

**File**: `backend/cloudbuild.yaml` (already created)

```yaml
steps:
  # Step 1: Run tests
  - name: 'python:3.11-slim'
    dir: 'backend'
    entrypoint: 'bash'
    env:
      - 'DATABASE_URL=sqlite:///./test.db'
      - 'FIREBASE_PROJECT_ID=test-project'
      - 'OPENROUTER_API_KEY=test-key'
      - 'HUBSPOT_CLIENT_ID=test-client-id'
      - 'HUBSPOT_CLIENT_SECRET=test-client-secret'
      - 'HUBSPOT_REDIRECT_URI=http://localhost:8000/callback'
      - 'SECRET_KEY=test-secret-key-for-ci-cd-builds-only'
    args:
      - '-c'
      - |
        pip install poetry
        poetry config virtualenvs.create false
        poetry install
        pytest tests/

  # Step 2: Deploy to Cloud Run using buildpack
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'churn-risk-api'
      - '--source=.'
      - '--region=us-east1'
      - '--platform=managed'
      - '--allow-unauthenticated'
    dir: 'backend'

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'

timeout: '1200s'  # 20 minutes
```

**Key Differences from Original Guide:**
- ✅ Uses **buildpack deployment** (`--source=.`) instead of Docker builds
- ✅ Tests run with **SQLite** (fast, no external DB needed)
- ✅ Test environment variables provided inline
- ✅ Simpler, more reliable than custom Dockerfiles
- ✅ Same deployment method as manual deployments (proven working)

**Why Buildpacks?**
- Docker builds failed 11 times with ModuleNotFoundError (see troubleshooting-deployment.md)
- Buildpack deployment was the only working solution
- Production service already runs on buildpacks
- Keeps CI/CD consistent with manual deployments

---

## Step 3: Create Build Trigger

### 3.1 Create Trigger for Main Branch

Go to: **Cloud Build → Triggers → CREATE TRIGGER**

**Configuration:**
- **Name:** `deploy-production`
- **Event:** Push to a branch
- **Repository:** Your connected repo
- **Branch:** `^main$` (regex for main branch)
- **Build configuration:** Cloud Build configuration file
- **Location:** `backend/cloudbuild.yaml`

**Advanced settings:**
- **Substitution variables:**
  - `_REGION`: `us-central1`

**Click "CREATE"**

### 3.2 Create Trigger for Development Branch (Optional)

**Configuration:**
- **Name:** `deploy-development`
- **Event:** Push to a branch
- **Branch:** `^dev$`
- **Build configuration:** `backend/cloudbuild.yaml`

**Deploy to different service:**
```yaml
# In cloudbuild.yaml, add _SERVICE substitution
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - '${_SERVICE}'  # churn-risk-api-dev for dev branch
```

---

## Step 4: Test CI/CD Pipeline

### 4.1 Make a Test Change

```bash
# Make a small change
echo "# Test change" >> backend/README.md

# Commit and push
git add backend/README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

### 4.2 Monitor Build Progress

Go to: **Cloud Build → History**

**Should see:**
- Build triggered automatically
- Running tests
- Building Docker image
- Deploying to Cloud Run

**Build time:** 5-15 minutes (first time, faster with cache)

### 4.3 Check Build Logs

Click on the build to see detailed logs:
```
Step 1: Run tests... SUCCESS
Step 2: Build Docker image... SUCCESS
Step 3: Push Docker image... SUCCESS
Step 4: Deploy to Cloud Run... SUCCESS
```

---

## Step 5: Set Up Deployment Notifications

### 5.1 Slack Notifications (Optional)

Create **Cloud Function** to send Slack notifications:

```bash
# Create Slack webhook URL first
# Then create Cloud Function triggered by Pub/Sub
```

### 5.2 Email Notifications

Configure Pub/Sub subscription for build updates:

```bash
# Subscribe to Cloud Build topic
gcloud pubsub subscriptions create build-notifications \
  --topic=cloud-builds \
  --push-endpoint=YOUR_EMAIL_WEBHOOK
```

---

## Step 6: Rollback Strategy

### 6.1 List Previous Revisions

```bash
gcloud run revisions list \
  --service=churn-risk-api \
  --region=us-central1
```

### 6.2 Rollback to Previous Version

```bash
# Get previous revision name
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service=churn-risk-api \
  --region=us-central1 \
  --format="value(name)" \
  --limit=2 | tail -1)

# Route 100% traffic to previous revision
gcloud run services update-traffic churn-risk-api \
  --region=us-central1 \
  --to-revisions=$PREVIOUS_REVISION=100
```

**Instant rollback** - takes < 30 seconds

---

## Step 7: Advanced: Canary Deployments

### 7.1 Gradual Rollout Strategy

Deploy new version with traffic split:

```yaml
# In cloudbuild.yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - 'churn-risk-api'
    - '--image=gcr.io/$PROJECT_ID/churn-risk-backend:$SHORT_SHA'
    - '--region=us-central1'
    - '--no-traffic'  # Deploy without sending traffic

# Then manually split traffic
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'services'
    - 'update-traffic'
    - 'churn-risk-api'
    - '--region=us-central1'
    - '--to-latest=10'  # 10% to new version
```

### 7.2 Monitor Canary

Wait 10 minutes, monitor:
- Error rates
- Latency
- Logs for new issues

### 7.3 Complete Rollout or Rollback

**If good:**
```bash
gcloud run services update-traffic churn-risk-api \
  --region=us-central1 \
  --to-latest=100
```

**If bad:**
```bash
gcloud run services update-traffic churn-risk-api \
  --region=us-central1 \
  --to-latest=0  # Revert to previous
```

---

## Best Practices

**Do:**
- ✅ Always run tests before deployment
- ✅ Use semantic versioning for images
- ✅ Keep previous revisions for rollback
- ✅ Monitor deployments for errors
- ✅ Use separate environments (dev/staging/prod)

**Don't:**
- ❌ Deploy without testing
- ❌ Delete old revisions immediately
- ❌ Deploy during peak traffic hours
- ❌ Skip monitoring after deployment

---

## Troubleshooting

### Problem: Build fails on tests

**Solution:**
```bash
# Run tests locally first
cd backend
poetry run pytest

# Fix failing tests before pushing
```

### Problem: "Permission denied" during deployment

**Solution:**
```bash
# Grant Cloud Build service account necessary roles
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Problem: Build times out

**Solution:**
```yaml
# Increase timeout in cloudbuild.yaml
timeout: '1800s'  # 30 minutes
```

---

## Costs

**Cloud Build pricing:**
- First 120 build-minutes/day: Free
- Additional: $0.003/build-minute

**Your usage (typical):**
- 1-2 deploys/day = 10-20 minutes
- **Cost:** $0/month (within free tier)

---

## What You've Accomplished

✅ Connected GitHub to Cloud Build
✅ Created automated build pipeline
✅ Set up automatic deployments
✅ Configured rollback capability
✅ Implemented canary deployment strategy

---

## Next Steps

**→ Next:** [12 - Custom Domain](12-custom-domain-optional.md) (Optional)

**Or skip to:** [13 - Troubleshooting](13-troubleshooting.md)

---

## Additional Resources

- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Build Triggers](https://cloud.google.com/build/docs/automating-builds/create-manage-triggers)
- [Cloud Run CI/CD](https://cloud.google.com/run/docs/continuous-deployment)

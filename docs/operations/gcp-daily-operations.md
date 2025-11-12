# GCP Daily Operations Guide - Churn Risk App

**Last Updated:** 2025-11-12
**Project:** churn-risk-app
**Project ID:** churn-risk-app (actual ID: 461448724047)

This guide helps you quickly locate and access all GCP resources after returning to the project.

---

## Quick Access - GCP Console

**Main Dashboard**: https://console.cloud.google.com/
**Project**: Select "churn-risk-app" from dropdown at top

---

## 🚀 Cloud Run (Backend Service)

**Location**: GCP Console → Cloud Run → churn-risk-api

**Quick Access**: https://console.cloud.google.com/run

**Service Details:**
- **Name**: `churn-risk-api`
- **Region**: `us-east1`
- **URL**: https://churn-risk-api-461448724047.us-east1.run.app

**What to Check:**
1. **Status**: Look for green checkmark (service is running)
2. **Latest Revision**: Click service name → see revision history
3. **Logs**: Click "LOGS" tab to see real-time application logs
4. **Metrics**: See request count, latency, error rate
5. **Traffic Split**: Check if 100% traffic goes to latest revision

**Common Tasks:**
- **View logs**: Click "LOGS" tab
- **Check metrics**: See "METRICS" tab for traffic/errors
- **Rollback**: Click "Revisions & Traffic" → route traffic to previous revision
- **Edit service**: Click "EDIT & DEPLOY NEW REVISION" (manual deployment)

**Health Check URL**: https://churn-risk-api-461448724047.us-east1.run.app/health

---

## 🗄️ Cloud SQL (Database)

**Location**: GCP Console → SQL → churn-risk-db

**Quick Access**: https://console.cloud.google.com/sql/instances

**Database Details:**
- **Instance Name**: `churn-risk-db`
- **Database**: `churn_risk_prod`
- **Region**: `us-east1`
- **Version**: PostgreSQL 15
- **Type**: db-f1-micro (shared core, 0.6GB RAM)

**What to Check:**
1. **Status**: Instance should show "Running" with green checkmark
2. **Connections**: See current connections count
3. **Storage**: Check used vs total storage (10GB)
4. **Backups**: View automatic backups (daily)
5. **CPU/Memory**: Check utilization metrics

**Common Tasks:**
- **View backups**: Click instance → "Backups" tab
- **Check connections**: Click instance → "Observability" tab
- **Connect via proxy**:
  ```bash
  cloud-sql-proxy churn-risk-app:us-east1:churn-risk-db
  psql "host=127.0.0.1 port=5432 user=postgres dbname=churn_risk_prod"
  ```
- **Query insights**: "Observability" → "Query Insights" (if enabled)

**Important Info:**
- Connection name: `churn-risk-app:us-east1:churn-risk-db`
- User: `postgres` (admin), `churn_risk_app` (application)
- Password stored in Secret Manager

---

## 🔐 Secret Manager (Credentials)

**Location**: GCP Console → Security → Secret Manager

**Quick Access**: https://console.cloud.google.com/security/secret-manager

**Secrets Stored:**
1. **database-url** - PostgreSQL connection string
2. **firebase-credentials** - Firebase service account JSON
3. **hubspot-client-id** - HubSpot OAuth client ID
4. **hubspot-client-secret** - HubSpot OAuth secret
5. **openrouter-api-key** - OpenRouter AI API key
6. **secret-key** - Application secret key

**What to Check:**
- All secrets should show "Enabled" status
- Check "Last Accessed" date to verify they're being used
- Version count (should be ≥1)

**Common Tasks:**
- **View secret value**: Click secret → "Versions" tab → "View secret value"
- **Add new version**: Click "NEW VERSION" (rotates secret)
- **Grant access**: Click "PERMISSIONS" tab → add service account

**Important**: Cloud Run service account already has access to all secrets

---

## 🔨 Cloud Build (CI/CD)

**Location**: GCP Console → Cloud Build

**Quick Access**: https://console.cloud.google.com/cloud-build

### Build History

**Path**: Cloud Build → History

**What to Check:**
1. **Latest build status**: Should show "Success" (green)
2. **Build time**: Typically 10-15 minutes
3. **Trigger source**: Should show GitHub commit SHA
4. **Build steps**:
   - Step 0: Tests (57/57 passing)
   - Step 1: Deploy to Cloud Run

**Common Tasks:**
- **View logs**: Click build ID → see detailed logs
- **Retry build**: Click "RETRY" button
- **View trigger**: See which Git commit triggered build

### Build Triggers

**Path**: Cloud Build → Triggers → deploy-production

**Trigger Details:**
- **Name**: `deploy-production`
- **Event**: Push to branch `main`
- **Repository**: GitHub (your repo)
- **Configuration**: `backend/cloudbuild.yaml`

**What to Check:**
- Trigger is enabled (blue toggle)
- Branch filter is `^main$`
- Build configuration points to correct file

**Common Tasks:**
- **Manual trigger**: Click "RUN" button → "RUN TRIGGER"
- **Disable trigger**: Toggle switch to pause automatic deployments
- **Edit trigger**: Click trigger name → "EDIT"

---

## 📊 Monitoring (Logs & Metrics)

**Location**: GCP Console → Logging / Monitoring

**Quick Access**: https://console.cloud.google.com/logs

### Application Logs

**Path**: Logging → Logs Explorer

**Quick Filters:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="churn-risk-api"
severity>=DEFAULT
```

**What to Look For:**
- Error logs (severity=ERROR)
- Request logs (HTTP methods, status codes)
- Application logs (your print/logger statements)

**Common Queries:**
- **Errors only**: `severity>=ERROR`
- **Slow requests**: `httpRequest.latency>1s`
- **Specific endpoint**: `httpRequest.requestUrl=~"/api/v1/tickets"`

### Metrics & Dashboards

**Path**: Monitoring → Dashboards

**Key Metrics:**
- **Cloud Run**: Request count, latency, error rate, instance count
- **Cloud SQL**: CPU utilization, connections, queries/second
- **Cloud Build**: Build success rate, duration

---

## 💰 Billing & Costs

**Location**: GCP Console → Billing

**Quick Access**: https://console.cloud.google.com/billing

**What to Check:**
1. **Current month costs**: See total spend
2. **Budget alerts**: Any warnings/alerts
3. **Cost breakdown by service**:
   - Cloud Run (pay per request)
   - Cloud SQL (~$9/month)
   - Cloud Build (free tier: 120 min/day)
   - Cloud Storage (minimal)

**Expected Costs** (with $300 free credits):
- Cloud SQL: ~$9/month
- Cloud Run: <$5/month (low traffic)
- Cloud Build: $0 (within free tier)
- **Total**: ~$14/month

---

## 🔄 Common Day-to-Day Tasks

### Check if Production is Healthy
1. Visit: https://churn-risk-api-461448724047.us-east1.run.app/health
2. Should return: `{"status":"healthy"}`
3. Check Cloud Run metrics for error rate

### View Recent Deployments
1. Go to Cloud Build → History
2. See latest builds with status
3. Click build ID to see logs

### Check Application Errors
1. Go to Logging → Logs Explorer
2. Filter: `severity>=ERROR resource.type="cloud_run_revision"`
3. Look for patterns in errors

### Connect to Production Database
```bash
# Start Cloud SQL Proxy
cloud-sql-proxy churn-risk-app:us-east1:churn-risk-db

# In another terminal
psql "host=127.0.0.1 port=5432 user=postgres dbname=churn_risk_prod"
```

### Rollback a Bad Deployment
1. Go to Cloud Run → churn-risk-api
2. Click "Revisions & Traffic"
3. Find previous working revision
4. Click "⋮" menu → "Manage traffic"
5. Set 100% traffic to previous revision

### View Secret Values
1. Go to Secret Manager
2. Click secret name
3. Click "Versions" tab
4. Click version → "View secret value"

### Manual Deployment (if needed)
```bash
cd backend
gcloud run deploy churn-risk-api \
  --source=. \
  --region=us-east1
```

---

## 🚨 Troubleshooting Quick Reference

### Service Won't Start
- **Check**: Cloud Run logs for startup errors
- **Look for**: Import errors, missing secrets, connection failures
- **Fix**: Review Secret Manager access, check Cloud SQL connectivity

### Database Connection Issues
- **Check**: Cloud SQL instance is running
- **Check**: Cloud Run has correct connection name
- **Check**: Database credentials in Secret Manager
- **Test**: Connect via Cloud SQL Proxy locally

### Build Failures
- **Check**: Cloud Build history for error logs
- **Common**: Test failures (Step 0), deployment issues (Step 1)
- **Fix**: Run tests locally, check for syntax errors

### High Costs
- **Check**: Cloud Run instance count (should scale to 0)
- **Check**: Cloud SQL connections (shouldn't have leaks)
- **Check**: Cloud Build minutes (stay under 120/day free)

---

## 📞 Quick Links Cheatsheet

| Resource | Direct Link |
|----------|------------|
| Production Service | https://churn-risk-api-461448724047.us-east1.run.app |
| Cloud Run Console | https://console.cloud.google.com/run |
| Cloud SQL Console | https://console.cloud.google.com/sql/instances |
| Secret Manager | https://console.cloud.google.com/security/secret-manager |
| Build History | https://console.cloud.google.com/cloud-build/builds |
| Application Logs | https://console.cloud.google.com/logs |
| Billing | https://console.cloud.google.com/billing |

---

## 📝 Important Notes

1. **Never delete Cloud SQL backups** - They're your safety net
2. **Check billing weekly** - Catch cost spikes early
3. **Review logs after deployments** - Ensure no new errors
4. **Keep local .env updated** - Match production config
5. **Test locally before pushing** - CI/CD deploys automatically

---

**Pro Tip**: Bookmark the Cloud Run and Build History pages for daily checks!

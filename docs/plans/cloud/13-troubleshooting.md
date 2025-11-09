# 13 - Troubleshooting Guide

**Quick Reference:** Common issues and solutions

---

## Quick Diagnostics

### Get Current Status

```bash
# Service status
gcloud run services describe churn-risk-api --region=us-central1

# Recent logs
gcloud run services logs read churn-risk-api --region=us-central1 --limit=50

# Recent errors only
gcloud run services logs read churn-risk-api --region=us-central1 --limit=200 | grep ERROR
```

---

## Deployment Issues

### Container Won't Start

**Symptoms:** Service shows "Revision failed", 502 errors

**Check:**
```bash
gcloud run services logs read churn-risk-api --region=us-central1 --limit=100
```

**Common causes:**

**1. Missing environment variable**
```
KeyError: 'DATABASE_URL'
```
**Fix:**
```bash
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --update-env-vars="DATABASE_URL=postgresql://..."
```

**2. Python import error**
```
ModuleNotFoundError: No module named 'fastapi'
```
**Fix:** Rebuild Docker image with correct dependencies

**3. Port mismatch**
```
Container failed to start. Failed to start and then listen on the port defined by the PORT environment variable.
```
**Fix:** Ensure Dockerfile exposes port 8080 and app listens on PORT env var

---

## Database Connection Issues

### Can't Connect to Cloud SQL

**Symptoms:** "connection refused", "password authentication failed"

**Check:**
```bash
# Verify Cloud SQL instance is running
gcloud sql instances describe churn-risk-db

# Check connection name
gcloud sql instances describe churn-risk-db --format="value(connectionName)"

# Verify service account has Cloud SQL Client role
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
```

**Solutions:**

**1. Wrong connection name**
```bash
# Update Cloud Run with correct connection
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE
```

**2. Wrong DATABASE_URL format**

For Cloud Run (Unix socket):
```
postgresql://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
```

NOT:
```
postgresql://user:password@localhost:5432/dbname  # Wrong for Cloud Run
```

**3. Missing permissions**
```bash
# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

---

## Secret Manager Issues

### Can't Access Secrets

**Symptoms:** "Permission denied", "Secret not found"

**Check:**
```bash
# Verify secret exists
gcloud secrets list

# Check secret value
gcloud secrets versions access latest --secret="hubspot-client-secret"

# Check permissions
gcloud secrets get-iam-policy firebase-credentials
```

**Solutions:**

**1. Secret doesn't exist**
```bash
# Create secret
echo -n "VALUE" | gcloud secrets create SECRET_NAME \
  --replication-policy="automatic" \
  --data-file=-
```

**2. No permission**
```bash
# Grant access
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**3. Wrong secret reference in Cloud Run**
```bash
# Update secret reference
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --update-secrets="SECRET_NAME=gcp-secret-name:latest"
```

---

## Performance Issues

### Slow Response Times

**Check:**
```bash
# View latency metrics
gcloud run services describe churn-risk-api \
  --region=us-central1 \
  --format="value(status.latestReadyRevisionName)"
```

**Common causes:**

**1. Cold starts**
```bash
# Set minimum instances
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --min-instances=1
```

**2. Insufficient resources**
```bash
# Increase CPU/memory
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --cpu=2 \
  --memory=1Gi
```

**3. Slow database queries**
- Check query performance
- Add database indexes
- Enable connection pooling

---

## OAuth / Authentication Issues

### HubSpot OAuth Fails

**Symptoms:** Redirect fails, "redirect_uri mismatch"

**Check redirect URI:**
```bash
# Should match exactly
echo "Expected: https://YOUR-URL.run.app/api/v1/integrations/hubspot/callback"
```

**Fix:**
1. Update `hs-churn-risk/public-app.json`
2. Run `hs project upload`
3. Update Cloud Run env var

### Firebase Auth Fails

**Symptoms:** "Invalid authentication token"

**Check:**
```bash
# Verify Firebase credentials are mounted
gcloud run services describe churn-risk-api \
  --region=us-central1 \
  --format="yaml" | grep firebase
```

**Fix:**
```bash
# Remount secret as volume
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --update-secrets="/app/firebase-credentials.json=firebase-credentials:latest"
```

---

## Build Issues

### Docker Build Fails

**Common errors:**

**1. Poetry install fails**
```
ERROR: Could not find a version that satisfies the requirement...
```
**Fix:** Update `pyproject.toml`, run `poetry lock`

**2. Image too large**
```
ERROR: failed to push: size exceeds maximum
```
**Fix:** Use multi-stage build (already in Dockerfile)

**3. Python version mismatch**
```
ERROR: This package requires Python >=3.11
```
**Fix:** Update Dockerfile base image to `python:3.11-slim`

---

## Monitoring & Logging

### No Logs Showing

**Check:**
```bash
# Ensure logging enabled
gcloud run services describe churn-risk-api \
  --region=us-central1 \
  --format="value(spec.template.metadata.annotations.run.googleapis.com/client-name)"
```

**View logs in Console:**
- GCP Console → Cloud Run → churn-risk-api → Logs

### Alerts Not Working

**Check notification channels:**
```bash
gcloud alpha monitoring channels list
```

**Test alert:**
1. Manually trigger condition
2. Check notification channel is verified
3. Check spam folder for emails

---

## Cost Issues

### Unexpected Charges

**Check spending:**
- GCP Console → Billing → Reports
- Filter by: Project, Service, Time Range

**Common causes:**
1. Forgot to set min-instances=0 (always running)
2. Cloud SQL instance too large
3. Excessive log storage
4. Large container images

**Optimize:**
```bash
# Set min instances to 0
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --min-instances=0

# Reduce Cloud SQL if needed
gcloud sql instances patch churn-risk-db \
  --tier=db-f1-micro
```

---

## Emergency Procedures

### Immediate Rollback

```bash
# List revisions
gcloud run revisions list --service=churn-risk-api --region=us-central1

# Get previous revision
PREVIOUS=$(gcloud run revisions list --service=churn-risk-api --region=us-central1 --format="value(name)" --limit=2 | tail -1)

# Rollback
gcloud run services update-traffic churn-risk-api \
  --region=us-central1 \
  --to-revisions=$PREVIOUS=100
```

### Stop All Traffic

```bash
# Set max instances to 0
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --max-instances=0
```

### Delete and Redeploy

```bash
# Delete service (data in Cloud SQL is safe)
gcloud run services delete churn-risk-api --region=us-central1

# Redeploy from scratch
# Follow Guide 08 again
```

---

## Getting Help

**1. Check logs first:**
```bash
gcloud run services logs read churn-risk-api --region=us-central1 --limit=200
```

**2. Check Error Reporting:**
- GCP Console → Error Reporting

**3. Community resources:**
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/google-cloud-run)
- [Google Cloud Community](https://www.googlecloudcommunity.com/)

**4. GCP Support:**
- Free tier: Community support only
- Paid support: Available with support plan

---

## Useful Commands Reference

```bash
# Service info
gcloud run services describe churn-risk-api --region=us-central1

# Logs (last 50 lines)
gcloud run services logs read churn-risk-api --region=us-central1 --limit=50

# Errors only
gcloud run services logs read churn-risk-api --region=us-central1 | grep ERROR

# Follow logs (live)
gcloud run services logs tail churn-risk-api --region=us-central1

# Revisions
gcloud run revisions list --service=churn-risk-api --region=us-central1

# Environment variables
gcloud run services describe churn-risk-api --region=us-central1 --format="value(spec.template.spec.containers[0].env)"

# Update single env var
gcloud run services update churn-risk-api --region=us-central1 --update-env-vars="KEY=value"

# Restart service (redeploy current revision)
gcloud run services update churn-risk-api --region=us-central1 --clear-env-vars=""
```

---

## Still Having Issues?

1. **Review all guides** - Ensure you followed each step
2. **Check prerequisites** - Verify all APIs enabled, permissions granted
3. **Compare with working state** - Review what changed since it last worked
4. **Test locally first** - Use Guide 07 to test Docker container locally
5. **Start fresh** - Sometimes easier to delete and redeploy

---

**End of Deployment Guides**

Return to: [Overview](00-overview.md) | [README](README.md)

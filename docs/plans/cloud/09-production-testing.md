# 09 - Production Testing

**Estimated Time:** 20-30 minutes
**Cost:** $0 (covered by free tier)
**Prerequisites:** Guide 08 completed (deployed to Cloud Run)

---

## Overview

Comprehensive testing of your production deployment to ensure everything works correctly.

**What You'll Test:**
- API endpoints respond correctly
- Database connectivity
- Firebase authentication
- HubSpot OAuth flow
- Secret Manager integration
- Error handling and logging
- Performance and response times

---

## Step 1: Basic Health Checks

### 1.1 Get Your Service URL

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=$(gcloud config get-value compute/region)
SERVICE_URL=$(gcloud run services describe churn-risk-api --region=${REGION} --format="value(status.url)")

echo "Service URL: $SERVICE_URL"
```

### 1.2 Test Health Endpoint

```bash
curl ${SERVICE_URL}/health
```

**Expected:**
```json
{"status":"healthy","environment":"production"}
```

### 1.3 Test API Root

```bash
curl ${SERVICE_URL}/api/v1/
```

**Expected:**
```json
{"message":"Churn Risk API","version":"1.0.0"}
```

### 1.4 Test API Documentation

Open in browser:
```
https://YOUR-SERVICE-URL.run.app/api/v1/docs
```

**Should show:** Interactive Swagger UI

---

## Step 2: Database Connectivity Test

### 2.1 Check Logs for Database Connection

```bash
gcloud run services logs read churn-risk-api --region=${REGION} --limit=20
```

**Look for:**
- ✅ No "connection refused" errors
- ✅ No "password authentication failed"
- ✅ Successful startup messages

### 2.2 Test Database-Dependent Endpoint

If you created any test data:

```bash
curl ${SERVICE_URL}/api/v1/users/me \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

**(Would require Firebase token - test after auth setup)**

---

## Step 3: Test Firebase Authentication

### 3.1 Verify Firebase Integration

Check that Firebase credentials are loaded:

```bash
# Check logs for Firebase initialization
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=100 | grep -i firebase
```

**Should NOT see:**
- ❌ "Firebase app already exists"
- ❌ "Could not load Firebase credentials"
- ❌ "Permission denied" errors

### 3.2 Test Protected Endpoint (with Local Frontend)

If you have your local frontend running:

1. Start frontend: `cd frontend && npm run dev`
2. Update frontend `.env` to use production API:
```bash
NUXT_PUBLIC_API_BASE=https://YOUR-SERVICE-URL.run.app
```
3. Test login flow through frontend
4. Verify API calls to production work

---

## Step 4: Test Secret Manager Integration

### 4.1 Verify Secrets Accessible

Check logs for secret access:

```bash
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=50 | grep -i secret
```

**Should NOT see:**
- ❌ "Permission denied accessing secret"
- ❌ "Secret not found"

### 4.2 Test HubSpot OAuth (Requires Secrets)

The OAuth flow will fail if secrets aren't accessible.

Test authorization URL generation:

```bash
curl ${SERVICE_URL}/api/v1/integrations/hubspot/authorize \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

**(Returns authorization URL if secrets work)**

---

## Step 5: Performance Testing

### 5.1 Test Response Times

```bash
# Test health endpoint latency
time curl -s ${SERVICE_URL}/health > /dev/null
```

**Target:** < 200ms for health check

### 5.2 Test Cold Start Time

```bash
# Scale to zero
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --min-instances=0

# Wait 15 minutes for scale-down
sleep 900

# Test cold start
time curl ${SERVICE_URL}/health
```

**Expected:** 2-5 seconds (first request after scale-to-zero)

### 5.3 Test Under Load

```bash
# Send 100 requests
for i in {1..100}; do
  curl -s ${SERVICE_URL}/health > /dev/null &
done
wait

echo "All requests completed"
```

Check logs for errors:
```bash
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=200 | grep ERROR
```

**Should see:** No errors

---

## Step 6: Test Error Handling

### 6.1 Test 404 Handling

```bash
curl -i ${SERVICE_URL}/api/v1/nonexistent
```

**Expected:**
```
HTTP/2 404
{"detail":"Not Found"}
```

### 6.2 Test Invalid Authentication

```bash
curl -i ${SERVICE_URL}/api/v1/me \
  -H "Authorization: Bearer invalid-token"
```

**Expected:**
```
HTTP/2 401
{"detail":"Invalid authentication token"}
```

---

## Step 7: Monitor Logs and Metrics

### 7.1 View Recent Logs

```bash
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=50
```

### 7.2 Check for Errors

```bash
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=500 | grep -E "ERROR|CRITICAL|Exception"
```

**Should be:** Empty (no critical errors)

### 7.3 View Metrics in Console

Go to: **GCP Console → Cloud Run → churn-risk-api → Metrics**

**Check:**
- Request count
- Request latency (p50, p95, p99)
- Error rate
- Container instance count

---

## Step 8: Test HubSpot OAuth Flow (End-to-End)

### 8.1 Update HubSpot Redirect URI

Ensure your HubSpot app has the production URL in `redirectUrls`.

### 8.2 Test Authorization URL

Get auth URL from production:

```bash
# With valid Firebase token
curl ${SERVICE_URL}/api/v1/integrations/hubspot/authorize \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 8.3 Complete OAuth Flow

1. Open returned authorization URL in browser
2. Authorize HubSpot
3. Verify redirect to production callback
4. Check logs for successful token exchange

---

## Step 9: Verify Deployment Configuration

### 9.1 Check Service Configuration

```bash
gcloud run services describe churn-risk-api \
  --region=${REGION} \
  --format=yaml
```

**Verify:**
- Image: `gcr.io/PROJECT/churn-risk-backend:v1`
- CPU: 1
- Memory: 512Mi
- Cloud SQL connection configured
- All environment variables present
- Secrets mounted correctly

### 9.2 Check Service Account Permissions

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Verify Cloud SQL Client role
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --format="table(bindings.role)"
```

**Should include:**
- `roles/cloudsql.client`

---

## Step 10: Cost Monitoring

### 10.1 Check Current Spend

Go to: **GCP Console → Billing → Reports**

Filter by:
- Project: Your project
- Services: Cloud Run, Cloud SQL
- Time range: Last 7 days

### 10.2 Verify Within Free Tier

```bash
# Check Cloud Run usage
gcloud run services describe churn-risk-api \
  --region=${REGION} \
  --format="value(status.traffic)"
```

**With minimal traffic:** Should be well within free tier ($0 cost)

---

## Verification Checklist

Production deployment is ready when:

- [ ] Health endpoint returns 200
- [ ] API documentation accessible
- [ ] No errors in logs
- [ ] Database connectivity working
- [ ] Firebase credentials loaded
- [ ] Secrets accessible from Secret Manager
- [ ] Response times acceptable (< 1s)
- [ ] Error handling works correctly
- [ ] HubSpot OAuth can be authorized
- [ ] CORS configured correctly
- [ ] Costs within expected range

---

## Common Issues & Quick Fixes

### Issue: "502 Bad Gateway"

**Cause:** Container failed to start
**Fix:**
```bash
# Check logs
gcloud run services logs read churn-risk-api --region=${REGION} --limit=50

# Common causes:
# - Missing environment variable
# - Database connection failed
# - Secret not accessible
```

### Issue: "Cloud SQL connection failed"

**Cause:** Unix socket path incorrect or permissions missing
**Fix:**
```bash
# Verify connection name
gcloud sql instances describe churn-risk-db --format="value(connectionName)"

# Update Cloud Run with correct connection
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE
```

### Issue: High latency (> 5 seconds)

**Causes:**
- Cold start
- Database query slow
- External API call slow

**Fix:**
```bash
# Set minimum instances to avoid cold starts
gcloud run services update churn-risk-api \
  --region=${REGION} \
  --min-instances=1
```

---

## Performance Benchmarks

**Target performance:**
- Health check: < 200ms
- API root: < 300ms
- Database query: < 500ms
- Cold start: < 5s

**If slower:**
- Check Cloud SQL location (same region as Cloud Run?)
- Enable connection pooling
- Optimize database queries
- Consider increasing CPU/memory

---

## What You've Accomplished

✅ Verified production deployment works
✅ Tested all critical endpoints
✅ Confirmed database connectivity
✅ Validated secret management
✅ Checked error handling
✅ Monitored performance metrics
✅ Verified costs within budget

---

## Next Steps

With production tested and verified, set up monitoring and alerts.

**→ Next:** [10 - Monitoring Setup](10-monitoring.md)

---

## Additional Resources

- [Cloud Run Logging](https://cloud.google.com/run/docs/logging)
- [Cloud Run Metrics](https://cloud.google.com/run/docs/monitoring)
- [Troubleshooting Cloud Run](https://cloud.google.com/run/docs/troubleshooting)

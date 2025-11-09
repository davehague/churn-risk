# 10 - Monitoring & Alerts

**Estimated Time:** 15-20 minutes
**Cost:** Free (within limits)
**Prerequisites:** Guide 09 completed

---

## Overview

Set up logging, monitoring, and alerts for your production deployment.

**What You'll Set Up:**
- Cloud Logging for application logs
- Uptime checks for availability monitoring
- Error alerting via email
- Cost monitoring and budget alerts
- Performance dashboards

---

## Step 1: Cloud Logging

### 1.1 View Application Logs

```bash
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=100
```

### 1.2 Create Log Query in Console

Go to: **GCP Console → Logging → Logs Explorer**

**Query for errors:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="churn-risk-api"
severity>=ERROR
```

**Save this query as:** "Cloud Run Errors"

### 1.3 Enable Log-based Metrics

Create custom metric for tracking specific events:

```bash
gcloud logging metrics create churn_risk_errors \
  --description="Count of ERROR level logs" \
  --log-filter='resource.type="cloud_run_revision"
resource.labels.service_name="churn-risk-api"
severity>=ERROR'
```

---

## Step 2: Uptime Monitoring

### 2.1 Create Uptime Check

Go to: **GCP Console → Monitoring → Uptime checks**

**Click "CREATE UPTIME CHECK"**

**Configuration:**
- **Title:** Churn Risk API Health Check
- **Protocol:** HTTPS
- **Resource Type:** URL
- **Hostname:** YOUR-SERVICE-URL.run.app
- **Path:** /health
- **Check frequency:** 5 minutes
- **Regions:** Select 3-4 regions (USA, Europe, Asia)

**Response validation:**
- Response code: 200
- Response content: `healthy`

**Click "CREATE"**

### 2.2 Create Alert Policy for Uptime

After creating uptime check:

1. Click on the uptime check
2. Click "CREATE ALERT"
3. Configure alert:
   - **Alert name:** API Down Alert
   - **Condition:** Check fails from at least 2 locations
   - **Duration:** 5 minutes
   - **Notification:** Email to your address

**Click "SAVE"**

---

## Step 3: Error Rate Alerts

### 3.1 Create Error Rate Alert

Go to: **GCP Console → Monitoring → Alerting**

**Click "CREATE POLICY"**

**Add Condition:**
- **Target:** Cloud Run Revision
- **Metric:** Request count
- **Filter:** response_code_class = "5xx"
- **Aggregation:** Sum
- **Condition:** Above threshold
- **Threshold value:** 10 (errors in 5 minutes)
- **Duration:** 5 minutes

**Notification:**
- Channel: Your email

**Alert name:** High Error Rate - Churn Risk API

**Click "SAVE"**

---

## Step 4: Cost Monitoring

### 4.1 Check Current Costs

Go to: **GCP Console → Billing → Reports**

**Filter by:**
- **Projects:** Your project
- **Services:** Cloud Run, Cloud SQL, Secret Manager
- **Time range:** Last 30 days

### 4.2 Set Up Budget Alert (If Not Done in Guide 01)

Go to: **Billing → Budgets & alerts**

**CREATE BUDGET:**
- **Name:** Monthly Production Budget
- **Projects:** Your project
- **Budget amount:** $50/month
- **Alerts:**
  - 50% = $25
  - 80% = $40
  - 100% = $50
- **Email notifications:** Your email

---

## Step 5: Performance Dashboard

### 5.1 Create Custom Dashboard

Go to: **GCP Console → Monitoring → Dashboards**

**CREATE DASHBOARD:** "Churn Risk Production"

**Add charts:**

**Chart 1: Request Rate**
- Metric: Cloud Run request count
- Aggregation: Rate (requests/second)
- Filter: service_name = churn-risk-api

**Chart 2: Latency (p50, p95, p99)**
- Metric: Cloud Run request latencies
- Percentiles: 50th, 95th, 99th
- Filter: service_name = churn-risk-api

**Chart 3: Error Rate**
- Metric: Cloud Run request count
- Filter: response_code_class = "5xx"
- Aggregation: Rate

**Chart 4: Container Instances**
- Metric: Cloud Run instance count
- Shows auto-scaling behavior

**Chart 5: CPU Utilization**
- Metric: Cloud Run container CPU utilization
- Shows if you need to adjust resources

**Chart 6: Memory Utilization**
- Metric: Cloud Run container memory utilization

**Chart 7: Cloud SQL Connections**
- Metric: Cloud SQL database connections
- Filter: database_id = churn-risk-db

**Save dashboard**

---

## Step 6: Log-Based Alerts

### 6.1 Alert on Specific Errors

Create alert for database connection errors:

```bash
gcloud alpha logging metrics create database_errors \
  --description="Database connection errors" \
  --log-filter='resource.type="cloud_run_revision"
resource.labels.service_name="churn-risk-api"
textPayload=~"connection.*failed"
OR textPayload=~"database.*error"'
```

### 6.2 Create Alert Policy

Go to: **Monitoring → Alerting → CREATE POLICY**

**Condition:**
- Metric: database_errors (log-based metric)
- Threshold: > 0 in 5 minutes

**Notification:** Email

**Name:** Database Connection Errors

---

## Step 7: Notification Channels

### 7.1 Add Email Notification

Go to: **Monitoring → Alerting → Edit notification channels**

**Add Email:**
- Email address: your@email.com
- Display name: Your Name

**Verify** by clicking link in email

### 7.2 Optional: Add Slack Notifications

If you use Slack:

1. **Monitoring → Alerting → Edit notification channels**
2. **ADD NEW → Slack**
3. Follow OAuth flow to connect Slack workspace
4. Select channel for alerts

### 7.3 Optional: Add SMS Notifications

1. **Monitoring → Alerting → Edit notification channels**
2. **ADD NEW → SMS**
3. Enter phone number
4. Verify with code

---

## Step 8: Application Performance Monitoring

### 8.1 Enable Cloud Trace (Request Tracing)

Cloud Trace is automatically enabled for Cloud Run.

**View traces:**
- **GCP Console → Trace → Trace list**
- See request latency breakdown

### 8.2 Enable Cloud Profiler (Optional)

For deeper performance analysis:

```bash
# Add to requirements
poetry add google-cloud-profiler
```

**Update main.py:**
```python
import googlecloudprofiler

# In production only
if settings.ENVIRONMENT == "production":
    try:
        googlecloudprofiler.start(service='churn-risk-api')
    except:
        pass  # Ignore profiler errors
```

---

## Step 9: Set Up SLOs (Service Level Objectives)

### 9.1 Define SLOs

Go to: **Monitoring → Services → churn-risk-api**

**CREATE SLO:**

**Availability SLO:**
- **SLI:** Availability (request-based)
- **Target:** 99.9% (99.9% of requests succeed)
- **Period:** 28 days
- **Goal:** 99.9%

**Latency SLO:**
- **SLI:** Latency (request-based)
- **Threshold:** 1000ms
- **Target:** 95% (95% of requests < 1s)
- **Period:** 28 days

---

## Step 10: Regular Monitoring Tasks

### 10.1 Daily Checks

```bash
# Quick health check
SERVICE_URL=$(gcloud run services describe churn-risk-api --region=${REGION} --format="value(status.url)")
curl ${SERVICE_URL}/health

# Check recent errors
gcloud run services logs read churn-risk-api \
  --region=${REGION} \
  --limit=50 | grep ERROR
```

### 10.2 Weekly Reviews

**Check dashboard:**
- Request volume trends
- Error rate trends
- Latency percentiles
- Cost trends

### 10.3 Monthly Tasks

**Review:**
- Budget vs actual spend
- SLO compliance
- Alert noise (too many/too few alerts)
- Adjust thresholds if needed

---

## Monitoring Checklist

- [ ] Cloud Logging configured
- [ ] Uptime check created and working
- [ ] Email notifications set up
- [ ] Error rate alerts configured
- [ ] Budget alerts active
- [ ] Performance dashboard created
- [ ] Log-based metrics created
- [ ] SLOs defined (optional)

---

## Alert Notification Best Practices

**Do:**
- ✅ Set meaningful thresholds (avoid alert fatigue)
- ✅ Include context in alert messages
- ✅ Test alerts periodically
- ✅ Have escalation paths (email → SMS → phone)
- ✅ Document runbooks for common alerts

**Don't:**
- ❌ Alert on every single error
- ❌ Use only one notification channel
- ❌ Ignore repeated alerts
- ❌ Set thresholds too sensitive

---

## Costs

**Cloud Monitoring pricing:**
- First 150 MiB of logs: Free
- Uptime checks: Free (first 1 million checks/month)
- Metrics: Free (first 150 MiB ingested/month)

**Your setup:** $0-2/month (well within free tier)

---

## Troubleshooting

### Problem: Not receiving alert emails

**Solutions:**
- Check notification channel is verified
- Check spam folder
- Verify alert policy is enabled
- Test notification channel

### Problem: Too many false alerts

**Solution:**
```bash
# Adjust alert threshold or duration
# Example: Increase threshold from 5 to 10 errors
```

### Problem: Dashboard shows no data

**Solutions:**
- Wait 2-3 minutes for data collection
- Verify service is receiving traffic
- Check time range on dashboard

---

## What You've Accomplished

✅ Set up Cloud Logging
✅ Created uptime monitoring
✅ Configured error alerts
✅ Set budget alerts
✅ Built performance dashboard
✅ Enabled tracing and profiling
✅ Defined SLOs

---

## Next Steps (Optional Enhancements)

**→ Next:** [11 - CI/CD Setup](11-cicd-optional.md) (Optional)

**Or skip to:** [13 - Troubleshooting](13-troubleshooting.md)

---

## Additional Resources

- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Cloud Logging](https://cloud.google.com/logging/docs)
- [Uptime Checks](https://cloud.google.com/monitoring/uptime-checks)
- [SLO Monitoring](https://cloud.google.com/stackdriver/docs/solutions/slo-monitoring)

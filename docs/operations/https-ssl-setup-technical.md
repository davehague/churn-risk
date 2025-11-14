# HTTPS/SSL Setup - Technical Guide

**Prerequisites**: Domain purchased and DNS configured to point to `136.110.172.10`

**Time**: 30-60 minutes
**Cost**: $0 (Google-managed SSL certificates are free)

---

## Overview

Current state:
- Frontend: http://136.110.172.10/ (HTTP only, no domain)
- Backend: https://churn-risk-api-461448724047.us-east1.run.app (already has HTTPS)

Goal:
- Frontend: https://yourdomain.com (HTTPS with custom domain)
- Backend: Keep current URL or add custom domain (optional)

---

## Phase 1: Create SSL Certificate

### Step 1: Reserve the Static IP (Already Done)

Your IP `136.110.172.10` is already reserved as `churn-risk-frontend-ip`.

Verify:
```bash
gcloud compute addresses describe churn-risk-frontend-ip --global
```

### Step 2: Create Google-Managed SSL Certificate

```bash
# Replace yourdomain.com with your actual domain
gcloud compute ssl-certificates create churn-risk-frontend-ssl \
  --domains=yourdomain.com,www.yourdomain.com \
  --global
```

**Note**: The certificate will show as `PROVISIONING` initially. Google needs to verify domain ownership via DNS, which can take 10-60 minutes.

Check status:
```bash
gcloud compute ssl-certificates describe churn-risk-frontend-ssl --global
```

Look for:
```
status: ACTIVE
```

If it shows `FAILED_NOT_VISIBLE`, your DNS hasn't propagated yet. Wait and check again.

---

## Phase 2: Update Load Balancer for HTTPS

### Step 3: Create HTTPS Target Proxy

```bash
# Get the URL map name
gcloud compute url-maps describe churn-risk-frontend-lb --global

# Create HTTPS target proxy
gcloud compute target-https-proxies create churn-risk-frontend-https-proxy \
  --ssl-certificates=churn-risk-frontend-ssl \
  --url-map=churn-risk-frontend-lb \
  --global
```

### Step 4: Create HTTPS Forwarding Rule

```bash
# Add HTTPS forwarding rule using your existing IP
gcloud compute forwarding-rules create churn-risk-frontend-https-rule \
  --address=churn-risk-frontend-ip \
  --target-https-proxy=churn-risk-frontend-https-proxy \
  --global \
  --ports=443
```

### Step 5: Set Up HTTP to HTTPS Redirect

Create a URL map for redirecting HTTP to HTTPS:

```bash
# Create a simple redirect configuration
cat > /tmp/redirect-config.yaml << 'EOF'
kind: compute#urlMap
name: churn-risk-frontend-redirect
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
EOF

# Create the redirect URL map
gcloud compute url-maps import churn-risk-frontend-redirect \
  --source=/tmp/redirect-config.yaml \
  --global
```

Update the HTTP target proxy to use the redirect:

```bash
# Update existing HTTP proxy to redirect
gcloud compute target-http-proxies update churn-risk-frontend-http-proxy \
  --url-map=churn-risk-frontend-redirect \
  --global
```

**Wait**: The redirect won't work until we configure the backend properly.

---

## Phase 3: Update Application Configuration

### Step 6: Update Frontend Environment Variables

Edit `frontend/.env.production`:

```bash
# Before
NUXT_PUBLIC_API_BASE=https://churn-risk-api-461448724047.us-east1.run.app

# After (if keeping backend on Cloud Run URL)
NUXT_PUBLIC_API_BASE=https://churn-risk-api-461448724047.us-east1.run.app
```

**Note**: Backend URL stays the same unless you want to add a custom domain for the API too.

### Step 7: Update Backend CORS Configuration

```bash
# Update Cloud Run service to allow your new domain
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --set-env-vars="CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
```

### Step 8: Update Firebase Authorized Domains

1. Go to Firebase Console: https://console.firebase.google.com/

2. Select your project: `churn-risk`

3. Go to **Authentication** → **Settings** → **Authorized domains**

4. Click **Add domain**

5. Add both:
   - `yourdomain.com`
   - `www.yourdomain.com`

### Step 9: Update HubSpot OAuth Redirect URLs

Update the HubSpot app configuration:

Edit `hs-churn-risk/src/app/app-hsmeta.json`:

```json
"redirectUrls": [
  "http://localhost:3000",
  "http://localhost:8000/api/v1/integrations/hubspot/callback",
  "https://churn-risk-api-461448724047.us-east1.run.app/api/v1/integrations/hubspot/callback",
  "https://yourdomain.com",
  "https://www.yourdomain.com"
]
```

Upload the updated configuration:

```bash
cd hs-churn-risk
hs project upload
```

---

## Phase 4: Rebuild and Deploy Frontend

### Step 10: Rebuild with New Domain

```bash
cd frontend

# Clean previous build
rm -rf .nuxt .output

# Build with production config
npm run generate

# Deploy to Cloud Storage
gsutil -m rsync -R -d .output/public/ gs://churn-risk-frontend-prod/

# Invalidate CDN cache
gcloud compute url-maps invalidate-cdn-cache churn-risk-frontend-lb --path="/*"
```

---

## Phase 5: Testing

### Step 11: Verify DNS Propagation

```bash
# Check if domain resolves to your IP
dig yourdomain.com
dig www.yourdomain.com

# Should show:
# ANSWER SECTION:
# yourdomain.com. 3600 IN A 136.110.172.10
```

### Step 12: Check SSL Certificate Status

```bash
gcloud compute ssl-certificates describe churn-risk-frontend-ssl --global
```

Should show:
```
status: ACTIVE
domainStatus:
  yourdomain.com: ACTIVE
  www.yourdomain.com: ACTIVE
```

If it shows `PROVISIONING`, wait 10-30 minutes and check again.

### Step 13: Test HTTPS Access

1. Visit: `https://yourdomain.com`
   - Should load with green padlock icon
   - Should show your landing page

2. Visit: `http://yourdomain.com`
   - Should redirect to `https://yourdomain.com`

3. Test login:
   - Register new account
   - Login
   - Connect to HubSpot OAuth
   - Import tickets

### Step 14: Verify Backend API Calls

Open browser DevTools (Network tab) and check:
- API calls to backend should succeed
- CORS headers should be present
- No CORS errors in console

---

## Phase 6: Update Documentation

### Step 15: Update Production URLs

Update these files with your new domain:

**README.md**:
```markdown
**Production URLs**:
- Frontend: https://yourdomain.com
- Backend API: https://churn-risk-api-461448724047.us-east1.run.app
```

**CLAUDE.md**:
```markdown
- **Frontend**: https://yourdomain.com
- **Backend**: https://churn-risk-api-461448724047.us-east1.run.app
```

**docs/operations/gcp-daily-operations.md**:
```markdown
| **Frontend (User UI)** | https://yourdomain.com |
```

---

## Troubleshooting

### Certificate stuck in PROVISIONING

**Symptom**: `gcloud compute ssl-certificates describe` shows `PROVISIONING` for 1+ hours

**Fixes**:
1. Verify DNS is correct: `dig yourdomain.com` should show `136.110.172.10`
2. Check domain has propagated globally: https://www.whatsmydns.net/
3. Wait 24-48 hours (rare, but can happen)
4. If still stuck, delete and recreate certificate

### "This site can't be reached"

**Symptom**: Domain doesn't load at all

**Fixes**:
1. Check DNS propagation (can take 1-48 hours)
2. Verify A records point to `136.110.172.10`
3. Try from different network/device (DNS caching)

### "Not Secure" Warning

**Symptom**: HTTPS loads but shows "Not Secure"

**Fixes**:
1. Certificate not active yet - check status
2. Mixed content (HTTP resources on HTTPS page) - check browser console
3. Certificate doesn't include domain - check certificate domains

### CORS Errors After Domain Change

**Symptom**: API calls fail with CORS errors

**Fixes**:
1. Verify `CORS_ORIGINS` includes new domain
2. Check backend deployment updated
3. Clear browser cache
4. Test in incognito window

### Firebase Auth Not Working

**Symptom**: "auth/unauthorized-domain" error

**Fixes**:
1. Add domain to Firebase authorized domains
2. Wait 5-10 minutes for Firebase to update
3. Clear browser cache / try incognito

---

## Optional: Add Custom Domain for Backend API

If you want `api.yourdomain.com` instead of the Cloud Run URL:

1. Add DNS record:
   - Type: `CNAME`
   - Name: `api`
   - Value: `ghs.googlehosted.com`

2. Map domain in Cloud Run:
   ```bash
   gcloud run domain-mappings create \
     --service=churn-risk-api \
     --domain=api.yourdomain.com \
     --region=us-east1
   ```

3. Update frontend `.env.production`:
   ```
   NUXT_PUBLIC_API_BASE=https://api.yourdomain.com
   ```

---

## Cost Impact

**Before HTTPS**:
- Load Balancer forwarding rules: ~$0.025/hour = ~$18/month
- Cloud CDN: Minimal (based on traffic)

**After HTTPS**:
- Same costs (SSL certificate is FREE)
- One additional forwarding rule for HTTPS: ~$0.025/hour = ~$18/month

**Total additional cost**: ~$18/month for HTTPS forwarding rule

**Note**: Domain registration ($12-15/year) is separate.

---

## Summary

After completing these steps:
- ✅ Custom domain with HTTPS
- ✅ Free Google-managed SSL certificate
- ✅ HTTP → HTTPS automatic redirect
- ✅ Updated Firebase and HubSpot OAuth
- ✅ Full production setup

**Next**: Monitor certificate auto-renewal (Google handles this automatically, no action needed).

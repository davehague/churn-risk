# 12 - Custom Domain Setup (Optional)

**Estimated Time:** 20-30 minutes
**Cost:** $12/year (domain registration)
**Prerequisites:** Guides 01-10 completed

---

## Overview

Map your Cloud Run service to a custom domain with automatic SSL certificates.

**What You'll Set Up:**
- Custom domain (e.g., api.churnrisk.com)
- Automatic SSL/TLS certificate
- DNS configuration
- Subdomain routing

**Result:** Your API accessible at `https://api.yourdomain.com`

---

## Step 1: Domain Prerequisites

### 1.1 Domain Requirements

You need to:
- Own a domain (or register one)
- Have access to DNS settings

**Popular registrars:**
- Google Domains
- Namecheap
- GoDaddy
- Cloudflare

### 1.2 Choose Subdomain

**Recommended structure:**
- `api.yourdomain.com` → Backend API
- `app.yourdomain.com` → Frontend (future)
- `www.yourdomain.com` → Marketing site (future)

**For this guide:** We'll use `api.yourdomain.com`

---

## Step 2: Verify Domain Ownership

### 2.1 Add Domain to Cloud Run

```bash
gcloud run domain-mappings create \
  --service=churn-risk-api \
  --domain=api.yourdomain.com \
  --region=us-central1
```

**Expected output:**
```
Deploying domain mapping...
Waiting for certificate provisioning. You must configure your DNS records for certificate issuance to begin.
```

### 2.2 Get DNS Records to Add

```bash
gcloud run domain-mappings describe \
  --domain=api.yourdomain.com \
  --region=us-central1
```

**Will show DNS records you need to add:**
```yaml
status:
  resourceRecords:
  - name: api.yourdomain.com
    type: A
    rr Data: 216.239.32.21
  - name: api.yourdomain.com
    type: AAAA
    rrData: 2001:4860:4802:32::15
```

**Save these records** - you'll add them to your DNS.

---

## Step 3: Configure DNS

### 3.1 Add DNS Records

**Method depends on your registrar:**

**Example: Google Domains**

1. Go to: https://domains.google.com
2. Click on your domain
3. Go to "DNS" tab
4. Add Custom Records:

```
Name:  api
Type:  A
TTL:   1h
Data:  216.239.32.21

Name:  api
Type:  AAAA
TTL:   1h
Data:  2001:4860:4802:32::15
```

**Example: Cloudflare**

1. Dashboard → DNS
2. Add records as above
3. **Important:** Set proxy status to "DNS only" (not proxied)

**Example: Namecheap / GoDaddy**

1. Advanced DNS settings
2. Add A and AAAA records as shown

### 3.2 Verify DNS Propagation

```bash
# Check A record
dig api.yourdomain.com A

# Check AAAA record (IPv6)
dig api.yourdomain.com AAAA
```

**Wait for DNS to propagate:** 5 minutes to 48 hours (usually < 1 hour)

---

## Step 4: Wait for SSL Certificate

### 4.1 Check Certificate Status

```bash
gcloud run domain-mappings describe \
  --domain=api.yourdomain.com \
  --region=us-central1 \
  --format="value(status.conditions[0].message)"
```

**Statuses:**
- "Certificate provisioning..." - Still working
- "Ready" - Certificate issued and active

**Usually takes:** 15 minutes after DNS propagates

### 4.2 Monitor Certificate Progress

```bash
# Check every few minutes
watch -n 60 'gcloud run domain-mappings describe --domain=api.yourdomain.com --region=us-central1 --format="value(status.conditions[0].status)"'
```

**When status shows "True"** - Certificate is ready!

---

## Step 5: Update Application Configuration

### 5.1 Update CORS Origins

```bash
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --update-env-vars="CORS_ORIGINS=https://api.yourdomain.com,http://localhost:3000"
```

### 5.2 Update HubSpot OAuth Redirect URI

**Edit `hs-churn-risk/public-app.json`:**

```json
{
  "redirectUrls": [
    "http://localhost:8000/api/v1/integrations/hubspot/callback",
    "https://api.yourdomain.com/api/v1/integrations/hubspot/callback"
  ]
}
```

**Upload:**
```bash
cd hs-churn-risk
hs project upload
```

### 5.3 Update Environment Variables

```bash
gcloud run services update churn-risk-api \
  --region=us-central1 \
  --update-env-vars="HUBSPOT_REDIRECT_URI=https://api.yourdomain.com/api/v1/integrations/hubspot/callback"
```

---

## Step 6: Test Custom Domain

### 6.1 Test HTTPS

```bash
curl https://api.yourdomain.com/health
```

**Expected:**
```json
{"status":"healthy","environment":"production"}
```

### 6.2 Test SSL Certificate

```bash
curl -vI https://api.yourdomain.com/health 2>&1 | grep -E "SSL|certificate"
```

**Should show:** Valid Google-managed certificate

### 6.3 Test in Browser

Open: `https://api.yourdomain.com/api/v1/docs`

**Should show:**
- Valid SSL (lock icon in browser)
- No certificate warnings
- Swagger UI loads

---

## Step 7: Update Documentation

### 7.1 Update README

```markdown
## API Endpoints

- Production: https://api.yourdomain.com
- API Docs: https://api.yourdomain.com/api/v1/docs
- Health Check: https://api.yourdomain.com/health
```

### 7.2 Update Frontend Configuration

If you have a frontend:

```bash
# frontend/.env.production
NUXT_PUBLIC_API_BASE=https://api.yourdomain.com
```

---

## Optional: Redirect .run.app to Custom Domain

### 8.1 Keep Both URLs Active

By default, both work:
- `https://churn-risk-api-xyz.run.app` ✅
- `https://api.yourdomain.com` ✅

### 8.2 Force Custom Domain Only (Optional)

Add middleware to redirect:

```python
# In main.py
from fastapi import Request
from fastapi.responses import RedirectResponse

@app.middleware("http")
async def redirect_to_custom_domain(request: Request, call_next):
    host = request.headers.get("host", "")
    
    # If accessed via .run.app, redirect to custom domain
    if host.endswith(".run.app"):
        custom_url = f"https://api.yourdomain.com{request.url.path}"
        if request.url.query:
            custom_url += f"?{request.url.query}"
        return RedirectResponse(url=custom_url, status_code=301)
    
    return await call_next(request)
```

---

## Troubleshooting

### Problem: "Certificate provisioning failed"

**Causes:**
- DNS records incorrect
- DNS not propagated yet
- Domain ownership not verified

**Solutions:**
```bash
# Verify DNS records
dig api.yourdomain.com A

# Check domain mapping status
gcloud run domain-mappings describe --domain=api.yourdomain.com --region=us-central1

# Delete and recreate if needed
gcloud run domain-mappings delete --domain=api.yourdomain.com --region=us-central1
# Wait 5 minutes, then recreate
```

### Problem: DNS not propagating

**Solutions:**
- Wait longer (can take up to 48 hours)
- Check authoritative nameservers: `dig api.yourdomain.com +trace`
- Clear local DNS cache: `sudo dscacheutil -flushcache` (macOS)
- Try different DNS server: `dig @8.8.8.8 api.yourdomain.com`

### Problem: "This site can't be reached"

**Solutions:**
- Verify A and AAAA records are correct
- Check Cloud Run service is running
- Wait for DNS propagation
- Try from different network/device

---

## Custom Domain Best Practices

**Do:**
- ✅ Use subdomains (api.domain.com) not root (domain.com)
- ✅ Configure both A and AAAA records (IPv4 and IPv6)
- ✅ Use managed certificates (automatic renewal)
- ✅ Update all OAuth redirect URIs
- ✅ Test from multiple locations/networks

**Don't:**
- ❌ Use root domain for API (use subdomain)
- ❌ Forget to update CORS origins
- ❌ Delete domain mappings while certificate is provisioning
- ❌ Use self-signed certificates (Google provides free ones)

---

## Costs

**Domain registration:** $12-15/year (domain name)
**SSL certificate:** $0 (Google provides free)
**Cloud Run:** No additional cost

**Total added cost:** ~$12/year for domain only

---

## What You've Accomplished

✅ Configured custom domain for Cloud Run
✅ Set up automatic SSL certificate
✅ Updated DNS records
✅ Updated OAuth redirect URIs
✅ Tested HTTPS on custom domain
✅ Professional API URL

---

## Next Steps

**→ Next:** [13 - Troubleshooting Guide](13-troubleshooting.md)

---

## Additional Resources

- [Cloud Run Custom Domains](https://cloud.google.com/run/docs/mapping-custom-domains)
- [DNS Configuration](https://cloud.google.com/dns/docs)
- [Managed SSL Certificates](https://cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs)

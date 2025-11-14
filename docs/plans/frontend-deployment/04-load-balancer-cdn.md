# Guide 04: Setup Load Balancer & CDN

**Estimated Time:** 20 minutes
**Prerequisites:** Guide 03 completed (bucket created and files uploaded)

---

## Overview

Add a Load Balancer with Cloud CDN to serve your site globally with HTTPS and edge caching.

**What you'll get:**
- 🌍 Global edge caching (faster worldwide)
- 🔒 HTTPS automatically
- 🚀 < 100ms latency from CDN edges
- 💰 Reduced costs (CDN caching reduces origin requests)

---

## Architecture

**Before (Direct Cloud Storage):**
```
User (Japan) → US Storage Bucket (200-300ms)
```

**After (Load Balancer + CDN):**
```
User (Japan) → CDN Edge (Tokyo, 10-20ms) → US Storage Bucket
```

---

## Step 1: Reserve Static IP Address

Create a global static IP for your Load Balancer:

```bash
# Reserve a global static IP
gcloud compute addresses create churn-risk-frontend-ip \
  --global \
  --ip-version IPV4

# Get the IP address
gcloud compute addresses describe churn-risk-frontend-ip \
  --global \
  --format="get(address)"

# Save the IP
export FRONTEND_IP=$(gcloud compute addresses describe churn-risk-frontend-ip --global --format="get(address)")
echo "Frontend IP: $FRONTEND_IP"
```

**Expected output:**
```
Created [https://www.googleapis.com/compute/v1/projects/churn-risk-app/global/addresses/churn-risk-frontend-ip].
34.120.XXX.XXX
```

---

## Step 2: Create Backend Bucket

A "backend bucket" connects your Cloud Storage bucket to the Load Balancer:

```bash
# Load bucket name (from Guide 03)
export BUCKET_NAME="churn-risk-frontend-prod"  # Or load from saved file

# Create backend bucket
gcloud compute backend-buckets create churn-risk-frontend-backend \
  --gcs-bucket-name=$BUCKET_NAME \
  --enable-cdn

# Expected output:
# Created backend bucket [churn-risk-frontend-backend]
```

**Flags:**
- `--gcs-bucket-name` - Your Cloud Storage bucket
- `--enable-cdn` - Enable Cloud CDN (edge caching)

---

## Step 3: Create URL Map

URL map routes requests to the backend:

```bash
# Create URL map
gcloud compute url-maps create churn-risk-frontend-lb \
  --default-backend-bucket=churn-risk-frontend-backend

# Expected output:
# Created URL map [churn-risk-frontend-lb]
```

---

## Step 4: Create SSL Certificate

Get a Google-managed SSL certificate (free):

### Option A: Using Your Own Domain (Recommended if you have one)

```bash
# Replace with your actual domain
export DOMAIN="app.yourdomain.com"

# Create managed certificate
gcloud compute ssl-certificates create churn-risk-frontend-cert \
  --domains=$DOMAIN

# Check certificate status (will be PROVISIONING initially)
gcloud compute ssl-certificates describe churn-risk-frontend-cert

# Note: Certificate will be ACTIVE after you point DNS to the Load Balancer IP
```

### Option B: Self-Signed for Testing (Temporary)

If you don't have a domain yet, skip SSL for now. You can add it later.

```bash
# Skip this step for now
# You'll access via http://FRONTEND_IP instead of https://
```

---

## Step 5: Create Target HTTPS Proxy

```bash
# If you created SSL certificate (Option A)
gcloud compute target-https-proxies create churn-risk-frontend-https-proxy \
  --url-map=churn-risk-frontend-lb \
  --ssl-certificates=churn-risk-frontend-cert

# Expected output:
# Created target HTTPS proxy [churn-risk-frontend-https-proxy]
```

**If you skipped SSL certificate:**
```bash
# Create target HTTP proxy instead (no SSL)
gcloud compute target-http-proxies create churn-risk-frontend-http-proxy \
  --url-map=churn-risk-frontend-lb
```

---

## Step 6: Create Forwarding Rule

This connects your IP address to the proxy:

```bash
# For HTTPS (if you created SSL certificate)
gcloud compute forwarding-rules create churn-risk-frontend-https-rule \
  --global \
  --target-https-proxy=churn-risk-frontend-https-proxy \
  --address=churn-risk-frontend-ip \
  --ports=443

# Expected output:
# Created forwarding rule [churn-risk-frontend-https-rule]
```

**If you're using HTTP only (no SSL):**
```bash
# For HTTP (testing without domain)
gcloud compute forwarding-rules create churn-risk-frontend-http-rule \
  --global \
  --target-http-proxy=churn-risk-frontend-http-proxy \
  --address=churn-risk-frontend-ip \
  --ports=80
```

---

## Step 7: Wait for Load Balancer Provisioning

Load Balancers take 5-10 minutes to fully provision:

```bash
# Check forwarding rule status
gcloud compute forwarding-rules describe churn-risk-frontend-https-rule \
  --global

# Wait until you see "IPAddress" populated
```

**While waiting:**
- ☕ Grab coffee
- 📖 Read about Cloud CDN cache modes
- 🎵 Listen to your favorite song

---

## Step 8: Update DNS (If Using Custom Domain)

Point your domain to the Load Balancer IP:

**In your DNS provider (e.g., Cloudflare, GoDaddy, Namecheap):**
1. Create an `A` record:
   - **Name:** `app` (or `@` for root domain)
   - **Type:** `A`
   - **Value:** `YOUR_FRONTEND_IP` (e.g., 34.120.XXX.XXX)
   - **TTL:** 300 (5 minutes)

2. Wait for DNS propagation (5-30 minutes)

```bash
# Check DNS propagation
dig app.yourdomain.com

# Should show your Load Balancer IP
```

---

## Step 9: Test Load Balancer Access

### If using HTTPS with domain:
```bash
# Test HTTPS access
curl -I https://app.yourdomain.com

# Should see:
# HTTP/2 200
# x-goog-stored-content-length: ... (confirms CDN serving)
```

### If using HTTP only (no domain):
```bash
# Test HTTP access via IP
curl -I http://$FRONTEND_IP

# Should see:
# HTTP/1.1 200 OK
```

---

## Step 10: Verify CDN is Working

Check that Cloud CDN is caching your content:

```bash
# First request (cache MISS)
curl -I https://app.yourdomain.com

# Look for these headers:
# x-goog-stored-content-length: ... (served from Cloud Storage)
# Age: 0 (fresh from origin)

# Second request (cache HIT)
curl -I https://app.yourdomain.com

# Should see:
# Age: 5 (cached for 5 seconds)
# x-cache-lookup: HIT (CDN cache hit)
```

---

## Step 11: Test in Browser

Open your site:

**With domain:**
```
https://app.yourdomain.com
```

**Without domain (using IP):**
```
http://YOUR_FRONTEND_IP
```

Verify:
- [ ] Landing page loads fast
- [ ] CSS/JS loads correctly
- [ ] Can navigate to /login
- [ ] Firebase auth works
- [ ] API calls reach backend
- [ ] HTTPS lock icon (if using SSL)

---

## Step 12: Configure Cache Settings (Optional)

Optimize CDN caching for your static site:

```bash
# Set cache TTL (how long CDN caches files)
gcloud compute backend-buckets update churn-risk-frontend-backend \
  --cache-mode=CACHE_ALL_STATIC \
  --default-ttl=3600 \
  --max-ttl=86400

# Flags:
# --cache-mode=CACHE_ALL_STATIC - Cache all static content
# --default-ttl=3600 - Cache for 1 hour by default
# --max-ttl=86400 - Maximum cache time of 24 hours
```

**Cache modes:**
- `CACHE_ALL_STATIC` - Cache HTML, CSS, JS, images (recommended)
- `FORCE_CACHE_ALL` - Cache everything including API responses (NOT recommended)
- `USE_ORIGIN_HEADERS` - Respect Cache-Control headers from origin

---

## Step 13: Update Backend CORS

Update your backend to allow requests from the new domain:

```bash
# If using custom domain
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="https://app.yourdomain.com"

# If using IP (for testing)
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="http://$FRONTEND_IP"
```

---

## Verification Checklist

Before proceeding, verify:

- [ ] Static IP reserved
- [ ] Backend bucket created with CDN enabled
- [ ] URL map created
- [ ] SSL certificate provisioned (if using domain)
- [ ] Target proxy created
- [ ] Forwarding rule created
- [ ] DNS pointing to Load Balancer IP (if using domain)
- [ ] Site loads via Load Balancer
- [ ] CDN caching working (check `Age` header)
- [ ] HTTPS working (if using SSL)
- [ ] Backend CORS updated

---

## Performance Comparison

### Before (Direct Cloud Storage):
```bash
# Test from your location
time curl -I https://storage.googleapis.com/$BUCKET_NAME/index.html

# Typical: 100-300ms depending on distance from us-east1
```

### After (Load Balancer + CDN):
```bash
# First request (cache miss)
time curl -I https://app.yourdomain.com

# Typical: 100-200ms (first load)

# Second request (cache hit)
time curl -I https://app.yourdomain.com

# Typical: 10-50ms (from CDN edge!)
```

**Improvement:** 2-10x faster for cached content!

---

## Common Issues

### Issue: SSL Certificate Stuck in PROVISIONING

**Symptom:** Certificate status remains PROVISIONING for > 30 minutes

**Solution:**
```bash
# Check certificate status
gcloud compute ssl-certificates describe churn-risk-frontend-cert

# Common causes:
# 1. DNS not pointing to Load Balancer IP yet
# 2. DNS propagation not complete
# 3. Certificate validation pending

# Verify DNS is correct
dig app.yourdomain.com
# Should show your Load Balancer IP

# Wait up to 24 hours for Google to provision certificate
# In the meantime, use HTTP (port 80) for testing
```

### Issue: 404 Not Found via Load Balancer

**Symptom:** Load Balancer returns 404 but direct bucket access works

**Solution:**
```bash
# Verify backend bucket configuration
gcloud compute backend-buckets describe churn-risk-frontend-backend

# Check bucket name is correct
# Should show: bucketName: churn-risk-frontend-prod

# Verify URL map
gcloud compute url-maps describe churn-risk-frontend-lb

# Test backend bucket directly
curl -I https://storage.googleapis.com/$BUCKET_NAME/index.html
```

### Issue: CDN Not Caching

**Symptom:** `Age` header always shows 0

**Solution:**
```bash
# Check CDN is enabled
gcloud compute backend-buckets describe churn-risk-frontend-backend \
  --format="get(enableCdn)"
# Should show: True

# Update cache mode
gcloud compute backend-buckets update churn-risk-frontend-backend \
  --cache-mode=CACHE_ALL_STATIC

# Invalidate CDN cache to test
gcloud compute url-maps invalidate-cdn-cache churn-risk-frontend-lb \
  --path="/*"
```

### Issue: CORS Errors After Load Balancer

**Symptom:** API calls fail with CORS error

**Solution:**
```bash
# Update backend CORS to include new domain
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="https://app.yourdomain.com,https://storage.googleapis.com"

# Test from browser console
fetch('https://churn-risk-api-461448724047.us-east1.run.app/health')
  .then(r => r.json())
  .then(console.log)
```

---

## Cost Estimate

**Load Balancer + CDN Monthly Costs:**
```
Forwarding rules (1 rule):           $0.60/month
Cloud CDN (1,000 requests/day):      $0.50/month
Data egress (1GB/month):             $0.10/month
SSL certificate (Google-managed):    $0 (free!)
TOTAL:                               ~$1.20/month
```

**With 10,000 daily users:**
```
Forwarding rules:                    $0.60/month
Cloud CDN (300K requests/month):     $2.00/month
Data egress (10GB/month):            $1.00/month
SSL certificate:                     $0
TOTAL:                               ~$3.60/month
```

---

## Next Steps

Your frontend is now globally accessible with CDN and HTTPS!

**→ Proceed to Guide 05: Setup CI/CD Pipeline**

This will automate deployments when you push to GitHub.

---

## Reference

- **Load Balancer Docs:** https://cloud.google.com/load-balancing/docs/https
- **Cloud CDN:** https://cloud.google.com/cdn/docs
- **SSL Certificates:** https://cloud.google.com/load-balancing/docs/ssl-certificates

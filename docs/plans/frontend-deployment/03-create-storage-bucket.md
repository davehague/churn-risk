# Guide 03: Create Cloud Storage Bucket

**Estimated Time:** 10 minutes
**Prerequisites:** Guide 02 completed (static build tested)

---

## Overview

Create a Cloud Storage bucket to host your static frontend files.

---

## Step 1: Choose Bucket Name

Bucket names must be globally unique across ALL of GCP.

**Naming rules:**
- Lowercase only
- Hyphens allowed
- No underscores
- 3-63 characters
- Must be unique across all GCP

**Recommended format:** `churn-risk-frontend-prod`

```bash
# Set bucket name (change if needed)
export BUCKET_NAME="churn-risk-frontend-prod"

# Verify it's set
echo $BUCKET_NAME
```

---

## Step 2: Check if Name is Available

```bash
# Try to get bucket info (should fail if available)
gsutil ls gs://$BUCKET_NAME 2>&1

# Expected output if available:
# BucketNotFoundException: 404 gs://churn-risk-frontend-prod bucket does not exist.

# If bucket exists:
# Choose a different name (add random suffix)
export BUCKET_NAME="churn-risk-frontend-prod-$(date +%s)"
```

---

## Step 3: Create the Bucket

```bash
# Create bucket in us-east1 (same region as your backend)
gsutil mb -l us-east1 -c STANDARD gs://$BUCKET_NAME

# Expected output:
# Creating gs://churn-risk-frontend-prod/...
```

**Flags explained:**
- `-l us-east1` - Location (same as backend for lower latency)
- `-c STANDARD` - Storage class (default, good for static sites)

**Storage classes:**
- `STANDARD` - Frequent access (recommended for web apps)
- `NEARLINE` - Monthly access (cheaper, slower)
- `COLDLINE` - Yearly access (archives)

---

## Step 4: Configure Bucket for Website Hosting

```bash
# Set index and error pages
gsutil web set -m index.html -e 404.html gs://$BUCKET_NAME

# Expected output:
# Setting website config on gs://churn-risk-frontend-prod/...
```

**What this does:**
- `-m index.html` - Main page (served for directory URLs)
- `-e 404.html` - Error page (served for missing files)

---

## Step 5: Make Bucket Publicly Readable

Your static site needs to be accessible to the internet:

```bash
# Grant public read access to all objects
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Expected output:
# Updated IAM policy for bucket [churn-risk-frontend-prod]
```

**What this does:**
- `allUsers` - Anyone on the internet
- `objectViewer` - Can read objects (not write/delete)

**Security note:** This is safe for public websites. Files are read-only.

---

## Step 6: Verify Bucket Configuration

```bash
# Check bucket exists
gsutil ls gs://$BUCKET_NAME

# Check bucket metadata
gsutil ls -L -b gs://$BUCKET_NAME

# Should show:
# - Location: US-EAST1
# - Storage class: STANDARD
# - Public access: allUsers has READER permission
```

---

## Step 7: Upload Test File

Test that uploads work:

```bash
# Create test file
echo "<h1>Test</h1>" > test.html

# Upload to bucket
gsutil cp test.html gs://$BUCKET_NAME/

# Verify upload
gsutil ls gs://$BUCKET_NAME/test.html

# Test public access
curl https://storage.googleapis.com/$BUCKET_NAME/test.html

# Should return: <h1>Test</h1>
```

---

## Step 8: Deploy Your Static Site

Now upload your actual static files:

```bash
cd frontend

# Ensure static files exist
ls .output/public/

# Upload all files to bucket
gsutil -m rsync -R -d .output/public/ gs://$BUCKET_NAME/

# Expected output:
# Building synchronization state...
# Starting synchronization...
# Copying file://index.html...
# Copying file://404.html...
# Copying file://login/index.html...
# ...
```

**Flags explained:**
- `-m` - Multi-threaded (faster uploads)
- `-R` - Recursive (upload subdirectories)
- `-d` - Delete remote files not in source (clean sync)

---

## Step 9: Verify Deployment

Check that files were uploaded:

```bash
# List all files in bucket
gsutil ls -r gs://$BUCKET_NAME/

# Should see:
# gs://churn-risk-frontend-prod/index.html
# gs://churn-risk-frontend-prod/login/index.html
# gs://churn-risk-frontend-prod/register/index.html
# gs://churn-risk-frontend-prod/dashboard/index.html
# gs://churn-risk-frontend-prod/404.html
# gs://churn-risk-frontend-prod/_nuxt/...

# Check file count
gsutil ls -r gs://$BUCKET_NAME/ | wc -l
# Should be 20-50 files typically
```

---

## Step 10: Test Public Access

```bash
# Test landing page
curl https://storage.googleapis.com/$BUCKET_NAME/index.html | head -20

# Test login page
curl https://storage.googleapis.com/$BUCKET_NAME/login/index.html | head -20

# Test 404 page
curl https://storage.googleapis.com/$BUCKET_NAME/404.html | head -20

# All should return HTML content
```

---

## Step 11: Test in Browser

Open your site in a browser:

```bash
# Get the public URL
echo "https://storage.googleapis.com/$BUCKET_NAME/index.html"
```

Visit the URL and verify:
- [ ] Landing page loads
- [ ] CSS styling works
- [ ] JavaScript loads
- [ ] Can navigate to /login
- [ ] Firebase auth works
- [ ] API calls reach backend

**Note:** Direct access via storage.googleapis.com is slow. We'll add CDN next.

---

## Step 12: Check Costs

View your storage costs:

```bash
# Get bucket size
gsutil du -sh gs://$BUCKET_NAME/

# Typical size: 1-3 MB for Nuxt app

# Check cost estimate
# Storage: $0.02/GB/month in us-east1
# For 3 MB: ~$0.0006/month (essentially free)
```

---

## Verification Checklist

Before proceeding, verify:

- [ ] Bucket created successfully
- [ ] Bucket is publicly readable (`allUsers:objectViewer`)
- [ ] Website configuration set (`index.html`, `404.html`)
- [ ] All static files uploaded
- [ ] Public URL works in browser
- [ ] App loads and functions correctly
- [ ] API calls reach production backend

---

## Common Issues

### Issue: Bucket Name Already Exists

**Symptom:** `BucketAlreadyExists: 409 bucket already exists`

**Solution:**
```bash
# Use a unique suffix
export BUCKET_NAME="churn-risk-frontend-prod-$(openssl rand -hex 4)"
echo "New bucket name: $BUCKET_NAME"

# Re-run create command
gsutil mb -l us-east1 -c STANDARD gs://$BUCKET_NAME
```

### Issue: Permission Denied

**Symptom:** `AccessDeniedException: 403`

**Solution:**
```bash
# Verify you're authenticated
gcloud auth list

# Verify project is set
gcloud config get-value project

# Re-authenticate if needed
gcloud auth login
```

### Issue: Files Not Uploading

**Symptom:** `rsync` fails or hangs

**Solution:**
```bash
# Check .output/public exists
ls -la frontend/.output/public/

# Try single file upload first
gsutil cp frontend/.output/public/index.html gs://$BUCKET_NAME/

# If that works, try rsync again
gsutil -m rsync -R frontend/.output/public/ gs://$BUCKET_NAME/
```

### Issue: 404 When Accessing Site

**Symptom:** Browser shows "Not Found"

**Solution:**
```bash
# Check file exists in bucket
gsutil ls gs://$BUCKET_NAME/index.html

# Verify public access
gsutil iam get gs://$BUCKET_NAME | grep allUsers

# Re-apply public access if needed
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
```

### Issue: CSS/JS Not Loading

**Symptom:** Page loads but looks broken

**Solution:**
```bash
# Check _nuxt directory was uploaded
gsutil ls gs://$BUCKET_NAME/_nuxt/

# Verify all files uploaded
gsutil ls -r gs://$BUCKET_NAME/ | grep -c "\.js$"
# Should see several JS files

# Re-sync if files missing
gsutil -m rsync -R -d frontend/.output/public/ gs://$BUCKET_NAME/
```

---

## Cleanup Script (If Needed)

To delete the bucket and start over:

```bash
# ⚠️ WARNING: This deletes ALL files in the bucket!

# Delete all objects
gsutil -m rm -r gs://$BUCKET_NAME/**

# Delete bucket
gsutil rb gs://$BUCKET_NAME

# Expected output:
# Removing gs://churn-risk-frontend-prod/...
```

---

## Save Bucket Name for Later

Save the bucket name for use in later guides:

```bash
# Save to file
echo "export BUCKET_NAME=$BUCKET_NAME" >> ~/.zshrc  # or ~/.bashrc

# Or create a project-specific file
echo "export BUCKET_NAME=$BUCKET_NAME" > frontend/.bucket-name

# Load in future sessions:
source frontend/.bucket-name
```

---

## Performance Note

**Current access:** `https://storage.googleapis.com/BUCKET_NAME/`
- ✅ Works
- ⚠️ Slower (no CDN)
- ⚠️ Not optimized

**After Load Balancer + CDN (next guide):** `https://your-domain.com/`
- ✅ Fast (CDN edge caching)
- ✅ HTTPS automatic
- ✅ Custom domain support

---

## Next Steps

Your static site is now hosted on Cloud Storage! But it's slow without CDN.

**→ Proceed to Guide 04: Setup Load Balancer & CDN**

This will add global CDN caching and HTTPS support.

---

## Reference

- **Cloud Storage Web Hosting:** https://cloud.google.com/storage/docs/hosting-static-website
- **gsutil rsync:** https://cloud.google.com/storage/docs/gsutil/commands/rsync
- **Bucket Naming:** https://cloud.google.com/storage/docs/naming-buckets

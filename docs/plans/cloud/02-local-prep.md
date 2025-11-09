# 02 - Local Environment Prep - COMPLETE!

Updated gcloud, installed cloud-sql-proxy, set region.  Rest was already set

**Estimated Time:** 10-15 minutes
**Prerequisites:** Guide 01 completed (GCP account created)

---

## Overview

In this guide, you'll set up your local machine to interact with Google Cloud Platform. This involves:
- Updating gcloud CLI
- Authenticating with your new GCP account
- Setting default project and region
- Verifying access

---

## Step 1: Update gcloud CLI

You mentioned you already have gcloud installed. Let's make sure it's up to date.

### 1.1 Check Current Version

```bash
gcloud version
```

**Expected output:**
```
Google Cloud SDK 456.0.0  # (or higher - latest is fine)
```

### 1.2 Update Components

```bash
gcloud components update
```

This will:
- Update core gcloud components
- Update gcloud CLI itself
- Takes 2-3 minutes

**If you get permission errors:**
```bash
# On Mac/Linux, you may need sudo
sudo gcloud components update
```

**Verify update:**
```bash
gcloud version
```

Should show latest version (as of Nov 2025, should be 456.0.0 or higher).

---

## Step 2: Authenticate with GCP

### 2.1 Login to GCP

```bash
gcloud auth login
```

**What happens:**
1. Opens browser window automatically
2. Asks you to choose Google account
3. Click "Allow" to grant gcloud access
4. Returns to terminal with "You are now logged in"

**If browser doesn't open automatically:**
- Copy the URL from terminal
- Open manually in browser
- Complete authentication
- Paste the verification code back in terminal

### 2.2 Set Application Default Credentials

This allows your local Python code to authenticate with GCP:

```bash
gcloud auth application-default login
```

**What happens:**
- Opens another browser window
- Same flow as before (choose account, click Allow)
- Stores credentials locally for your applications

**Why you need this:**
- Allows Cloud SQL Proxy to connect
- Allows Secret Manager client libraries to work
- Enables local testing with GCP services

---

## Step 3: Configure Default Project

### 3.1 Set Your Project

Use the project ID from Guide 01 (e.g., `churn-risk-prod-123456`):

```bash
gcloud config set project YOUR_PROJECT_ID
```

**Example:**
```bash
gcloud config set project churn-risk-prod-123456
```

**Expected output:**
```
Updated property [core/project].
```

### 3.2 Verify Project Set

```bash
gcloud config get-value project
```

**Should output:**
```
churn-risk-prod-123456
```

---

## Step 4: Set Default Region and Zone

### 4.1 Choose a Region

For best performance, choose a region close to:
- Your location (for development)
- Your users (for production)
- Your other services (Firebase, etc.)

**Recommended regions (USA):**
- `us-central1` (Iowa) - lowest cost, good general purpose
- `us-east1` (South Carolina) - good for East Coast
- `us-west1` (Oregon) - good for West Coast

**Recommended regions (Other):**
- `europe-west1` (Belgium) - Europe
- `asia-northeast1` (Tokyo) - Asia Pacific

**For this guide, we'll use `us-central1`** (change if needed for your location):

```bash
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

**Expected output:**
```
Updated property [compute/region].
Updated property [compute/zone].
```

---

## Step 5: Enable Required APIs

If you didn't enable APIs in Guide 01 via console, do it now via CLI:

```bash
# Enable all required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

**Expected output for each:**
```
Operation "operations/..." finished successfully.
```

**Note:** Each API takes 10-30 seconds to enable.

### 5.1 Verify APIs Enabled

```bash
gcloud services list --enabled
```

**Should include:**
```
NAME                              TITLE
run.googleapis.com                Cloud Run API
sqladmin.googleapis.com           Cloud SQL Admin API
secretmanager.googleapis.com      Secret Manager API
cloudbuild.googleapis.com         Cloud Build API
containerregistry.googleapis.com  Container Registry API
```

---

## Step 6: Install Cloud SQL Proxy (For Database Connections)

### 6.1 Download Cloud SQL Proxy

**On macOS (using Homebrew):**
```bash
brew install cloud-sql-proxy
```

**On macOS (manual download):**
```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64

chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/
```

**On Linux:**
```bash
wget https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64 -O cloud-sql-proxy

chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/
```

### 6.2 Verify Installation

```bash
cloud-sql-proxy --version
```

**Expected output:**
```
Cloud SQL Proxy v2.8.0 (or higher)
```

---

## Step 7: Verify Complete Setup

### 7.1 Run Verification Commands

```bash
# 1. Check authentication
gcloud auth list

# Should show your email with * (active)
# Example:
#        Credentialed Accounts
# ACTIVE  ACCOUNT
# *       you@example.com

# 2. Check project
gcloud config get-value project

# Should show: churn-risk-prod-123456

# 3. Check region
gcloud config get-value compute/region

# Should show: us-central1

# 4. Check enabled APIs
gcloud services list --enabled | grep -E "run|sql|secret"

# Should show Cloud Run, Cloud SQL, Secret Manager
```

### 7.2 Checklist

Before proceeding, verify:

- [ ] gcloud CLI updated to latest version
- [ ] Authenticated with `gcloud auth login`
- [ ] Application default credentials set
- [ ] Default project configured
- [ ] Default region/zone set
- [ ] All required APIs enabled
- [ ] Cloud SQL Proxy installed

---

## What You've Accomplished

✅ Updated gcloud CLI to latest version
✅ Authenticated with your GCP account
✅ Configured default project and region
✅ Enabled required GCP APIs
✅ Installed Cloud SQL Proxy for database connections

---

## Costs So Far

**Total spend:** $0
**Credits used:** $0.00
**Remaining credits:** $300.00

*(No charges yet - we haven't created any resources)*

---

## Troubleshooting

### Problem: "gcloud: command not found"

**Solution:**
You need to install gcloud CLI first:

```bash
# On macOS
brew install google-cloud-sdk

# Or download from:
# https://cloud.google.com/sdk/docs/install
```

### Problem: "Permission denied" during gcloud components update

**Solution:**
```bash
# Use sudo
sudo gcloud components update

# Or, if installed via Homebrew, reinstall:
brew upgrade google-cloud-sdk
```

### Problem: Browser doesn't open during auth

**Solution:**
1. Copy the URL shown in terminal
2. Open it manually in your browser
3. Complete authentication
4. Copy verification code from browser
5. Paste it back in terminal

### Problem: "APIs failed to enable"

**Solution:**
- Make sure billing is enabled for your project
- Wait a few minutes after creating project
- Try enabling one API at a time
- Check GCP Console → APIs & Services for errors

### Problem: Cloud SQL Proxy won't install

**Solution:**
- Check internet connection
- Try manual download method
- Verify download URL is correct
- Check system architecture (amd64 vs arm64 for M1/M2 Macs)

---

## Configuration Summary

Save these values - you'll need them:

```
GCP Project ID: ___________________________
Region:         us-central1 (or your choice)
Zone:           us-central1-a
Account Email:  ___________________________
```

---

## Next Steps

With your local environment configured, you're ready to create a production Dockerfile.

**→ Next:** [03 - Dockerfile Creation](03-dockerfile.md)

---

## Additional Resources

- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
- [Cloud SQL Proxy Documentation](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [Regions and Zones](https://cloud.google.com/compute/docs/regions-zones)

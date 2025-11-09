# 01 - GCP Account Setup

**Estimated Time:** 15-20 minutes
**Cost:** $0 (you'll get $300 in free credits)

---

## Overview

In this guide, you'll create a new Google Cloud Platform account and activate the $300 free tier credits. This is a one-time setup.

**What You'll Get:**
- $300 in credits valid for 90 days
- Always-free tier (continues after credits expire)
- Access to all GCP services

**Important:** Use an email address that has never been used for GCP before to qualify for the $300 credits.

---

## Step 1: Create GCP Account

### 1.1 Go to Google Cloud Console

Open your browser and navigate to:
```
https://console.cloud.google.com/
```

### 1.2 Sign In or Create Google Account

**If you have a Google account** (Gmail, Google Workspace):
- Click "Sign in"
- Use an email that has NEVER been used for GCP before

**If you need a new Google account**:
- Click "Create account"
- Follow the prompts to create a new Gmail account
- Verify your email address

**Pro Tip:** Consider using a company email if you have one (e.g., `you@yourcompany.com`) rather than personal Gmail. This looks more professional when applying for startup credits later.

### 1.3 Start Free Trial

You should see a banner: **"Try Google Cloud for free"** or **"Activate Free Trial"**

Click the button to start the free trial.

**If you don't see the banner:**
- Go directly to: https://cloud.google.com/free
- Click "Get started for free"

---

## Step 2: Complete Free Trial Setup

### 2.1 Choose Your Country

- Select your country from the dropdown
- Read and accept the Terms of Service
- Check the box to agree to the terms
- Click "Continue"

### 2.2 Provide Account Information

**Account type:**
- Choose "Individual" (unless you're setting up for a company)

**Name and address:**
- Enter your full legal name
- Provide your billing address
- This information is required for tax purposes

Click "Continue"

### 2.3 Add Payment Method

**Why you need a credit card:**
- Required to verify you're not a bot
- You will NOT be charged unless you explicitly upgrade
- The $300 credits will be used first
- You'll receive warnings before credits run out

**Steps:**
1. Click "Add a payment method"
2. Enter credit card details:
   - Card number
   - Expiration date
   - CVV
   - Billing ZIP code
3. Click "Start my free trial"

**What Happens:**
- Google will charge $1 temporarily (refunded within a few days)
- This verifies your card is valid
- You are NOT enrolled in automatic billing yet

---

## Step 3: Verify Free Trial Activated

### 3.1 Check for Credits

After completing signup, you should see:
```
Free trial status: Active
Credits remaining: $300.00
```

Look in the top-right corner of the GCP Console for the billing indicator.

### 3.2 Verify Billing Account Created

1. In GCP Console, click the navigation menu (☰) in top-left
2. Go to **"Billing"**
3. You should see:
   - Account name: "My Billing Account" (or similar)
   - Status: "Active"
   - Free trial credits: $300.00

**Screenshot checkpoint:** You should see a billing account with $300 credits.

---

## Step 4: Create Your First Project

### 4.1 Understanding GCP Projects

Everything in GCP belongs to a **project**. Think of it as a folder that contains:
- All your services (Cloud Run, Cloud SQL, etc.)
- Billing information
- API access controls
- Team member permissions

### 4.2 Create Project

**Option A: Via Console (Recommended for First Time)**

1. Click the project selector in the top bar (next to "Google Cloud")
2. Click "NEW PROJECT" in the popup
3. Fill in project details:

**Project name:**
```
churn-risk-prod
```
(or choose your own - keep it short, lowercase, with hyphens)

**Project ID:**
- Will auto-generate based on project name
- Must be globally unique
- You can edit it before creating
- Example: `churn-risk-prod-123456`
- **Write this down - you'll need it later**

**Organization:**
- Leave as "No organization" (unless you have a Google Workspace)

4. Click "CREATE"

**Option B: Via gcloud CLI (Optional)**

```bash
# If you prefer command line
gcloud projects create churn-risk-prod-123456 \
    --name="Churn Risk Production"
```

### 4.3 Verify Project Created

1. You should see a notification: "Creating project churn-risk-prod..."
2. After 10-20 seconds: "Project created successfully"
3. The project name should now appear in the top bar

---

## Step 5: Enable Billing for Project

### 5.1 Link Project to Billing Account

1. Go to **Navigation Menu (☰) → Billing**
2. Click "Link a billing account" (if prompted)
3. Select your billing account (should be the one with $300 credits)
4. Click "Set account"

**Verify:**
- Go to **Billing → Account management**
- You should see your project listed under this billing account

### 5.2 Set Budget Alerts (Recommended)

Even though you have $300 credits, set up alerts to avoid surprises:

1. Go to **Billing → Budgets & alerts**
2. Click "CREATE BUDGET"
3. Configure:
   - **Scope:** Select your project
   - **Budget name:** "Free Tier Monitoring"
   - **Budget amount:** $50 per month
   - **Threshold rules:**
     - Alert at 50% ($25)
     - Alert at 80% ($40)
     - Alert at 100% ($50)
4. Click "FINISH"

**What this does:**
- Sends you email alerts if spending exceeds thresholds
- Helps you catch unexpected costs early
- You'll get warnings long before your $300 runs out

---

## Step 6: Enable Required APIs

GCP services are "APIs" that must be enabled before use. Enable the core ones you'll need:

### 6.1 Enable APIs via Console

1. Go to **Navigation Menu (☰) → APIs & Services → Library**

2. Search for and enable each of these APIs:
   - **Cloud Run API** (for backend deployment)
   - **Cloud SQL Admin API** (for PostgreSQL)
   - **Secret Manager API** (for secrets)
   - **Cloud Build API** (for container builds)
   - **Container Registry API** (for storing Docker images)

**For each API:**
1. Search for the API name
2. Click on it
3. Click "ENABLE"
4. Wait for "API enabled" confirmation

### 6.2 Enable APIs via gcloud (Faster)

Alternatively, run these commands (we'll set up gcloud in the next guide):

```bash
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

**Note:** If you haven't set up gcloud yet, you can skip this and do it in the next guide.

---

## Step 7: Verify Setup

### 7.1 Checklist

Before proceeding, verify:

- [ ] GCP account created and signed in
- [ ] Free trial activated ($300 credits visible)
- [ ] Project created (e.g., `churn-risk-prod`)
- [ ] Project ID written down (you'll need this)
- [ ] Billing account linked to project
- [ ] Budget alerts configured
- [ ] Required APIs enabled

### 7.2 Quick Verification Commands

If you've set up gcloud (next guide), verify:

```bash
# Check current project
gcloud config get-value project

# Should output your project ID
# Example: churn-risk-prod-123456

# List enabled APIs
gcloud services list --enabled

# Should include run.googleapis.com, sqladmin.googleapis.com, etc.
```

---

## What You've Accomplished

✅ Created new GCP account
✅ Activated $300 free tier credits (90 days)
✅ Created your first GCP project
✅ Enabled billing with budget alerts
✅ Enabled required APIs for deployment

---

## Costs So Far

**Total spend:** $0
**Credits used:** $0
**Remaining credits:** $300

---

## Troubleshooting

### Problem: "Free trial not available"

**Possible causes:**
- Email address previously used for GCP
- Country not eligible for free trial
- Payment method rejected

**Solutions:**
- Try a different email address
- Use a different credit/debit card
- Check https://cloud.google.com/free for eligible countries

### Problem: "Payment method declined"

**Solutions:**
- Use a different credit/debit card
- Ensure billing address matches card
- Try a different card type (Visa vs Mastercard)
- Contact your bank (sometimes they block Google charges)

### Problem: "Can't create project"

**Solutions:**
- Wait a few minutes after creating account
- Refresh the page
- Try creating via gcloud CLI (next guide)
- Check that billing is properly linked

### Problem: "APIs won't enable"

**Solutions:**
- Make sure billing is linked to project
- Wait a few minutes after creating project
- Try enabling one at a time
- Check quota limits (shouldn't hit them yet)

---

## Next Steps

Now that your GCP account is set up, you're ready to configure your local environment.

**→ Next:** [02 - Local Environment Prep](02-local-prep.md)

---

## Additional Resources

- [GCP Free Tier Documentation](https://cloud.google.com/free)
- [Understanding GCP Projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- [Billing Overview](https://cloud.google.com/billing/docs)
- [API Library](https://console.cloud.google.com/apis/library)

---

**Project ID to Save:** `_______________________` (Write it here for reference)

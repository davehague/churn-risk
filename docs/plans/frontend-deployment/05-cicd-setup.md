# Guide 05: Setup CI/CD Pipeline

**Estimated Time:** 20 minutes
**Prerequisites:** Guide 04 completed (Load Balancer + CDN working)

---

## Overview

Automate frontend deployments using Cloud Build triggered by GitHub pushes.

**What you'll get:**
- 🚀 Auto-deploy on push to `main` branch
- ✅ Build verification before deploying
- 📦 Automatic `nuxt generate` in cloud
- ⚡ Fast deploys (2-3 minutes)

---

## Architecture

**Manual Deployment (Current):**
```
You → npm run generate → gsutil rsync → Cloud Storage
```

**Automated CI/CD (What We're Building):**
```
You → git push main → GitHub → Cloud Build Trigger
                                      ↓
                          1. npm install
                          2. npm run generate
                          3. gsutil rsync → Cloud Storage
                          4. Invalidate CDN cache
```

---

## Step 1: Create cloudbuild.yaml

Create CI/CD configuration for frontend:

```bash
cd frontend

cat > cloudbuild.yaml << 'EOF'
steps:
  # Step 1: Install dependencies
  - name: 'node:18'
    entrypoint: npm
    args: ['install']
    dir: 'frontend'

  # Step 2: Generate static site
  - name: 'node:18'
    entrypoint: npm
    args: ['run', 'generate']
    dir: 'frontend'
    env:
      - 'NUXT_PUBLIC_API_BASE=${_API_BASE}'
      - 'NUXT_PUBLIC_FIREBASE_API_KEY=${_FIREBASE_API_KEY}'
      - 'NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN=${_FIREBASE_AUTH_DOMAIN}'
      - 'NUXT_PUBLIC_FIREBASE_PROJECT_ID=${_FIREBASE_PROJECT_ID}'

  # Step 3: Deploy to Cloud Storage
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: bash
    args:
      - '-c'
      - |
        gsutil -m rsync -R -d frontend/.output/public/ gs://${_BUCKET_NAME}/

  # Step 4: Invalidate CDN cache
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'compute'
      - 'url-maps'
      - 'invalidate-cdn-cache'
      - '${_URL_MAP_NAME}'
      - '--path=/*'
      - '--async'

timeout: '600s'

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'N1_HIGHCPU_8'

substitutions:
  _BUCKET_NAME: 'churn-risk-frontend-prod'
  _URL_MAP_NAME: 'churn-risk-frontend-lb'
  _API_BASE: 'https://churn-risk-api-461448724047.us-east1.run.app'
  _FIREBASE_API_KEY: 'your-api-key'
  _FIREBASE_AUTH_DOMAIN: 'your-project.firebaseapp.com'
  _FIREBASE_PROJECT_ID: 'your-project-id'
EOF
```

**Update the substitutions:**
- `_BUCKET_NAME` - Your bucket name from Guide 03
- `_URL_MAP_NAME` - Your URL map name from Guide 04
- `_API_BASE` - Your production backend URL
- `_FIREBASE_*` - Your Firebase credentials

---

## Step 2: Store Firebase Credentials in Secret Manager

Don't hardcode Firebase credentials in cloudbuild.yaml:

```bash
# Store Firebase API key
echo -n "your-actual-firebase-api-key" | \
  gcloud secrets create frontend-firebase-api-key --data-file=-

# Store Firebase auth domain
echo -n "your-project.firebaseapp.com" | \
  gcloud secrets create frontend-firebase-auth-domain --data-file=-

# Store Firebase project ID
echo -n "your-project-id" | \
  gcloud secrets create frontend-firebase-project-id --data-file=-

# Expected output for each:
# Created version [1] of the secret [frontend-firebase-api-key]
```

---

## Step 3: Update cloudbuild.yaml to Use Secrets

Replace the substitutions section:

```yaml
# In cloudbuild.yaml, update Step 2:
  # Step 2: Generate static site
  - name: 'node:18'
    entrypoint: npm
    args: ['run', 'generate']
    dir: 'frontend'
    secretEnv:
      - 'NUXT_PUBLIC_FIREBASE_API_KEY'
      - 'NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN'
      - 'NUXT_PUBLIC_FIREBASE_PROJECT_ID'
    env:
      - 'NUXT_PUBLIC_API_BASE=${_API_BASE}'

# Add at the bottom (after options section):
availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/frontend-firebase-api-key/versions/latest
      env: 'NUXT_PUBLIC_FIREBASE_API_KEY'
    - versionName: projects/$PROJECT_ID/secrets/frontend-firebase-auth-domain/versions/latest
      env: 'NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN'
    - versionName: projects/$PROJECT_ID/secrets/frontend-firebase-project-id/versions/latest
      env: 'NUXT_PUBLIC_FIREBASE_PROJECT_ID'
```

---

## Step 4: Grant Cloud Build Access to Secrets

```bash
# Get Cloud Build service account email
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
export CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant access to secrets
gcloud secrets add-iam-policy-binding frontend-firebase-api-key \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding frontend-firebase-auth-domain \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding frontend-firebase-project-id \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/secretmanager.secretAccessor"

# Expected output:
# Updated IAM policy for secret [frontend-firebase-api-key]
```

---

## Step 5: Connect GitHub Repository (If Not Already Done)

```bash
# List connected repositories
gcloud builds repositories list --connection=github

# If not connected, create connection
gcloud builds repositories create \
  --connection=github \
  --region=us-east1 \
  --repository=yourusername/churn-risk-app

# Follow prompts to authenticate with GitHub
```

---

## Step 6: Create Build Trigger

```bash
# Create trigger for frontend deployments
gcloud builds triggers create github \
  --name=deploy-frontend \
  --repo-name=churn-risk-app \
  --repo-owner=yourusername \
  --branch-pattern="^main$" \
  --build-config=frontend/cloudbuild.yaml \
  --region=us-east1

# Expected output:
# Created build trigger [deploy-frontend]
```

**Important:** Update `--repo-owner` with your GitHub username.

---

## Step 7: Commit and Push cloudbuild.yaml

```bash
cd frontend

# Stage cloudbuild.yaml
git add cloudbuild.yaml

# Commit
git commit -m "feat: add CI/CD pipeline for frontend deployment"

# Push to main branch
git push origin main
```

---

## Step 8: Monitor Build Progress

```bash
# Watch build logs in real-time
gcloud builds list --ongoing --region=us-east1

# Get latest build ID
export BUILD_ID=$(gcloud builds list --region=us-east1 --limit=1 --format="value(id)")

# Stream logs
gcloud builds log $BUILD_ID --region=us-east1 --stream
```

**Expected output:**
```
Step 1/4: Installing dependencies...
✓ npm install complete
Step 2/4: Generating static site...
✓ nuxt generate complete
Step 3/4: Uploading to Cloud Storage...
✓ gsutil rsync complete
Step 4/4: Invalidating CDN cache...
✓ CDN cache invalidated

SUCCESS
```

---

## Step 9: Verify Deployment

```bash
# Check that build succeeded
gcloud builds describe $BUILD_ID --region=us-east1

# Should see:
# status: SUCCESS

# Test the deployed site
curl -I https://app.yourdomain.com

# Should see fresh content (after CDN cache invalidation)
```

---

## Step 10: Test Automatic Deployment

Make a small change and verify auto-deploy works:

```bash
cd frontend

# Make a visible change
echo "<p>Build version: $(date)</p>" >> pages/index.vue

# Commit and push
git add pages/index.vue
git commit -m "test: verify CI/CD pipeline"
git push origin main

# Watch build trigger automatically
gcloud builds list --region=us-east1 --limit=1

# Wait for build to complete (2-3 minutes)
# Then check your site to see the change
```

---

## Step 11: Setup Build Notifications (Optional)

Get notified when builds fail:

```bash
# Create Pub/Sub topic for build notifications
gcloud pubsub topics create cloud-builds

# Subscribe your email
gcloud pubsub subscriptions create build-notifications \
  --topic=cloud-builds \
  --push-endpoint=mailto:your-email@example.com

# Expected output:
# Created subscription [build-notifications]
```

---

## Verification Checklist

Before considering CI/CD complete, verify:

- [ ] `cloudbuild.yaml` created and committed
- [ ] Firebase credentials stored in Secret Manager
- [ ] Cloud Build has access to secrets
- [ ] GitHub repository connected
- [ ] Build trigger created for `main` branch
- [ ] Initial build succeeded
- [ ] Site deployed automatically
- [ ] CDN cache invalidated
- [ ] Test change triggered auto-deploy
- [ ] Build logs accessible

---

## Common Issues

### Issue: Build Fails at npm install

**Symptom:** `Step 1/4` fails with dependency errors

**Solution:**
```bash
# Check package.json is valid
cd frontend && npm install

# Verify Node version
node --version
# Should be 18+

# Update cloudbuild.yaml to use specific Node version
# Change: 'node:18' to 'node:18.18.0'
```

### Issue: Build Fails at nuxt generate

**Symptom:** `Step 2/4` fails with build errors

**Solution:**
```bash
# Test build locally first
cd frontend
npm run generate

# Check for syntax errors
npm run typecheck

# Common cause: Missing environment variables
# Verify substitutions in cloudbuild.yaml are correct
```

### Issue: Secrets Not Found

**Symptom:** `Step 2/4` fails with "secret not found"

**Solution:**
```bash
# Verify secrets exist
gcloud secrets list | grep frontend-firebase

# Re-create secrets if missing
echo -n "your-value" | \
  gcloud secrets create frontend-firebase-api-key --data-file=-

# Verify Cloud Build has access
gcloud secrets get-iam-policy frontend-firebase-api-key
# Should list cloudbuild service account
```

### Issue: Permission Denied on gsutil rsync

**Symptom:** `Step 3/4` fails with 403 error

**Solution:**
```bash
# Grant Cloud Build write access to bucket
gsutil iam ch \
  "serviceAccount:${CLOUDBUILD_SA}:objectAdmin" \
  gs://${BUCKET_NAME}

# Verify permissions
gsutil iam get gs://${BUCKET_NAME} | grep cloudbuild
```

### Issue: CDN Cache Invalidation Fails

**Symptom:** `Step 4/4` fails with permission error

**Solution:**
```bash
# Grant Cloud Build compute.urlMaps.invalidateCache permission
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/compute.loadBalancerAdmin"

# Re-run build
gcloud builds triggers run deploy-frontend --region=us-east1
```

### Issue: Trigger Doesn't Fire on Push

**Symptom:** Git push doesn't start a build

**Solution:**
```bash
# Verify trigger exists
gcloud builds triggers list --region=us-east1

# Check branch pattern matches
gcloud builds triggers describe deploy-frontend --region=us-east1
# Should show: includedFiles: ['frontend/**']

# Manually trigger to test
gcloud builds triggers run deploy-frontend --region=us-east1
```

---

## Build Time Optimization

**Current build time:** ~3-5 minutes

**Optimize with:**

1. **Cache node_modules:**
```yaml
# Add to cloudbuild.yaml
options:
  volumes:
    - name: 'node_modules'
      path: '/workspace/node_modules'
```

2. **Use faster machine:**
```yaml
# Already set in template
machineType: 'N1_HIGHCPU_8'  # 8 vCPUs
```

3. **Skip CDN invalidation for non-critical builds:**
```yaml
# Only invalidate for production branch
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: bash
  args:
    - '-c'
    - |
      if [ "$BRANCH_NAME" = "main" ]; then
        gcloud compute url-maps invalidate-cdn-cache ${_URL_MAP_NAME} --path=/*
      fi
```

---

## Deployment Flow Diagram

```
Developer → git push main → GitHub
                              ↓
                       Cloud Build Trigger
                              ↓
                    ┌─────────┴─────────┐
                    │                   │
                Step 1               Step 2
            npm install        nuxt generate
                    │                   │
                    └─────────┬─────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │                   │
                Step 3               Step 4
           Upload to GCS      Invalidate CDN
                    │                   │
                    └─────────┬─────────┘
                              ↓
                     Live on Production!
```

---

## Cost Estimate

**Cloud Build Costs:**
```
First 120 build-minutes/day:         Free
After that: $0.003/build-minute

Typical frontend build: 3 minutes
Typical usage (5 builds/day): Free
Heavy usage (50 builds/day): ~$2/month
```

---

## Next Steps

Your CI/CD pipeline is complete! Every push to `main` automatically deploys.

**Optional Next Steps:**
- [Guide 06: Custom Domain Setup](06-custom-domain.md) (if not done)
- [Guide 07: Monitoring & Alerts](07-monitoring.md)
- [Guide 08: Rollback Procedures](08-rollback.md)

---

## Reference

- **Cloud Build Docs:** https://cloud.google.com/build/docs
- **Build Triggers:** https://cloud.google.com/build/docs/automating-builds/create-manage-triggers
- **Secret Manager Integration:** https://cloud.google.com/build/docs/securing-builds/use-secrets

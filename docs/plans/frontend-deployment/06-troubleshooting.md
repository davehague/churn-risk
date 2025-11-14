# Troubleshooting Guide - Frontend Deployment

Common issues and solutions when deploying Nuxt 3 frontend to GCP.

---

## Build Issues

### ❌ npm install Fails in Cloud Build

**Symptom:**
```
Step 1/4: Installing dependencies...
ERROR: npm ERR! code ENOTFOUND
```

**Causes & Solutions:**

1. **package-lock.json out of sync:**
```bash
cd frontend
rm package-lock.json
npm install
git add package-lock.json
git commit -m "fix: regenerate package-lock.json"
git push
```

2. **Node version mismatch:**
```yaml
# In cloudbuild.yaml, specify exact version
- name: 'node:18.18.0'  # Instead of 'node:18'
```

3. **Private npm packages:**
```bash
# Add npm token to Secret Manager
echo -n "your-npm-token" | gcloud secrets create npm-token --data-file=-

# Update cloudbuild.yaml to use it
- name: 'node:18'
  entrypoint: bash
  args:
    - '-c'
    - 'echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > ~/.npmrc && npm install'
  secretEnv: ['NPM_TOKEN']
```

---

### ❌ nuxt generate Fails

**Symptom:**
```
Step 2/4: Generating static site...
ERROR: Cannot find module 'nuxt'
```

**Solution:**
```bash
# Ensure nuxt is in dependencies (not devDependencies)
cd frontend
npm install --save nuxt

# Update package.json
# Move nuxt from devDependencies to dependencies

git add package.json package-lock.json
git commit -m "fix: move nuxt to dependencies"
git push
```

---

### ❌ Environment Variables Not Working

**Symptom:**
- Build succeeds but app connects to wrong API
- Firebase auth fails

**Solution:**

1. **Check cloudbuild.yaml substitutions:**
```yaml
substitutions:
  _API_BASE: 'https://churn-risk-api-461448724047.us-east1.run.app'  # Must be correct!
```

2. **Verify secrets are accessible:**
```bash
# Test secret access
gcloud secrets versions access latest --secret=frontend-firebase-api-key
```

3. **Check built files contain correct values:**
```bash
# After build, check JS bundles
gsutil cat gs://your-bucket/_nuxt/entry.*.js | grep "churn-risk-api"
# Should show your production API URL
```

---

## Deployment Issues

### ❌ 403 Forbidden When Accessing Site

**Symptom:**
```
<Error>
  <Code>AccessDenied</Code>
  <Message>Access denied.</Message>
</Error>
```

**Solution:**
```bash
# Make bucket publicly readable
export BUCKET_NAME="churn-risk-frontend-prod"
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Verify permissions
gsutil iam get gs://$BUCKET_NAME | grep allUsers
# Should see: allUsers with role: roles/storage.objectViewer
```

---

### ❌ 404 Not Found for All Routes

**Symptom:**
- Landing page works
- But /login, /dashboard return 404

**Solution:**

1. **Check website configuration:**
```bash
# Set main and error pages
gsutil web set -m index.html -e 404.html gs://$BUCKET_NAME

# Verify it's set
gsutil web get gs://$BUCKET_NAME
```

2. **Verify files were uploaded:**
```bash
# Check all HTML files exist
gsutil ls gs://$BUCKET_NAME/login/index.html
gsutil ls gs://$BUCKET_NAME/dashboard/index.html
gsutil ls gs://$BUCKET_NAME/register/index.html
```

3. **For SPA routing, use Load Balancer with URL rewrite:**
```bash
# This is handled by the Load Balancer setup in Guide 04
# Direct Cloud Storage access has limitations for SPA routing
```

---

### ❌ Blank Page (White Screen)

**Symptom:**
- Page loads but shows nothing
- Browser console shows errors

**Common Causes:**

1. **JavaScript files not loading:**
```bash
# Check _nuxt directory exists
gsutil ls gs://$BUCKET_NAME/_nuxt/

# Verify JS files are publicly accessible
curl -I https://storage.googleapis.com/$BUCKET_NAME/_nuxt/entry.*.js
# Should return 200 OK
```

2. **Base path issues:**
```javascript
// Check nuxt.config.ts
export default defineNuxtConfig({
  app: {
    baseURL: '/',  // Should be '/' for root domain
  }
})
```

3. **CORS blocking resources:**
```bash
# Update backend CORS
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="https://storage.googleapis.com,https://$BUCKET_NAME.storage.googleapis.com"
```

---

## API Connection Issues

### ❌ CORS Errors in Browser Console

**Symptom:**
```
Access to fetch at 'https://churn-risk-api...run.app/api/v1/me' from origin
'https://your-domain.com' has been blocked by CORS policy
```

**Solution:**

1. **Update backend CORS to include frontend domain:**
```bash
# Get your frontend domain
export FRONTEND_DOMAIN="https://your-domain.com"

# Update backend CORS
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="$FRONTEND_DOMAIN"

# For multiple domains (comma-separated):
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="https://domain1.com,https://domain2.com,https://storage.googleapis.com"
```

2. **Verify CORS in backend logs:**
```bash
# Check if OPTIONS requests are succeeding
gcloud run services logs read churn-risk-api --region=us-east1 --limit=50 | grep OPTIONS
```

---

### ❌ API Returns 401 Unauthorized

**Symptom:**
- Can't login
- All API calls return 401

**Solution:**

1. **Check Firebase auth is initialized:**
```javascript
// Open browser console
console.log('Firebase config:', useRuntimeConfig().public)
// Should show firebaseApiKey, firebaseAuthDomain, firebaseProjectId
```

2. **Verify token is being sent:**
```javascript
// In browser console, on any page
const { idToken } = useAuth()
console.log('ID Token:', idToken.value)
// Should show a JWT token (long string)
```

3. **Check backend can verify tokens:**
```bash
# Test backend health
curl https://churn-risk-api-461448724047.us-east1.run.app/health

# Check backend logs for auth errors
gcloud run services logs read churn-risk-api --region=us-east1 --limit=50 | grep -i "auth\|token\|401"
```

---

## CDN & Load Balancer Issues

### ❌ SSL Certificate Stuck in PROVISIONING

**Symptom:**
```
gcloud compute ssl-certificates describe churn-risk-frontend-cert
status: PROVISIONING
```

**Solution:**

1. **Verify DNS is pointing to Load Balancer:**
```bash
# Get Load Balancer IP
gcloud compute addresses describe churn-risk-frontend-ip --global

# Check DNS
dig your-domain.com
# Should show Load Balancer IP
```

2. **Wait up to 24 hours:**
- Google needs to verify domain ownership
- Certificate provisioning can take time

3. **Check domain authorization:**
```bash
# Ensure domain is authorized in Google Search Console
# Visit: https://search.google.com/search-console
```

4. **Temporarily use HTTP:**
```bash
# While SSL is provisioning, test with HTTP
curl http://YOUR_LOAD_BALANCER_IP
```

---

### ❌ CDN Not Caching (Always Age: 0)

**Symptom:**
```bash
curl -I https://your-domain.com
# Always shows: Age: 0
```

**Solution:**

1. **Verify CDN is enabled:**
```bash
gcloud compute backend-buckets describe churn-risk-frontend-backend
# Should show: enableCdn: true
```

2. **Set cache mode:**
```bash
gcloud compute backend-buckets update churn-risk-frontend-backend \
  --cache-mode=CACHE_ALL_STATIC
```

3. **Check file is cacheable:**
```bash
# Some file types are cached by default (CSS, JS, images)
# HTML files may need explicit cache headers

# Test with a JS file
curl -I https://your-domain.com/_nuxt/entry.*.js
# Should show: Age: > 0 on second request
```

---

## CI/CD Issues

### ❌ Build Trigger Doesn't Fire

**Symptom:**
- Push to GitHub, but no build starts

**Solution:**

1. **Verify trigger is enabled:**
```bash
gcloud builds triggers describe deploy-frontend --region=us-east1
# Should show: disabled: false
```

2. **Check branch pattern:**
```bash
# Trigger should match your branch
gcloud builds triggers describe deploy-frontend --region=us-east1
# Should show: includedFiles: ['frontend/**']
# branchName: main
```

3. **Check GitHub connection:**
```bash
gcloud builds repositories list --connection=github
# Should list your repository
```

4. **Manually trigger to test:**
```bash
gcloud builds triggers run deploy-frontend --region=us-east1 --branch=main
```

---

### ❌ Build Succeeds But Site Doesn't Update

**Symptom:**
- Build shows SUCCESS
- But site still shows old content

**Solution:**

1. **CDN cache needs to be invalidated:**
```bash
# Manually invalidate CDN cache
gcloud compute url-maps invalidate-cdn-cache churn-risk-frontend-lb \
  --path="/*"
```

2. **Check cloudbuild.yaml has invalidation step:**
```yaml
# Step 4 should invalidate CDN
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    - 'compute'
    - 'url-maps'
    - 'invalidate-cdn-cache'
    - 'churn-risk-frontend-lb'
    - '--path=/*'
```

3. **Hard refresh browser:**
- Chrome/Firefox: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or open in incognito mode

---

## Performance Issues

### ⚠️ Slow Initial Load

**Symptom:**
- First page load takes > 2 seconds

**Solutions:**

1. **Check bundle sizes:**
```bash
# List JS bundle sizes
gsutil ls -lh gs://$BUCKET_NAME/_nuxt/*.js

# Aim for:
# - Main bundle: < 300 KB
# - Total JS: < 500 KB
```

2. **Optimize images:**
```bash
# Use WebP format
# Compress images before deploying
# Use responsive images
```

3. **Enable CDN caching:**
```bash
# Already done in Guide 04, but verify
gcloud compute backend-buckets describe churn-risk-frontend-backend \
  --format="get(enableCdn)"
# Should show: True
```

4. **Check CDN hit rate:**
```bash
# View CDN metrics in Cloud Console
# Go to: Network Services → Cloud CDN → Your backend
# Check cache hit rate (should be > 80%)
```

---

## Debugging Checklist

When something's not working:

### 1. Check Build Logs
```bash
gcloud builds list --region=us-east1 --limit=5
gcloud builds log <BUILD_ID> --region=us-east1
```

### 2. Check Deployed Files
```bash
gsutil ls -r gs://$BUCKET_NAME/ | head -20
```

### 3. Check Browser Console
- Open DevTools → Console
- Look for errors (red text)
- Check Network tab for failed requests

### 4. Check Backend Logs
```bash
gcloud run services logs read churn-risk-api --region=us-east1 --limit=50
```

### 5. Test Directly vs Through CDN
```bash
# Direct Cloud Storage access
curl -I https://storage.googleapis.com/$BUCKET_NAME/index.html

# Through Load Balancer + CDN
curl -I https://your-domain.com
```

---

## Quick Fixes

### Reset Everything and Redeploy

```bash
# 1. Clear CDN cache
gcloud compute url-maps invalidate-cdn-cache churn-risk-frontend-lb --path="/*"

# 2. Delete all files from bucket
gsutil -m rm -r gs://$BUCKET_NAME/**

# 3. Rebuild locally
cd frontend
rm -rf .nuxt .output node_modules
npm install
npm run generate

# 4. Re-upload
gsutil -m rsync -R -d .output/public/ gs://$BUCKET_NAME/

# 5. Test
curl -I https://your-domain.com
```

---

## Getting More Help

### View Detailed Logs

**Cloud Build:**
```bash
gcloud builds log <BUILD_ID> --region=us-east1 > build.log
cat build.log | grep -i error
```

**Cloud Storage:**
```bash
gsutil logging get gs://$BUCKET_NAME
```

**Load Balancer:**
```bash
gcloud compute url-maps describe churn-risk-frontend-lb
gcloud compute backend-buckets describe churn-risk-frontend-backend
```

### Cloud Console

- **Cloud Build:** https://console.cloud.google.com/cloud-build/builds
- **Cloud Storage:** https://console.cloud.google.com/storage/browser
- **Load Balancing:** https://console.cloud.google.com/net-services/loadbalancing
- **Cloud CDN:** https://console.cloud.google.com/net-services/cdn/list

### Community Resources

- **GCP Documentation:** https://cloud.google.com/docs
- **Nuxt Deployment:** https://nuxt.com/docs/getting-started/deployment
- **Stack Overflow:** https://stackoverflow.com/questions/tagged/google-cloud-platform

---

## Known Limitations

### Static Site Limitations

**What works:**
- ✅ Client-side routing (Vue Router)
- ✅ Client-side API calls
- ✅ Client-side auth (Firebase)
- ✅ Dynamic content via API

**What doesn't work:**
- ❌ Server-side rendering (SSR)
- ❌ Server-side API routes
- ❌ Dynamic route generation at request time
- ❌ Server middleware

**Solution if you need SSR:**
Deploy to Cloud Run with Docker instead (see alternative guide).

---

## Emergency Rollback

If deployment breaks production:

```bash
# 1. Get list of recent deployments
gsutil ls -lh gs://$BUCKET_NAME/_nuxt/

# 2. Revert to previous build
# (You'll need to rebuild from git history)
git checkout <previous-commit-hash>
cd frontend
npm run generate
gsutil -m rsync -R -d .output/public/ gs://$BUCKET_NAME/

# 3. Invalidate CDN
gcloud compute url-maps invalidate-cdn-cache churn-risk-frontend-lb --path="/*"
```

**Better approach:** Use versioned buckets (see advanced guides).

---

## Prevention Tips

1. **Test locally before deploying:**
```bash
npm run generate
npm run preview
# Test thoroughly at http://localhost:4173
```

2. **Use staging environment:**
- Create separate bucket for staging
- Test on staging before production

3. **Monitor builds:**
- Set up build failure notifications
- Review build logs regularly

4. **Keep dependencies updated:**
```bash
npm update
npm audit fix
```

---

**Still stuck?** Check the main CLAUDE.md or create an issue in your repository.

# Guide 01: Configure Frontend for Production

**Estimated Time:** 15 minutes
**Prerequisites:** Frontend running locally

---

## Overview

Configure your Nuxt 3 frontend to connect to the production backend API and Firebase Auth.

---

## Step 1: Create Production Environment File

Create a `.env.production` file in the `frontend/` directory:

```bash
cd frontend
touch .env.production
```

Add the following content:

```bash
# Production Backend API
NUXT_PUBLIC_API_BASE=https://churn-risk-api-461448724047.us-east1.run.app

# Firebase Configuration (from your Firebase project)
NUXT_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key-here
NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NUXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
```

**Where to find Firebase values:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Click ⚙️ (Settings) → Project Settings
4. Scroll to "Your apps" section
5. Copy values from the Firebase SDK config

---

## Step 2: Verify Nuxt Configuration

Check that `frontend/nuxt.config.ts` is set up correctly:

```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      firebaseApiKey: process.env.NUXT_PUBLIC_FIREBASE_API_KEY,
      firebaseAuthDomain: process.env.NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
      firebaseProjectId: process.env.NUXT_PUBLIC_FIREBASE_PROJECT_ID,
    }
  }
})
```

This should already be configured (from `frontend/nuxt.config.ts:7-14`).

---

## Step 3: Update Backend CORS Settings

Your production backend needs to allow requests from the frontend domain.

### Option A: Allow All Origins (Development/Testing)

Edit `backend/.env`:
```bash
CORS_ORIGINS=*
```

Update Cloud Run environment variable:
```bash
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="*"
```

### Option B: Specific Origins (Production - Recommended)

Once you know your frontend URL (after deploying), update to specific origins:

```bash
# Example with Cloud Storage bucket domain
CORS_ORIGINS=https://storage.googleapis.com,https://churn-risk-frontend-prod.storage.googleapis.com

# Or with custom domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

Update Cloud Run:
```bash
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="https://storage.googleapis.com,https://your-bucket-name.storage.googleapis.com"
```

**For now, use Option A (allow all) for testing. Lock it down later.**

---

## Step 4: Test Configuration Locally

Start the dev server with production API:

```bash
cd frontend

# Load production environment
export $(cat .env.production | xargs)

# Start dev server
npm run dev
```

Open http://localhost:3000 and verify:
- ✅ App loads without errors
- ✅ Can log in with Firebase
- ✅ API calls reach production backend
- ✅ Check browser console: `API Base: https://churn-risk-api-*.run.app`

### Debugging Tips

**Check runtime config in browser console:**
```javascript
// Open browser console on http://localhost:3000
const config = useRuntimeConfig()
console.log('API Base:', config.public.apiBase)
console.log('Firebase Project:', config.public.firebaseProjectId)
```

**Check network tab:**
1. Open DevTools → Network tab
2. Try logging in
3. Look for API calls to `churn-risk-api-*.run.app`
4. Verify they're not being blocked by CORS

---

## Step 5: Create .gitignore Entry

Ensure production secrets aren't committed:

```bash
cd frontend

# Check if .env.production is ignored
cat .gitignore | grep .env.production
```

If not present, add it:

```bash
echo ".env.production" >> .gitignore
```

**Important:** Never commit `.env.production` to git!

---

## Step 6: Document Environment Variables

Create a `.env.production.example` file for your team:

```bash
cd frontend
cat > .env.production.example << 'EOF'
# Production Backend API
NUXT_PUBLIC_API_BASE=https://your-backend-url.run.app

# Firebase Configuration
NUXT_PUBLIC_FIREBASE_API_KEY=your-api-key-here
NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NUXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id

# Copy this file to .env.production and fill in actual values
EOF
```

This file CAN be committed (it's just a template).

---

## Verification Checklist

Before proceeding to the next guide, verify:

- [ ] `.env.production` created with actual values
- [ ] Backend CORS set to allow frontend domain (or `*` for testing)
- [ ] Local dev server connects to production backend
- [ ] Firebase auth works with production backend
- [ ] API calls visible in Network tab
- [ ] No CORS errors in browser console
- [ ] `.env.production` added to `.gitignore`
- [ ] `.env.production.example` created

---

## Expected Results

### Success Indicators

**Browser Console:**
```
✅ API Base: https://churn-risk-api-461448724047.us-east1.run.app
✅ Firebase Project: your-project-id
✅ No CORS errors
✅ API calls succeed (200 status)
```

**Backend Logs (Cloud Run):**
```bash
# Check backend received requests
gcloud run services logs read churn-risk-api --region=us-east1 --limit=20
```

You should see:
```
✅ OPTIONS requests (CORS preflight)
✅ GET /api/v1/me requests
✅ POST /api/v1/auth/* requests
```

---

## Common Issues

### Issue: CORS Error

**Symptom:** Browser console shows `Access-Control-Allow-Origin` error

**Solution:**
```bash
# Set CORS to allow all origins temporarily
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="*"

# Wait 30 seconds for deployment, then refresh browser
```

### Issue: Firebase Auth Not Working

**Symptom:** Login fails with Firebase error

**Solution:**
1. Check Firebase Console → Authentication → Sign-in method
2. Ensure Email/Password is enabled
3. Verify `.env.production` has correct Firebase values
4. Check browser console for specific Firebase error

### Issue: 404 on API Calls

**Symptom:** API calls return 404

**Solution:**
- Verify API URL in `.env.production` is correct
- Check endpoint path: `/api/v1/me` (not `/me`)
- Verify backend is running: `curl https://churn-risk-api-*.run.app/health`

---

## Next Steps

Once configuration is verified and working:

**→ Proceed to Guide 02: Test Static Build**

This guide will test that `nuxt generate` works correctly before deploying.

---

## Rollback

If you need to undo changes:

```bash
# Revert backend CORS to localhost only
gcloud run services update churn-risk-api \
  --region=us-east1 \
  --update-env-vars=CORS_ORIGINS="http://localhost:3000,http://localhost:8000"

# Delete production env file
rm frontend/.env.production
```

---

## Reference

- **Nuxt Runtime Config:** https://nuxt.com/docs/guide/going-further/runtime-config
- **Firebase Web Setup:** https://firebase.google.com/docs/web/setup
- **CORS Troubleshooting:** https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS

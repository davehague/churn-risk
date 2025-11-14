# Guide 02: Test Static Build

**Estimated Time:** 15 minutes
**Prerequisites:** Guide 01 completed (production config ready)

---

## Overview

Test that Nuxt can generate static files correctly before deploying to GCP. This catches issues early.

---

## Step 1: Understanding Nuxt Generate

Nuxt's `generate` command creates a static version of your app:

**What it does:**
- Pre-renders all pages to HTML
- Bundles JavaScript, CSS, images
- Creates a `.output/public/` directory with deployable files
- Perfect for Cloud Storage hosting

**What it requires:**
- All routes must be pre-renderable
- No server-side-only logic
- API calls happen in browser (client-side)

---

## Step 2: Run Static Generation

```bash
cd frontend

# Load production environment
export $(cat .env.production | xargs)

# Generate static files
npm run generate
```

**Expected output:**
```
ℹ Building Nuxt
✔ Nuxt built in 15s
ℹ Generating pages
✔ Generated route /
✔ Generated route /login
✔ Generated route /register
✔ Generated route /dashboard
✔ Generated route /404
✔ Generated .output/public
```

---

## Step 3: Inspect Generated Files

Check that files were created:

```bash
# View directory structure
ls -lh .output/public/

# Expected files:
# index.html          - Landing page
# login/index.html    - Login page
# register/index.html - Registration page
# dashboard/index.html - Dashboard page
# 404.html            - Error page
# _nuxt/              - JS/CSS bundles
# favicon.ico         - Icon
```

**Key files to verify:**

```bash
# Check index.html exists
cat .output/public/index.html | head -20

# Check JS bundles exist
ls -lh .output/public/_nuxt/*.js

# Check total size (should be < 5MB)
du -sh .output/public/
```

**Typical sizes:**
- HTML files: ~5-10 KB each
- JS bundles: 200-500 KB total
- CSS files: 50-100 KB total
- **Total: Usually 1-3 MB**

---

## Step 4: Preview Static Site Locally

Nuxt provides a preview server to test the generated static files:

```bash
cd frontend

# Preview the static build
npm run preview
```

**Expected output:**
```
  > Local:    http://localhost:4173/
  > Network:  use --host to expose
```

Open http://localhost:4173 in your browser.

---

## Step 5: Test Static Site Functionality

Test all key features work in static mode:

### ✅ Test 1: Landing Page
- [ ] Visit http://localhost:4173
- [ ] Page loads without errors
- [ ] Content displays correctly
- [ ] Links work

### ✅ Test 2: Authentication
- [ ] Go to /login
- [ ] Try logging in with test account
- [ ] Verify Firebase auth works
- [ ] Check redirect to /dashboard

### ✅ Test 3: Protected Routes
- [ ] Logout
- [ ] Try visiting /dashboard directly
- [ ] Should redirect to /login

### ✅ Test 4: API Calls
- [ ] Login to app
- [ ] Go to dashboard
- [ ] Open DevTools → Network tab
- [ ] Verify API calls to production backend
- [ ] Should see requests to `https://churn-risk-api-*.run.app`

### ✅ Test 5: Navigation
- [ ] Click through all menu items
- [ ] Verify no 404 errors
- [ ] All routes load correctly

---

## Step 6: Check Browser Console

Open browser DevTools → Console:

**Good signs (no errors):**
```
✅ No 404 errors for missing files
✅ No CORS errors
✅ Firebase initializes successfully
✅ API calls succeed
```

**Runtime config check:**
```javascript
// Type in console:
const config = useRuntimeConfig()
console.log(config.public)

// Should show:
{
  apiBase: "https://churn-risk-api-461448724047.us-east1.run.app",
  firebaseApiKey: "your-key",
  firebaseAuthDomain: "your-domain",
  firebaseProjectId: "your-project"
}
```

---

## Step 7: Test with Different Routes

Test that all routes work correctly:

```bash
# Test each route directly
curl -I http://localhost:4173/
curl -I http://localhost:4173/login
curl -I http://localhost:4173/register
curl -I http://localhost:4173/dashboard

# All should return 200 OK
```

**Important:** Static sites serve `dashboard/index.html` for `/dashboard` URLs.

---

## Step 8: Check for Build Errors

Review the build output for warnings:

```bash
# Re-run build to see any warnings
npm run generate 2>&1 | tee build.log

# Check for warnings
grep -i "warn\|error" build.log
```

**Common warnings (usually safe to ignore):**
- Hydration warnings (if using SSR components)
- Unused CSS warnings
- Image optimization warnings

**Errors to fix:**
- Module not found
- Syntax errors
- Missing dependencies

---

## Step 9: Verify Environment Variables in Build

Ensure production config is baked into the static files:

```bash
# Check that API URL is in the built JS
grep -r "churn-risk-api-461448724047" .output/public/_nuxt/

# Should find it in one of the JS bundles
# Example: .output/public/_nuxt/entry.abc123.js
```

If NOT found:
- Environment variables weren't loaded during build
- Re-run with `export $(cat .env.production | xargs)`

---

## Verification Checklist

Before proceeding, verify:

- [ ] `npm run generate` completes successfully
- [ ] `.output/public/` directory created with files
- [ ] All HTML pages generated (index, login, register, dashboard, 404)
- [ ] JS/CSS bundles created in `_nuxt/` directory
- [ ] Total size < 5 MB
- [ ] `npm run preview` works locally
- [ ] Can login via Firebase
- [ ] API calls reach production backend
- [ ] No console errors
- [ ] All routes accessible
- [ ] Production API URL found in built JS files

---

## Common Issues

### Issue: `nuxt generate` Fails

**Symptom:** Build fails with error

**Common causes:**
```bash
# 1. Missing dependencies
npm install

# 2. TypeScript errors
npm run typecheck

# 3. Syntax errors
npm run lint
```

### Issue: Blank Page After Build

**Symptom:** Preview shows blank page

**Solution:**
1. Check browser console for errors
2. Verify `index.html` was created
3. Check that base URL is set correctly
4. Try clearing `.nuxt` cache:
   ```bash
   rm -rf .nuxt .output
   npm run generate
   ```

### Issue: API Calls Fail in Preview

**Symptom:** API calls return 404 or CORS errors

**Solution:**
1. Verify backend CORS allows your domain
2. Check `.env.production` is loaded:
   ```bash
   echo $NUXT_PUBLIC_API_BASE
   # Should show production URL
   ```
3. Re-run generate with env vars:
   ```bash
   export $(cat .env.production | xargs)
   npm run generate
   ```

### Issue: Firebase Auth Fails

**Symptom:** Login doesn't work in preview

**Solution:**
1. Check Firebase config in built files:
   ```bash
   grep -r "firebaseApiKey" .output/public/_nuxt/
   ```
2. Verify Firebase Console → Authentication enabled
3. Check authorized domains in Firebase Console

### Issue: 404 on Navigation

**Symptom:** Direct URL access returns 404

**Solution:**
- This is expected for static preview (local server limitation)
- Will work correctly on Cloud Storage with `gsutil web set`
- For now, navigate via links (not direct URLs)

---

## Expected File Structure

```
.output/public/
├── index.html              # Landing page
├── login/
│   └── index.html          # Login page
├── register/
│   └── index.html          # Registration page
├── dashboard/
│   └── index.html          # Dashboard page
├── 404.html                # Error page
├── _nuxt/
│   ├── entry.*.js          # Main app bundle
│   ├── *.js                # Page-specific JS
│   └── *.css               # Stylesheets
└── favicon.ico             # Site icon
```

---

## Performance Check

Your static site should be fast:

```bash
# Check bundle sizes
ls -lh .output/public/_nuxt/*.js

# Aim for:
# - Entry bundle: < 300 KB
# - Total JS: < 500 KB
# - Total CSS: < 100 KB
```

**If bundles are too large:**
- Consider code splitting
- Remove unused dependencies
- Optimize images

---

## Next Steps

Once static build works perfectly:

**→ Proceed to Guide 03: Create Storage Bucket**

This guide will create the Cloud Storage bucket to host your static files.

---

## Rollback

If you need to go back to dev mode:

```bash
# Stop preview server (Ctrl+C)

# Clean build artifacts
rm -rf .nuxt .output

# Return to dev mode
npm run dev
```

---

## Reference

- **Nuxt Static Generation:** https://nuxt.com/docs/getting-started/deployment#static-hosting
- **Preview Mode:** https://nuxt.com/docs/api/commands/preview
- **Deployment Guide:** https://nuxt.com/docs/getting-started/deployment

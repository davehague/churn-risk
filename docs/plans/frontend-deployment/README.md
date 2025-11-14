# Frontend Deployment Guide - Churn Risk App

Complete guide for deploying the Nuxt 3 frontend to Google Cloud Platform using Cloud Storage + CDN.

---

## Quick Start

**Prerequisites:**
- ✅ Backend deployed to Cloud Run (you have this)
- ✅ Frontend running locally (you have this)
- ✅ gcloud CLI installed

**Deployment Strategy:** Static site on Cloud Storage + Cloud CDN
- ✅ No Docker issues (unlike backend)
- ✅ Cheaper ($1-3/month vs $5-10/month)
- ✅ Faster (CDN edge caching)
- ✅ Simpler CI/CD

---

## Guides

Follow these guides in order:

### Phase 1: Prepare & Test (45 min)
1. **[00-overview.md](00-overview.md)** - Architecture and strategy
2. **[01-configure-production.md](01-configure-production.md)** - Set production env vars
3. **[02-test-static-build.md](02-test-static-build.md)** - Test `nuxt generate` locally

### Phase 2: Deploy to GCP (30 min)
4. **[03-create-storage-bucket.md](03-create-storage-bucket.md)** - Create Cloud Storage bucket
5. **[04-load-balancer-cdn.md](04-load-balancer-cdn.md)** - Setup Load Balancer + CDN + HTTPS

### Phase 3: Automate (20 min)
6. **[05-cicd-setup.md](05-cicd-setup.md)** - CI/CD with Cloud Build

### Optional
7. **[06-troubleshooting.md](06-troubleshooting.md)** - Common issues and solutions

---

## What You'll Build

```
User (anywhere in world)
    ↓
Cloud CDN (edge cache, <50ms)
    ↓
Load Balancer (HTTPS)
    ↓
Cloud Storage (static files)
    ↓ API calls
Backend API (Cloud Run)
    ↓
Cloud SQL (database)
```

---

## Estimated Costs

**Static Frontend:**
- Cloud Storage: $0.10/month
- Cloud CDN: $0.50/month
- Load Balancer: $0.60/month
- SSL Certificate: Free
- **Total: ~$1.20/month**

**With $300 free credits:** Covered for 250 months!

---

## Why Static vs Container?

| Aspect | Static (This Guide) | Container (Alternative) |
|--------|-------------------|------------------------|
| Complexity | ⭐ Simple | ⭐⭐⭐ Complex |
| Docker | ✅ Not needed | ❌ Required (you had issues) |
| Cost | 💰 $1-3/month | 💰💰 $5-10/month |
| Performance | 🚀 CDN edges | 🐢 Single region |
| Your use case | ✅ Perfect fit | ⚠️ Overkill |

---

## Time Estimates

**Total time:** ~1.5-2 hours

- Guide 01: 15 minutes (configure production)
- Guide 02: 15 minutes (test static build)
- Guide 03: 10 minutes (create bucket)
- Guide 04: 20 minutes (load balancer + CDN)
- Guide 05: 20 minutes (CI/CD)
- Testing: 20 minutes

---

## Success Criteria

By the end, you'll have:
- ✅ Production frontend URL (with HTTPS)
- ✅ Global CDN caching (fast everywhere)
- ✅ Auto-deploy on git push
- ✅ Frontend talking to production backend
- ✅ Firebase auth working in production

---

## Getting Help

**During deployment:**
- Check [06-troubleshooting.md](06-troubleshooting.md)
- Review Cloud Build logs: `gcloud builds log <BUILD_ID>`
- Check browser console for errors

**After deployment:**
- Monitor via Cloud Console → Cloud Storage
- View CDN cache stats → Cloud CDN
- Check costs → Billing

---

## Ready to Start?

**→ Begin with [00-overview.md](00-overview.md)**

---

## Related Documentation

- **Backend Deployment:** `../cloud/` - Backend deployment guides
- **Architecture:** `../../dev/architecture-overview.md`
- **Frontend Dev Guide:** `../../frontend/CLAUDE.md`

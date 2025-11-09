# GCP Deployment Overview - Churn Risk App

**Last Updated:** 2025-11-09
**Estimated Time:** 2-3 hours (first time)
**Cost:** $0 (using $300 free tier credits)

---

## What We're Deploying

This guide will walk you through deploying the Churn Risk App backend to Google Cloud Platform (GCP). By the end, you'll have:

✅ **Production-ready FastAPI backend** running on Cloud Run
✅ **Managed PostgreSQL database** on Cloud SQL
✅ **Secure secrets management** via Secret Manager
✅ **Auto-scaling API** with custom `.run.app` domain
✅ **Working HubSpot OAuth** with production redirect URIs
✅ **Firebase authentication** connected to production
✅ **Monitoring and logging** via Cloud Logging

---

## Architecture: Local vs Production

### Current Local Setup

```
Your Machine:
├── Backend: poetry run uvicorn (port 8000)
├── Database: docker-compose postgres (port 5432)
├── Redis: docker-compose redis (port 6379)
└── Frontend: npm run dev (port 3000)
```

**What stays local:**
- Frontend (for now - you'll develop against production API)
- Docker Compose (for local development)
- Poetry environment (for local testing)

---

### Production Architecture (What You're Building)

```
Google Cloud Platform:
├── Cloud Run
│   └── FastAPI Backend (containerized)
│       ├── Auto-scales 0-1000 instances
│       ├── Custom domain: your-app-xyz.run.app
│       └── HTTPS automatically enabled
│
├── Cloud SQL for PostgreSQL
│   └── Managed database (db-f1-micro to start)
│       ├── Automated backups
│       ├── High availability option
│       └── Private VPC connection
│
├── Secret Manager
│   └── Encrypted secrets storage
│       ├── Firebase credentials
│       ├── HubSpot OAuth secrets
│       ├── OpenRouter API key
│       └── Database password
│
└── External Services (same as local)
    ├── Firebase Auth
    ├── HubSpot OAuth
    └── OpenRouter AI
```

---

## Why This Architecture?

**Cloud Run (vs Compute Engine VMs):**
- ✅ Serverless - pay only for requests, not idle time
- ✅ Auto-scales from 0 to 1000+ instances automatically
- ✅ No server management - Google handles OS updates
- ✅ Built-in HTTPS and load balancing
- ✅ Perfect for APIs with variable traffic

**Cloud SQL (vs self-hosted Postgres):**
- ✅ Managed service - Google handles backups, updates, scaling
- ✅ Automated daily backups + point-in-time recovery
- ✅ High availability with automatic failover
- ✅ Private VPC connection (secure)
- ✅ No need to manage database servers

**Secret Manager (vs environment variables):**
- ✅ Encrypted at rest and in transit
- ✅ Audit logging (who accessed what secret when)
- ✅ Version control for secrets
- ✅ Fine-grained access control
- ✅ Industry best practice for production

---

## Deployment Sequence

You'll deploy incrementally to catch issues early:

### Phase 1: Infrastructure Setup
1. **GCP Account Setup** - Create account, enable billing, activate credits
2. **Local Prep** - Install/update gcloud CLI, authenticate
3. **Dockerfile** - Create production container for FastAPI

### Phase 2: Database & Secrets
4. **Cloud SQL** - Create managed PostgreSQL instance
5. **Secret Manager** - Store sensitive credentials securely
6. **Database Migration** - Run Alembic migrations on Cloud SQL

### Phase 3: Deploy & Test
7. **Local Docker Test** - Verify container works before deploying
8. **Cloud Run Deployment** - Deploy backend to production
9. **Production Testing** - Verify everything works end-to-end

### Phase 4: Optional Enhancements
10. **Monitoring** - Set up logging, alerts, uptime checks
11. **CI/CD** - Automate deployments from GitHub
12. **Custom Domain** - Add your own domain (optional)
13. **Troubleshooting** - Common issues and solutions

---

## Cost Breakdown (With Free Tier)

### Free Tier Credits
- **$300 credits** for 90 days (new accounts)
- Covers all costs for first 3 months easily
- No credit card charges until you explicitly upgrade

### Estimated Monthly Costs

**Minimal Traffic (POC stage):**
```
Cloud Run (1-10 requests/day):     $0 (within free tier)
Cloud SQL (db-f1-micro):           $7/month
Secret Manager:                    $0 (first 6 secrets free)
Network egress:                    $1/month
TOTAL:                             ~$8/month
```

**Light Production (100 requests/day, 5 customers):**
```
Cloud Run:                         $5/month
Cloud SQL (db-g1-small):           $25/month
Secret Manager:                    $0
Network egress:                    $3/month
TOTAL:                             ~$33/month
```

**With $300 credits:** You're covered for 9+ months even at light production traffic.

---

## Prerequisites Checklist

Before starting, ensure you have:

**Required:**
- [ ] Credit card (for GCP billing - won't be charged)
- [ ] Email address not previously used for GCP (for $300 credits)
- [ ] Docker installed and running locally
- [ ] gcloud CLI installed (we'll update it)
- [ ] Your project running locally (backend + database)

**Helpful to Have:**
- [ ] GitHub account (for CI/CD later)
- [ ] Firebase project already set up (you have this)
- [ ] HubSpot OAuth app configured (you have this)
- [ ] OpenRouter API key (you have this)

---

## What You'll Need During Deployment

**Secrets/Credentials:**
- Firebase credentials JSON file (you have: `firebase-credentials.json`)
- HubSpot OAuth Client ID and Secret (you have in `.env`)
- OpenRouter API key (you have in `.env`)

**New Information You'll Create:**
- GCP Project ID (you'll choose this, e.g., `churn-risk-prod`)
- Cloud SQL instance name (e.g., `churn-risk-db`)
- Database username/password (you'll generate these)

---

## Timeline Estimates

**Fast Track (Experienced with GCP):**
- Phase 1: 20 minutes
- Phase 2: 30 minutes
- Phase 3: 20 minutes
- **Total: ~70 minutes**

**First Time (Following Guide Carefully):**
- Phase 1: 45 minutes
- Phase 2: 60 minutes
- Phase 3: 45 minutes
- **Total: ~2.5 hours**

**Recommended Approach:**
- Do Phases 1-2 in one sitting (setup)
- Take a break
- Do Phase 3 fresh (deployment & testing)

---

## Success Criteria

By the end of this deployment, you should have:

✅ A live API endpoint: `https://your-app-xyz.run.app`
✅ Health check responding: `https://your-app-xyz.run.app/health`
✅ API docs accessible: `https://your-app-xyz.run.app/api/v1/docs`
✅ Database with all 11 tables created
✅ Secrets stored securely in Secret Manager
✅ All environment variables configured
✅ HubSpot OAuth working with production URL
✅ Firebase auth working with production backend
✅ Logs visible in Cloud Logging
✅ Cost tracking showing usage within free tier

---

## Getting Help

**During Deployment:**
- Each guide has a "Troubleshooting" section
- Guide 13 has comprehensive troubleshooting
- Check Cloud Logging for detailed error messages

**After Deployment:**
- GCP Console → Error Reporting (shows Python exceptions)
- Cloud Logging (shows all application logs)
- Cloud Monitoring (shows performance metrics)

**Community Resources:**
- [GCP FastAPI Quickstart](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service)
- [Cloud SQL Quickstart](https://cloud.google.com/sql/docs/postgres/connect-instance-cloud-run)
- [Secret Manager Guide](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets)

---

## What's NOT In This Guide

**Not Covered (Yet):**
- Frontend deployment (backend only for now)
- Redis/Memorystore setup (can add later if needed)
- Cloud Tasks for background jobs (future enhancement)
- Custom domain setup (optional - see guide 12)
- Multi-region deployment (overkill for MVP)
- Load testing and optimization (premature)

**When to Add These:**
- Frontend: After backend is stable and tested
- Redis: When you need caching or session storage
- Cloud Tasks: When you need background job processing
- Custom domain: When you're ready to go live with customers

---

## Ready to Start?

If you have:
- ✅ Docker running locally
- ✅ Your local app working (backend + database)
- ✅ Credit card ready for GCP signup
- ✅ 2-3 hours of uninterrupted time

**→ Proceed to Guide 01: GCP Account Setup**

If not quite ready:
- Get your local environment working first (see `CLAUDE.md`)
- Make sure all tests pass: `cd backend && poetry run pytest`
- Verify local API works: `curl http://localhost:8000/health`

---

## Guide Navigation

- **→ Next:** [01 - GCP Account Setup](01-gcp-account-setup.md)
- **↑ Up:** [Main Documentation](../../README.md)

---

**Questions before starting?** Review the troubleshooting guide (13) or check the main `CLAUDE.md` for architecture details.

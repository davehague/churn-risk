# GCP Deployment Guides

Complete step-by-step guides for deploying the Churn Risk App to Google Cloud Platform.

## Quick Navigation

### Phase 1: Infrastructure Setup
- [00 - Overview](00-overview.md) - What we're deploying and why
- [01 - GCP Account Setup](01-gcp-account-setup.md) - Create account, enable billing, get $300 credits
- [02 - Local Prep](02-local-prep.md) - Install gcloud, authenticate, configure
- [03 - Dockerfile](03-dockerfile.md) - Create production container

### Phase 2: Database & Secrets
- [04 - Cloud SQL](04-cloud-sql.md) - Create managed PostgreSQL
- [05 - Secret Manager](05-secret-manager.md) - Store secrets securely
- [06 - Database Migration](06-database-migration.md) - Run Alembic migrations

### Phase 3: Deploy & Test
- [07 - Local Docker Test](07-local-docker-test.md) - Test container before deploying
- [08 - Cloud Run Deployment](08-cloud-run-deployment.md) - Deploy backend to production
- [09 - Production Testing](09-production-testing.md) - Verify everything works

### Phase 4: Optional Enhancements
- [10 - Monitoring](10-monitoring.md) - Logging, alerts, metrics
- [11 - CI/CD](11-cicd-optional.md) - Automatic deployments
- [12 - Custom Domain](12-custom-domain-optional.md) - Add your own domain
- [13 - Troubleshooting](13-troubleshooting.md) - Common issues & fixes

## Estimated Timeline

- **Fast track** (experienced): ~70 minutes
- **First time** (following carefully): ~2.5 hours
- **Recommended**: Do Phases 1-2 in one sitting, then Phase 3 after a break

## Prerequisites

- Credit card (for GCP billing - won't be charged)
- Email never used for GCP (for $300 credits)
- Docker installed and running
- Project running locally

## Costs

With $300 free tier credits:
- **Month 1-3**: $0 (covered by credits)
- **Ongoing**: ~$8-33/month (depending on traffic)

## Getting Help

- Each guide has troubleshooting section
- Guide 13 has comprehensive troubleshooting
- GCP Console → Logging for detailed errors

---

**Start here:** [00 - Overview](00-overview.md)

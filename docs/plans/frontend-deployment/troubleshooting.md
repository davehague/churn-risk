🔴 What I Changed (That May Have Broken Things)

  Changes Made:

  1. Added DATABASE_URL environment variable (NEW - wasn't set before)
  gcloud run services update churn-risk-api \
    --region=us-east1 \
    --set-env-vars="DATABASE_URL=postgresql://churn_risk_app:SecurePassword123@/churn_risk_prod?host=/cloudsql/churn-risk-app:us-east1:churn-risk-db"
  2. Changed database password from RicketyRocketWaterMice4* to SecurePassword123
  gcloud sql users set-password churn_risk_app --instance=churn-risk-db --password="SecurePassword123"
  3. Updated database-password secret in Secret Manager
  echo -n "SecurePassword123" | gcloud secrets versions add database-password --data-file=-
  4. Updated CORS_ORIGINS to * (this is fine, not the issue)

  ---
  🔍 How to Test Database Connection

  Step 1: Check What's Currently Configured

  # Check current backend environment variables
  gcloud run services describe churn-risk-api --region=us-east1 \
    --format="yaml(spec.template.spec.containers[0].env)"

  # Check Cloud SQL instance status
  gcloud sql instances describe churn-risk-db

  # Check database users
  gcloud sql users list --instance=churn-risk-db

  Step 2: Test Direct Database Connection

  # Install Cloud SQL Proxy (if not already installed)
  # On Mac:
  brew install --cask google-cloud-sdk
  gcloud components install cloud-sql-proxy

  # Start Cloud SQL Proxy in the background
  cloud-sql-proxy churn-risk-app:us-east1:churn-risk-db &

  # In another terminal, try to connect with current password
  psql "host=127.0.0.1 port=5432 user=churn_risk_app dbname=churn_risk_prod" \
    -c "SELECT version();"
  # When prompted, enter: SecurePassword123

  # If that fails, try with the old password:
  # Password: RicketyRocketWaterMice4*

  # Try connecting as postgres superuser
  gcloud sql connect churn-risk-db --user=postgres --database=churn_risk_prod

  Step 3: Check Backend Logs for Exact Error

  # Get the most recent database error
  gcloud run services logs read churn-risk-api --region=us-east1 --limit=100 \
    | grep -A5 "password authentication failed"

  # Get the full DATABASE_URL being used (without password shown)
  gcloud run services logs read churn-risk-api --region=us-east1 --limit=50 \
    | grep -i "database"

  ---
  🔄 How to Rollback My Changes

  Option 1: Rollback to Previous Working Revision

  # List recent revisions
  gcloud run revisions list --service=churn-risk-api --region=us-east1 --limit=10

  # Find the revision from BEFORE my changes (look for timestamp before ~14:00 UTC today)
  # Rollback to that revision (replace REVISION_NAME with actual name)
  gcloud run services update-traffic churn-risk-api \
    --region=us-east1 \
    --to-revisions=REVISION_NAME=100

  Option 2: Remove DATABASE_URL I Added

  # Remove the DATABASE_URL environment variable I added
  gcloud run services update churn-risk-api \
    --region=us-east1 \
    --remove-env-vars=DATABASE_URL

  Option 3: Restore Old Password

  # Set password back to original
  gcloud sql users set-password churn_risk_app \
    --instance=churn-risk-db \
    --password="RicketyRocketWaterMice4*"

  # Restore old password in Secret Manager
  echo -n "RicketyRocketWaterMice4*" | \
    gcloud secrets versions add database-password --data-file=-

  # Force new deployment to pick up old password
  gcloud run services update churn-risk-api \
    --region=us-east1 \
    --update-labels="rollback=$(date +%s)"

  ---
  📋 Original Configuration (Before My Changes)

  Based on the deployment, the backend was likely configured with:
  - ❌ No DATABASE_URL environment variable explicitly set
  - ✅ DATABASE_PASSWORD from Secret Manager: RicketyRocketWaterMice4*
  - ✅ Cloud SQL connection annotation: churn-risk-app:us-east1:churn-risk-db

  The backend code might have been building the DATABASE_URL automatically from other env vars or using a default configuration.

  ---
  🎯 Recommended Next Steps

  1. First, check what revision was working:
  gcloud run revisions list --service=churn-risk-api --region=us-east1 \
    --format="table(metadata.name,status.conditions[0].lastTransitionTime,metadata.labels)"
  2. Look for the revision from Nov 12 (before today's changes) and rollback to it
  3. Test database connection directly using the Cloud SQL Proxy method above
  4. Once we know which password works, we can reconfigure properly

  Would you like me to help you rollback to the previous working state?
# 06 - Database Migration

**Estimated Time:** 10-15 minutes
**Cost:** $0 (uses existing Cloud SQL instance)
**Prerequisites:** Guides 01-05 completed

---

## Overview

Run Alembic migrations to create your database schema on Cloud SQL. This creates all 11 tables needed for the application.

**What You'll Do:**
- Connect to Cloud SQL via Cloud SQL Proxy
- Run Alembic migrations
- Verify tables were created
- Test database connectivity

---

## Step 1: Prepare Connection

### 1.1 Start Cloud SQL Proxy

In a terminal, start the proxy (keep it running):

```bash
cloud-sql-proxy PROJECT_ID:REGION:INSTANCE_NAME
```

**Example:**
```bash
cloud-sql-proxy churn-risk-prod-123456:us-central1:churn-risk-db
```

**Expected output:**
```
Listening on 127.0.0.1:5432
Ready for new connections
```

**Keep this terminal open** during migration.

### 1.2 Create Temporary Connection Config

Create `backend/.env.migration`:

```bash
# Cloud SQL connection for migrations
DATABASE_URL=postgresql://churn_risk_app:YOUR_APP_PASSWORD@127.0.0.1:5432/churn_risk_prod

# Required for alembic
ENVIRONMENT=production
SECRET_KEY=temp-migration-key
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000

# Dummy values (not needed for migration but required by config)
FIREBASE_PROJECT_ID=dummy
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
OPENROUTER_API_KEY=dummy
HUBSPOT_CLIENT_ID=dummy
HUBSPOT_CLIENT_SECRET=dummy
HUBSPOT_REDIRECT_URI=dummy
```

**Replace `YOUR_APP_PASSWORD`** with the `churn_risk_app` password from Guide 04.

---

## Step 2: Verify Migration Files

### 2.1 Check Alembic Configuration

Verify `backend/alembic.ini` exists and is configured:

```bash
cd backend
cat alembic.ini | grep script_location
```

**Should show:**
```
script_location = alembic
```

### 2.2 List Existing Migrations

```bash
ls alembic/versions/
```

**Should show your initial migration file** (created during local development):
```
c08085465bad_initial_schema.py
```

### 2.3 Check Current Migration Status (Before Running)

```bash
# Load .env.migration (handles special characters properly)
set -a
source .env.migration
set +a

# Check migration status
poetry run alembic current
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

(No version shown = database has no migrations yet)

---

## Step 3: Run Migrations

### 3.1 Grant Permissions (First Time Only)

Before running migrations for the first time, grant the necessary permissions:

```bash
# Connect as postgres superuser
psql "host=127.0.0.1 port=5432 sslmode=disable user=postgres dbname=churn_risk_prod"
```

**Enter postgres password when prompted** (from Guide 04).

Then run these SQL commands:

```sql
-- Grant all privileges on the public schema
GRANT ALL PRIVILEGES ON SCHEMA public TO churn_risk_app;

-- Allow creating tables in the future
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO churn_risk_app;

-- Grant privileges on sequences (for auto-incrementing fields)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO churn_risk_app;

-- Exit psql
\q
```

**Why this is needed:** By default, the `churn_risk_app` user doesn't have permissions to create tables in the `public` schema. This grants the necessary permissions.

### 3.2 Apply All Migrations

```bash
# Load .env.migration (handles special characters properly)
set -a
source .env.migration
set +a

# Run migrations
poetry run alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> c08085465bad, Initial schema
```

**This creates all 11 tables:**
- tenants
- users
- integrations
- companies
- contacts
- tickets
- ticket_topics
- ticket_topic_assignments
- churn_risk_cards
- churn_risk_comments
- alembic_version

**Time:** Usually takes 2-5 seconds.

### 3.3 Verify Migration Completed

```bash
poetry run alembic current
```

**Should now show:**
```
c08085465bad (head)
```

This means the database is at the latest migration version.

---

## Step 4: Verify Tables Created

### 4.1 Connect with psql

```bash
psql "host=127.0.0.1 port=5432 sslmode=disable user=churn_risk_app dbname=churn_risk_prod"
```

**Enter your app password when prompted.**

### 4.2 List All Tables

```sql
\dt
```

**Expected output:**
```
                     List of relations
 Schema |             Name              | Type  |      Owner      
--------+-------------------------------+-------+-----------------
 public | alembic_version               | table | churn_risk_app
 public | churn_risk_cards              | table | churn_risk_app
 public | churn_risk_comments           | table | churn_risk_app
 public | companies                     | table | churn_risk_app
 public | contacts                      | table | churn_risk_app
 public | integrations                  | table | churn_risk_app
 public | tenants                       | table | churn_risk_app
 public | ticket_topic_assignments      | table | churn_risk_app
 public | ticket_topics                 | table | churn_risk_app
 public | tickets                       | table | churn_risk_app
 public | users                         | table | churn_risk_app
(11 rows)
```

**Should see exactly 11 tables.**

### 4.3 Check Table Structure (Sample)

```sql
\d tenants
```

**Should show:**
```
                        Table "public.tenants"
    Column    |            Type             | Collation | Nullable | Default 
--------------+-----------------------------+-----------+----------+---------
 id           | uuid                        |           | not null | 
 created_at   | timestamp without time zone |           | not null | 
 updated_at   | timestamp without time zone |           | not null | 
 name         | character varying(255)      |           | not null | 
 subdomain    | character varying(63)       |           | not null | 
 plan_tier    | VARCHAR(20)                 |           | not null | 
Indexes:
    "tenants_pkey" PRIMARY KEY, btree (id)
    "ix_tenants_subdomain" UNIQUE, btree (subdomain)
Referenced by:
    TABLE "users" CONSTRAINT "users_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
```

### 4.4 Exit psql

```sql
\q
```

---

## Step 5: Test Database Connectivity from Python

### 5.1 Create Connection Test Script

Create `backend/test_db_connection.py`:

```python
#!/usr/bin/env python3
"""Test database connection to Cloud SQL."""

import os
from sqlalchemy import create_engine, text

def test_connection():
    """Test connection to Cloud SQL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    print(f"Testing connection to: {database_url.split('@')[1]}")
    
    try:
        engine = create_engine(database_url)
        
        # Test basic connection
        with engine.connect() as conn:
            print("✅ Connection successful")
            
            # Count tables
            result = conn.execute(text("""
                SELECT COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """))
            count = result.fetchone()[0]
            print(f"✅ Found {count} tables")
            
            # Check alembic version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()[0]
            print(f"✅ Migration version: {version}")
            
            # List all tables
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✅ Tables: {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv(".env.migration")
    
    success = test_connection()
    exit(0 if success else 1)
```

### 5.2 Run Connection Test

```bash
poetry run python test_db_connection.py
```

**Expected output:**
```
Testing connection to: 127.0.0.1:5432/churn_risk_prod
✅ Connection successful
✅ Found 11 tables
✅ Migration version: c08085465bad
✅ Tables: alembic_version, churn_risk_cards, churn_risk_comments, companies, contacts, integrations, tenants, ticket_topic_assignments, ticket_topics, tickets, users
```

---

## Step 6: Clean Up Temporary Files

### 6.1 Remove Migration .env File

The `.env.migration` file contains the database password. Delete it:

```bash
rm .env.migration
```

**Why:** Secrets should only be in Secret Manager in production, not local files.

### 6.2 Keep Test Scripts (Optional)

You can keep test scripts for future reference:
```bash
# These are safe to keep (no secrets)
ls test_*.py
```

---

## Verification Checklist

Before proceeding:

- [ ] Cloud SQL Proxy connected successfully
- [ ] Alembic migrations ran without errors
- [ ] All 11 tables created in database
- [ ] Migration version shows: `c08085465bad (head)`
- [ ] Python connection test passed
- [ ] Temporary .env.migration file deleted

---

## Important: Migration Strategy for Production

### Future Migrations

When you add new tables or modify existing ones:

**1. Create migration locally:**
```bash
cd backend
poetry run alembic revision --autogenerate -m "description of changes"
```

**2. Review the generated migration file** in `alembic/versions/`

**3. Test locally:**
```bash
poetry run alembic upgrade head
```

**4. Deploy to production:**
```bash
# Connect via Cloud SQL Proxy and load environment
set -a
source .env.migration
set +a
poetry run alembic upgrade head
```

**5. Or run migrations automatically on Cloud Run startup** (we'll cover this in deployment guide)

---

## Rollback Strategy (If Needed)

### Rollback One Migration

```bash
poetry run alembic downgrade -1
```

### Rollback to Specific Version

```bash
poetry run alembic downgrade c08085465bad
```

### Check Migration History

```bash
poetry run alembic history
```

---

## Troubleshooting

### Problem: "export: not valid in this context" when loading .env.migration

**Cause:** The simple `export $(cat .env.migration | xargs)` command fails when environment variable values contain special characters like parentheses.

**Solution:** Use the `set -a; source .env.migration; set +a` approach instead:
```bash
set -a
source .env.migration
set +a
```

This properly handles special characters in variable values.

### Problem: "Can't connect to database"

**Solutions:**
- Verify Cloud SQL Proxy is running
- Check DATABASE_URL in .env.migration
- Ensure Cloud SQL instance status is "Ready"
- Verify password is correct

### Problem: "Permission denied for schema public"

**Cause:** The `churn_risk_app` user doesn't have permissions to create tables in the `public` schema.

**Solution:** This should be handled by Step 3.1. If you skipped that step, run:
```bash
# Connect as postgres superuser
psql "host=127.0.0.1 port=5432 sslmode=disable user=postgres dbname=churn_risk_prod"
```

Then grant permissions:
```sql
GRANT ALL PRIVILEGES ON SCHEMA public TO churn_risk_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO churn_risk_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO churn_risk_app;
\q
```

### Problem: "Migration already exists" or duplicate tables

**Solution:**
```bash
# Check current version
poetry run alembic current

# If tables exist but alembic_version is empty, stamp current version:
poetry run alembic stamp head
```

### Problem: "FATAL: password authentication failed"

**Solutions:**
- Verify you're using `churn_risk_app` user (not `postgres`)
- Check password is correct (from Guide 04)
- Ensure user exists: `SELECT * FROM pg_roles WHERE rolname = 'churn_risk_app';`

### Problem: Migration fails partway through

**Solutions:**
```bash
# Check what happened
poetry run alembic current

# Review migration file for errors
cat alembic/versions/c08085465bad*.py

# Drop database and start fresh (development only!)
# DO NOT do this in production with data
dropdb -h 127.0.0.1 -U postgres churn_risk_prod
createdb -h 127.0.0.1 -U postgres churn_risk_prod
# Re-run migrations
```

---

## What You've Accomplished

✅ Connected to Cloud SQL from local machine
✅ Ran Alembic migrations successfully
✅ Created all 11 database tables
✅ Verified table structure and relationships
✅ Tested database connectivity with Python

---

## Database Schema Summary

**Tables Created:**

1. **tenants** - Multi-tenant root entity
2. **users** - User accounts (linked to Firebase)
3. **integrations** - OAuth credentials (HubSpot)
4. **companies** - Customer companies from HubSpot
5. **contacts** - People at customer companies
6. **tickets** - Support tickets with sentiment
7. **ticket_topics** - Configured topics for classification
8. **ticket_topic_assignments** - Many-to-many ticket ↔ topic
9. **churn_risk_cards** - Generated churn risk alerts
10. **churn_risk_comments** - Activity timeline on cards
11. **alembic_version** - Migration tracking

**Total tables:** 11
**Foreign keys:** 15+ (all with CASCADE delete)
**Indexes:** 20+ (for performance)

---

## Costs Incurred

**Cloud SQL ongoing cost:** ~$8.87/month (from Guide 04)
**Migration cost:** $0 (no additional charge)

**With $300 credits:** Covered for 30+ months

---

## Next Steps

With your database ready, you're ready to test your Docker container before deploying to Cloud Run.

**→ Next:** [07 - Local Docker Test](07-local-docker-test.md)

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [PostgreSQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)

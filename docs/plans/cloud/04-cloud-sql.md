# 04 - Cloud SQL Setup

```
 gcloud sql instances create churn-risk-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-east1 \
    --root-password='RicketyRocketWaterMice4*' \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=3
```

Creating Cloud SQL instance for POSTGRES_15...done.                                                           
Created [https://sqladmin.googleapis.com/sql/v1beta4/projects/churn-risk-app/instances/churn-risk-db].
NAME           DATABASE_VERSION  LOCATION    TIER         PRIMARY_ADDRESS  PRIVATE_ADDRESS  STATUS
churn-risk-db  POSTGRES_15       us-east1-c  db-f1-micro  34.74.123.47     -                RUNNABLE

```
cloud-sql-proxy churn-risk-app:us-east1:churn-risk-db
psql "host=127.0.0.1 port=5432 sslmode=disable user=postgres dbname=postgres"
```

```
CREATE USER churn_risk_app WITH PASSWORD 'EagleBrinkAlloy53!';
```

```
poetry run python -c "from sqlalchemy import create_engine; from src.core.config import settings; engine = create_engine('postgresql://churn_risk_app:EagleBrinkAlloy53!@127.0.0.1:5432/churn_risk_prod'); conn = engine.connect(); print('Connected to Cloud SQL!'); conn.close()"
```

⏺ The issue is that zsh interprets ! as a history expansion operator. The exclamation mark in your password EagleBrinkAlloy53! is causing the error.

```
poetry run python -c 'from sqlalchemy import create_engine; engine = create_engine("postgresql://churn_risk_app:EagleBrinkAlloy53!@127.0.0.1:5432/churn_risk_prod"); conn = engine.connect(); print("Connected to Cloud SQL!"); conn.close()'
```

Instance Connection Name:  `churn-risk-app:us-east1:churn-risk-db`

**Estimated Time:** 20-30 minutes
**Cost:** ~$7/month (db-f1-micro), covered by free tier credits
**Prerequisites:** Guides 01-03 completed

---

## Overview

Create a managed PostgreSQL database on Cloud SQL. This will replace your local docker-compose PostgreSQL in production.

**What You'll Create:**
- Cloud SQL PostgreSQL instance (version 15)
- Database user and password
- Database named `churn_risk_prod`
- Private IP for secure connections

---

## Step 1: Create Cloud SQL Instance

### 1.1 Create via Console (Recommended for First Time)

1. Go to **GCP Console → SQL** (or search for "SQL" in top search bar)

2. Click **"CREATE INSTANCE"**

3. Choose **PostgreSQL**

4. Configure instance:

**Instance ID:**
```
churn-risk-db
```

**Password for postgres user:**
- Click "GENERATE" to create a secure password
- **SAVE THIS PASSWORD** - you'll need it later
- Example: `xK9#mL2$pQ7&wR4`

**Database version:**
- Select **PostgreSQL 15**

**Choose a configuration:**
- Select **Development** (cheaper, good for MVP)

**Region:**
- Choose same as your Cloud Run region (e.g., `us-central1`)
- **Important:** Same region = lower latency + lower costs

5. Expand **"Customize your instance"** (optional but recommended):

**Machine configuration:**
- Machine type: **Shared core → db-f1-micro** (1 vCPU, 0.6 GB RAM)
- Cost: ~$7/month
- Sufficient for development and early production

**Storage:**
- Storage type: **SSD**
- Storage capacity: **10 GB** (minimum, auto-increases if needed)
- Enable automatic storage increases: **Yes**

**Connections:**
- **Public IP**: Enable (for now, makes setup easier)
- **Private IP**: Leave disabled for now (can add later)
- Authorized networks: Leave empty (we'll use Cloud SQL Proxy)

**Data Protection:**
- Automated backups: **Enable**
- Backup window: Choose off-peak hours (e.g., 3:00 AM your timezone)
- Point-in-time recovery: **Enable** (requires binary logging)

**Maintenance:**
- Maintenance window: Choose off-peak time
- Order of update: **Any**

6. Click **"CREATE INSTANCE"**

**Expected time:** 5-10 minutes for instance to be created

### 1.2 Create via gcloud CLI (Alternative)

```bash
gcloud sql instances create churn-risk-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=3
```

---

## Step 2: Wait for Instance Creation

### 2.1 Monitor Progress

In GCP Console → SQL → churn-risk-db:
- Status will show: "Creating instance..."
- Progress bar indicates completion
- Usually takes 5-10 minutes

**While waiting:**
- ☕ Get coffee
- 📝 Save your postgres password somewhere secure
- 📋 Note down your instance connection name (appears once created)

### 2.2 Verify Instance Running

Once complete:
- Status shows: **"Ready"** (green checkmark)
- Public IP address is assigned
- Connection name visible (format: `project:region:instance`)

**Save connection name:**
```
project:region:instance = churn-risk-prod-123456:us-central1:churn-risk-db
```

---

## Step 3: Create Production Database

### 3.1 Connect via Cloud SQL Proxy (Local Machine)

Open a new terminal and start the proxy:

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

**Keep this terminal open** - the proxy must run while you're connected.

### 3.2 Connect with psql

In a **new terminal**:

```bash
psql "host=127.0.0.1 port=5432 sslmode=disable user=postgres dbname=postgres"
```

**Enter password when prompted:** (the postgres password you saved earlier)

**Expected:**
```
postgres=#
```

### 3.3 Create Production Database

```sql
CREATE DATABASE churn_risk_prod;
```

**Expected output:**
```
CREATE DATABASE
```

**Verify:**
```sql
\l
```

Should show `churn_risk_prod` in the list.

**Exit psql:**
```sql
\q
```

---

## Step 4: Create Application Database User (Security Best Practice)

### 4.1 Why a Separate User?

**Don't use postgres user in production:**
- postgres has superuser privileges
- If credentials leak, entire database is compromised
- Better to use limited-privilege user for application

### 4.2 Create App User

Reconnect to Cloud SQL:

```bash
psql "host=127.0.0.1 port=5432 sslmode=disable user=postgres dbname=churn_risk_prod"
```

**Create user:**
```sql
CREATE USER churn_risk_app WITH PASSWORD 'GENERATE_A_SECURE_PASSWORD';
```

**Example:**
```sql
CREATE USER churn_risk_app WITH PASSWORD 'aB3#xY9$mN2&qL5';
```

**Save this password** - you'll use it in your application.

**Grant permissions:**
```sql
GRANT ALL PRIVILEGES ON DATABASE churn_risk_prod TO churn_risk_app;
GRANT ALL PRIVILEGES ON SCHEMA public TO churn_risk_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO churn_risk_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO churn_risk_app;
```

**Verify:**
```sql
\du
```

Should show `churn_risk_app` in list.

**Exit:**
```sql
\q
```

---

## Step 5: Test Connection from Local Machine

### 5.1 Update Local .env for Testing

Create `backend/.env.cloud-test`:

```bash
# Cloud SQL connection (via proxy)
DATABASE_URL=postgresql://churn_risk_app:YOUR_APP_PASSWORD@127.0.0.1:5432/churn_risk_prod

# Other settings same as local
ENVIRONMENT=development
SECRET_KEY=test-key
API_V1_PREFIX=/api/v1
```

### 5.2 Test Connection with Python

```bash
cd backend

# Make sure cloud-sql-proxy is running in another terminal

# Test connection
poetry run python -c "from sqlalchemy import create_engine; from src.core.config import settings; engine = create_engine('postgresql://churn_risk_app:YOUR_PASSWORD@127.0.0.1:5432/churn_risk_prod'); conn = engine.connect(); print('Connected to Cloud SQL!'); conn.close()"
```

**Expected output:**
```
Connected to Cloud SQL!
```

---

## Step 6: Configure Cloud SQL for Cloud Run Connection

### 6.1 Enable Cloud SQL Admin API

```bash
gcloud services enable sqladmin.googleapis.com
```

### 6.2 Get Instance Connection Name

```bash
gcloud sql instances describe churn-risk-db --format="value(connectionName)"
```

**Output (save this):**
```
churn-risk-prod-123456:us-central1:churn-risk-db
```

You'll use this when deploying to Cloud Run.

---

## Verification Checklist

Before proceeding:

- [ ] Cloud SQL instance created and running
- [ ] Postgres root password saved securely
- [ ] Production database `churn_risk_prod` created
- [ ] Application user `churn_risk_app` created with password
- [ ] Can connect via Cloud SQL Proxy from local machine
- [ ] Instance connection name saved for later

---

## Important Information to Save

**Write these down - you'll need them:**

```
Instance Connection Name: _________________________________
Postgres Password:        _________________________________
App User Password:        _________________________________
Database Name:            churn_risk_prod
App Username:             churn_risk_app
```

---

## Costs Incurred

**Cloud SQL db-f1-micro:**
- $7.17/month (~$0.01/hour)
- 10 GB SSD: $1.70/month
- **Total: ~$8.87/month**

**With $300 credits:** Covered for 33+ months

---

## Troubleshooting

### Problem: Instance creation fails

**Solutions:**
- Check billing is enabled
- Verify region is supported
- Try a different instance name
- Check quota limits in GCP Console

### Problem: Can't connect via Cloud SQL Proxy

**Solutions:**
- Ensure proxy is running: `ps aux | grep cloud-sql-proxy`
- Check instance connection name is correct
- Verify Cloud SQL Admin API is enabled
- Check firewall isn't blocking port 5432

### Problem: "password authentication failed"

**Solutions:**
- Verify you're using correct password
- Check username is correct (postgres vs churn_risk_app)
- Ensure user was created successfully
- Try resetting password in GCP Console

### Problem: Database connection times out

**Solutions:**
- Check Cloud SQL instance is running (status "Ready")
- Verify cloud-sql-proxy is connected
- Check local firewall settings
- Try restarting cloud-sql-proxy

---

## Next Steps

With Cloud SQL running, you're ready to set up Secret Manager.

**→ Next:** [05 - Secret Manager Setup](05-secret-manager.md)

---

## Additional Resources

- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Cloud SQL Proxy Guide](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [Connecting from Cloud Run](https://cloud.google.com/sql/docs/postgres/connect-run)

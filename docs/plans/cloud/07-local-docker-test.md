# 07 - Local Docker Test

**Estimated Time:** 15-20 minutes
**Cost:** $0 (testing locally)
**Prerequisites:** Guides 01-06 completed

---

## Overview

Test your Docker container locally before deploying to Cloud Run. This catches configuration issues early.

**What You'll Test:**
- Docker image builds correctly
- Container starts without errors
- Can connect to Cloud SQL via proxy
- Health check endpoint works
- API endpoints respond correctly
- Environment variables configured properly

---

## Step 1: Build Production Docker Image

### 1.1 Navigate to Backend Directory

```bash
cd backend
```

### 1.2 Build Image

```bash
docker build -t churn-risk-backend:test .
```

**Expected output:**
```
[+] Building 120.5s (18/18) FINISHED
 => [internal] load build definition
 => [builder 1/6] FROM python:3.11-slim
 ...
 => naming to docker.io/library/churn-risk-backend:test
```

**Build time:** 2-5 minutes (uses cache if you've built before)

### 1.3 Verify Image Size

```bash
docker images churn-risk-backend:test
```

**Should show:**
```
REPOSITORY            TAG   IMAGE ID      CREATED        SIZE
churn-risk-backend    test  abc123def456  1 minute ago   250MB
```

**Target size:** 200-300MB (multi-stage build keeps it small)

---

## Step 2: Prepare Test Environment

### 2.1 Start Cloud SQL Proxy

In a **separate terminal**, start the proxy:

```bash
cloud-sql-proxy churn-risk-prod-123456:us-central1:churn-risk-db
```

**Keep running** during all tests.

### 2.2 Create Test Environment File

Create `backend/.env.docker-test`:

```bash
# Database (via Cloud SQL Proxy)
DATABASE_URL=postgresql://churn_risk_app:YOUR_DB_PASSWORD@host.docker.internal:5432/churn_risk_prod

# Application
ENVIRONMENT=production
SECRET_KEY=test-secret-key-for-docker
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Firebase (using local file for now)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# OpenRouter
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=google/gemini-2.5-flash

# HubSpot
HUBSPOT_CLIENT_ID=your-hubspot-client-id
HUBSPOT_CLIENT_SECRET=your-hubspot-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8080/api/v1/integrations/hubspot/callback

# Port (Cloud Run uses 8080)
PORT=8080
```

**Replace placeholders** with your actual values from `backend/.env`.

**Note:** We're using local values for testing. In production, these will come from Secret Manager.

---

## Step 3: Run Container Locally

### 3.1 Start Container

```bash
docker run --rm \
  --name churn-risk-test \
  -p 8080:8080 \
  --env-file .env.docker-test \
  -v "$(pwd)/../firebase-credentials.json:/app/firebase-credentials.json:ro" \
  churn-risk-backend:test
```

**What this does:**
- `--rm`: Remove container when stopped
- `--name`: Name it for easy reference
- `-p 8080:8080`: Map port 8080 (Cloud Run default)
- `--env-file`: Load environment variables
- `-v`: Mount Firebase credentials (read-only)
- `:ro`: Read-only mount for security

**Expected output:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Keep this running** - switch to a new terminal for testing.

### 3.2 Alternative: Run with Docker Compose (Optional)

Create `backend/docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    image: churn-risk-backend:test
    ports:
      - "8080:8080"
    env_file:
      - .env.docker-test
    volumes:
      - ../firebase-credentials.json:/app/firebase-credentials.json:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"  # Linux support
```

**Run:**
```bash
docker-compose -f docker-compose.test.yml up
```

---

## Step 4: Test API Endpoints

### 4.1 Test Health Check

```bash
curl http://localhost:8080/health
```

**Expected response:**
```json
{"status":"healthy","environment":"production"}
```

### 4.2 Test API Root

```bash
curl http://localhost:8080/api/v1/
```

**Expected response:**
```json
{"message":"Churn Risk API","version":"1.0.0"}
```

### 4.3 Test API Docs

Open browser:
```
http://localhost:8080/api/v1/docs
```

**Should show:** Swagger/OpenAPI documentation interface

### 4.4 Test Database Connectivity

```bash
curl http://localhost:8080/api/v1/ -v
```

Look for successful startup in container logs (no database connection errors).

---

## Step 5: Test with Sample Data (Optional)

### 5.1 Create Test Tenant and User

Create `backend/test_create_tenant.py`:

```python
#!/usr/bin/env python3
"""Create test tenant for local Docker testing."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid

from src.models.tenant import Tenant, PlanTier
from src.models.user import User, UserRole

def create_test_data():
    """Create test tenant and user."""
    database_url = os.environ.get("DATABASE_URL")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create tenant
        tenant = Tenant(
            name="Test Company",
            subdomain="testco",
            plan_tier=PlanTier.STARTER
        )
        session.add(tenant)
        session.flush()
        
        print(f"✅ Created tenant: {tenant.id}")
        
        # Create admin user
        user = User(
            tenant_id=tenant.id,
            firebase_uid="test-firebase-uid-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.ADMIN
        )
        session.add(user)
        session.commit()
        
        print(f"✅ Created user: {user.id}")
        print(f"\nTenant ID: {tenant.id}")
        print(f"User ID: {user.id}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(".env.docker-test")
    create_test_data()
```

**Run:**
```bash
poetry run python test_create_tenant.py
```

---

## Step 6: Monitor Container Logs

### 6.1 View Logs

In the terminal running the container, you should see:

```
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     127.0.0.1:53234 - "GET /health HTTP/1.1" 200
INFO:     127.0.0.1:53235 - "GET /api/v1/ HTTP/1.1" 200
```

### 6.2 Check for Errors

**Look for:**
- ✅ No database connection errors
- ✅ No missing environment variable errors
- ✅ All endpoints responding with 200 status
- ✅ No Python exceptions or tracebacks

**Common issues to watch for:**
- ❌ "connection refused" = Cloud SQL Proxy not running
- ❌ "password authentication failed" = wrong database password
- ❌ "module not found" = missing dependency
- ❌ "permission denied" = file mount issue

---

## Step 7: Performance Check

### 7.1 Test Response Time

```bash
time curl http://localhost:8080/health
```

**Should be:** < 100ms for health check

### 7.2 Test Under Light Load

```bash
# Send 10 requests
for i in {1..10}; do
  curl -s http://localhost:8080/health > /dev/null
  echo "Request $i complete"
done
```

**Should:** All complete successfully

---

## Step 8: Stop Container

### 8.1 Stop Test Container

Press `Ctrl+C` in the terminal running the container.

**Or, if running in background:**
```bash
docker stop churn-risk-test
```

### 8.2 Clean Up

```bash
# Remove test environment file (contains secrets)
rm .env.docker-test

# Optional: Remove test image (if rebuilding)
# docker rmi churn-risk-backend:test
```

---

## Verification Checklist

Before proceeding to Cloud Run deployment:

- [ ] Docker image builds without errors
- [ ] Image size < 400MB
- [ ] Container starts successfully
- [ ] Can connect to Cloud SQL via proxy
- [ ] Health check endpoint returns 200
- [ ] API root endpoint returns correct JSON
- [ ] API docs accessible
- [ ] No errors in container logs
- [ ] All environment variables loaded correctly
- [ ] Firebase credentials mounted successfully

---

## Troubleshooting

### Problem: "Cannot connect to the Docker daemon"

**Solution:**
```bash
# Start Docker Desktop
# Or on Linux: sudo systemctl start docker
```

### Problem: Container immediately exits

**Solution:**
```bash
# Check logs
docker logs churn-risk-test

# Common causes:
# - Missing environment variable
# - Python import error
# - Database connection failed at startup
```

### Problem: "host.docker.internal: Name or service not known"

**Solution (Linux only):**
```bash
# Use Docker bridge IP instead
docker run ... \
  -e DATABASE_URL="postgresql://churn_risk_app:PASSWORD@172.17.0.1:5432/churn_risk_prod" \
  ...

# Or add extra_hosts
docker run ... \
  --add-host=host.docker.internal:host-gateway \
  ...
```

### Problem: "Permission denied" for firebase-credentials.json

**Solution:**
```bash
# Check file exists
ls -la ../firebase-credentials.json

# Ensure readable
chmod 644 ../firebase-credentials.json

# Verify mount path in container
docker run --rm churn-risk-backend:test ls -la /app/firebase-credentials.json
```

### Problem: Container starts but API doesn't respond

**Solutions:**
```bash
# Check if port is already in use
lsof -i :8080

# Try different port
docker run -p 8081:8080 ...

# Check container is running
docker ps

# Check container logs
docker logs churn-risk-test
```

### Problem: Database connection fails

**Solutions:**
- Verify Cloud SQL Proxy is running: `ps aux | grep cloud-sql-proxy`
- Check DATABASE_URL format in .env.docker-test
- Test connection from host: `psql "host=127.0.0.1 port=5432 user=churn_risk_app dbname=churn_risk_prod"`
- Ensure password is correct

---

## What You've Accomplished

✅ Built production Docker image
✅ Tested container locally with Cloud SQL
✅ Verified all API endpoints work
✅ Confirmed environment variables configured correctly
✅ Tested database connectivity through proxy
✅ Ready for Cloud Run deployment

---

## Docker Image Details

**Final image includes:**
- Python 3.11 slim base
- All application dependencies (no dev dependencies)
- Application code from `src/`
- Alembic migrations
- Non-root user (appuser)
- Health check configuration
- Optimized for Cloud Run

**Image is ready to deploy to Google Container Registry.**

---

## Next Steps

With a working Docker image tested locally, you're ready to deploy to Cloud Run.

**→ Next:** [08 - Cloud Run Deployment](08-cloud-run-deployment.md)

---

## Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Cloud Run Container Contract](https://cloud.google.com/run/docs/container-contract)
- [Testing Containers Locally](https://cloud.google.com/run/docs/testing/local)

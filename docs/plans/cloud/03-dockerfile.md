# 03 - Dockerfile Creation - COMPLETED

Here's a summary of what we accomplished:

  ✅ Dockerfile Setup Complete

  Created Files:
  1. backend/Dockerfile - Production-ready multi-stage build
    - Updated for Poetry 2.x syntax (--without dev instead of --no-dev)
    - Added --no-root flag for dependency-only installation
    - Multi-stage build for smaller final image
    - Non-root user (appuser) for security
    - Health check compatible with Cloud Run
  2. backend/.dockerignore - Security and optimization
    - Excludes secrets (.env, firebase-credentials.json)
    - Excludes development files (tests/, .git/, etc.)
    - Reduces image size and build time
  3. backend/.env.docker - Docker-specific environment variables
    - Uses host.docker.internal for database connectivity from container

  Test Results:
  - ✅ Docker image built successfully: churn-risk-backend:local (541MB)
  - ✅ Container runs successfully on port 8080
  - ✅ Health check endpoint responds: {"status":"healthy","environment":"development"}
  - ✅ API root endpoint responds: {"message":"Churn Risk API","version":"0.1.0"}
  - ✅ Database connectivity verified from container
  - ✅ Clean shutdown without errors

  Key Fixes Applied:
  - Updated Poetry syntax for v2.2.1 compatibility
  - Fixed case sensitivity (AS builder instead of as builder)
  - Added --no-root flag for dependency installation
  - Used JSON array format for CMD (better signal handling)
  - Created complete environment file with all required variables
  

**Estimated Time:** 15-20 minutes
**Prerequisites:** Guides 01-02 completed

---

## Overview

Create a production-optimized Dockerfile for your FastAPI backend. This container will run on Cloud Run.

**Best Practices (2025):**
- Multi-stage builds for smaller images
- Non-root user for security
- Proper dependency management with Poetry
- Health checks for Cloud Run
- Minimal base image (Python slim)

---

## Step 1: Create Production Dockerfile

### 1.1 Create Dockerfile

Create `backend/Dockerfile`:

```dockerfile
# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

#-----------------------------------------------------------
# Final stage - smaller image
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Environment variables for Cloud Run
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port (Cloud Run will use this)
EXPOSE 8080

# Health check (Cloud Run compatible)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run the application
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT}
```

**Save this as:** `backend/Dockerfile`

---

## Step 2: Create .dockerignore

### 2.1 Create .dockerignore File

Create `backend/.dockerignore` to exclude unnecessary files:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.pytest_cache/
.coverage
htmlcov/

# Environment files (DO NOT include in container)
.env
.env.local
.env.*.local

# Secrets (DO NOT include in container)
firebase-credentials.json
*.key
*.pem

# Development
.git
.gitignore
README.md
tests/
scripts/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite
alembic/versions/*_local_*

# Logs
*.log
```

**Save this as:** `backend/.dockerignore`

**Why this matters:**
- Reduces image size
- Prevents secrets from being baked into image
- Faster builds (fewer files to copy)
- Security (no .env files in production image)

---

## Step 3: Update pyproject.toml for Production

### 3.1 Verify Dependencies

Ensure `backend/pyproject.toml` has all runtime dependencies:

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
psycopg2-binary = "^2.9.9"  # PostgreSQL driver
pydantic = {extras = ["email"], version = "^2.5.3"}
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
httpx = "^0.26.0"
firebase-admin = "^6.4.0"
python-dotenv = "^1.0.0"
tenacity = "^8.2.3"
google-cloud-secret-manager = "^2.18.0"  # Add if not present
```

**If you need to add google-cloud-secret-manager:**
```bash
cd backend
poetry add google-cloud-secret-manager
```

---

## Step 4: Create Cloud Run Startup Script (Optional but Recommended)

### 4.1 Create startup.sh

Create `backend/startup.sh`:

```bash
#!/bin/bash
set -e

echo "Starting Churn Risk API..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8080}"

# Run database migrations on startup (optional - can be done separately)
# echo "Running database migrations..."
# alembic upgrade head

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

**Make it executable:**
```bash
chmod +x backend/startup.sh
```

**Update Dockerfile CMD (if using startup script):**
```dockerfile
CMD ["./startup.sh"]
```

**Note:** Running migrations on startup is optional. For production, it's often better to run migrations separately to avoid race conditions with multiple containers.

---

## Step 5: Build Docker Image Locally

### 5.1 Build the Image

From your project root:

```bash
cd backend
docker build -t churn-risk-backend:local .
```

**Expected output:**
```
[+] Building 120.5s (18/18) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.2kB
 ...
 => exporting to image
 => => writing image sha256:abc123...
 => => naming to docker.io/library/churn-risk-backend:local
```

**Build time:** 2-5 minutes (first time, uses cache after)

### 5.2 Verify Image Created

```bash
docker images | grep churn-risk
```

**Should show:**
```
churn-risk-backend  local  abc123def456  2 minutes ago  250MB
```

**Image size should be:** 200-300MB (multi-stage build makes it smaller)

---

## Step 6: Test Docker Image Locally

### 6.1 Make Sure Docker Compose is Running

Your local PostgreSQL should be running:

```bash
docker-compose up -d
```

### 6.2 Run the Container

```bash
docker run --rm \
  --name churn-risk-test \
  -p 8080:8080 \
  -e DATABASE_URL="postgresql://postgres:password@host.docker.internal:5432/churn_risk_dev" \
  -e ENVIRONMENT="development" \
  -e SECRET_KEY="test-secret-key-for-local-docker" \
  -e API_V1_PREFIX="/api/v1" \
  -e CORS_ORIGINS="http://localhost:3000" \
  -e FIREBASE_PROJECT_ID="${FIREBASE_PROJECT_ID}" \
  -e FIREBASE_CREDENTIALS_PATH="/app/firebase-credentials.json" \
  -v "$(pwd)/../firebase-credentials.json:/app/firebase-credentials.json:ro" \
  churn-risk-backend:local
```

**Note:** `host.docker.internal` allows the container to connect to your local PostgreSQL.

**On Linux, use:**
```bash
-e DATABASE_URL="postgresql://postgres:password@172.17.0.1:5432/churn_risk_dev" \
```

### 6.3 Test the API

In a new terminal:

```bash
# Test health check
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","environment":"development"}

# Test API root
curl http://localhost:8080/api/v1/

# Expected response:
# {"message":"Churn Risk API","version":"1.0.0"}
```

### 6.4 Stop the Container

```bash
docker stop churn-risk-test
```

Or press `Ctrl+C` in the terminal running the container.

---

## Step 7: Optimize Dockerfile (Optional but Recommended)

### 7.1 Layer Caching Optimization

The Dockerfile is already optimized with:
- ✅ Multi-stage builds (smaller final image)
- ✅ Dependency installation before code copy (better caching)
- ✅ Non-root user (security)
- ✅ Health check (Cloud Run compatibility)

### 7.2 Further Optimizations (if needed)

**If image is too large (>300MB):**

1. Use alpine base instead of slim:
```dockerfile
FROM python:3.11-alpine
```
(But requires more build dependencies)

2. Remove unnecessary packages after install:
```dockerfile
RUN poetry install --no-dev && \
    rm -rf ~/.cache/pypoetry
```

---

## Troubleshooting

### Problem: "poetry: command not found" during build

**Solution:**
The Dockerfile installs Poetry - this error means the builder stage failed. Check:
- Internet connection during build
- Poetry installation script URL is correct

### Problem: "Failed to solve with frontend dockerfile.v0"

**Solution:**
- Check Dockerfile syntax (no tabs, proper indentation)
- Ensure all COPY paths exist
- Verify pyproject.toml and poetry.lock are in backend/

### Problem: Container runs but can't connect to database

**Solution:**
- Use `host.docker.internal` on Mac/Windows
- Use `172.17.0.1` on Linux
- Verify docker-compose postgres is running: `docker-compose ps`

### Problem: "Module not found" when container starts

**Solution:**
- Ensure all dependencies in pyproject.toml
- Run `poetry lock` before building
- Clear Docker cache: `docker build --no-cache`

### Problem: Image is too large (>500MB)

**Solution:**
- Ensure .dockerignore is working
- Use multi-stage build (already in Dockerfile)
- Don't include test data or large files

---

## Checklist

Before proceeding:

- [ ] Dockerfile created in `backend/`
- [ ] .dockerignore created in `backend/`
- [ ] Docker image builds successfully
- [ ] Image size is reasonable (< 400MB)
- [ ] Container runs locally
- [ ] Health check endpoint responds
- [ ] Can connect to local database from container

---

## What You've Accomplished

✅ Created production-ready Dockerfile
✅ Configured .dockerignore for security
✅ Built Docker image locally
✅ Tested container connects to database
✅ Verified health check works

---

## Costs So Far

**Total spend:** $0
**Credits used:** $0.00
**Remaining credits:** $300.00

*(Still no cloud resources created)*

---

## Next Steps

With a working Docker image, you're ready to set up Cloud SQL.

**→ Next:** [04 - Cloud SQL Setup](04-cloud-sql.md)

---

## Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Cloud Run Container Requirements](https://cloud.google.com/run/docs/container-contract)
- [Poetry in Docker](https://python-poetry.org/docs/master/faq/#i-dont-want-poetry-to-manage-my-virtual-environments-can-i-disable-it)

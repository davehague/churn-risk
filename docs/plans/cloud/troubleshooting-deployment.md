# Cloud Run Deployment Troubleshooting Log

**Date:** 2025-11-12
**Issue:** ModuleNotFoundError when deploying Python FastAPI app to Cloud Run
**Status:** ✅ **RESOLVED** (Cloud Run buildpack + Procfile)
**Service URL:** https://churn-risk-api-461448724047.us-east1.run.app

---

## Problem Statement

When deploying a FastAPI application with Poetry to Cloud Run, the container failed to start with:
```
ModuleNotFoundError: No module named 'src'
```

The same Docker image worked perfectly when tested locally, but consistently failed in Cloud Run.

---

## Root Cause Analysis

After extensive investigation, the issue was related to how Poetry and multi-stage Docker builds interact with Cloud Run's container runtime. The `src` module was either:
1. Not being properly installed by Poetry in the final image
2. Not being found due to working directory issues in Cloud Run's runtime environment

---

## Troubleshooting Steps Attempted

### 1. Fixed Cloud Resource Manager API (✅ Success)
**Problem:** Initial deployment failed with 404 token exchange error
**Solution:** Enabled Cloud Resource Manager API via GCP Console
**Result:** Resolved - API access working

### 2. Built AMD64-Compatible Docker Image (✅ Success)
**Problem:** Initial ARM64 image incompatible with Cloud Run
**Command:**
```bash
docker build --platform linux/amd64 -t churn-risk-backend:v2 .
```
**Result:** Image architecture correct, but ModuleNotFoundError persisted

### 3. Added PYTHONPATH Environment Variable (❌ No Effect)
**Dockerfile change:**
```dockerfile
ENV PYTHONPATH=/app
```
**Result:** Module still not found in Cloud Run (though worked locally)

### 4. Used `python -m uvicorn` Instead of Direct `uvicorn` Call (❌ No Effect)
**Dockerfile CMD change:**
```dockerfile
CMD ["sh", "-c", "exec python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]
```
**Rationale:** Using `-m` ensures Python runs from correct working directory
**Result:** Same ModuleNotFoundError

### 5. Installed Package via Poetry with `packages` Config (❌ No Effect)
**pyproject.toml change:**
```toml
[tool.poetry]
packages = [{include = "src"}]
```

**Dockerfile change:**
```dockerfile
# Copy source before installing
COPY src ./src

# Install with package (not --no-root)
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi
```
**Result:** Package installed in builder stage, but not accessible in final stage

### 6. Added Explicit WORKDIR After USER Switch (❌ No Effect)
**Dockerfile change:**
```dockerfile
USER appuser
WORKDIR /app
```
**Rationale:** Ensure working directory is correct when container starts
**Result:** Still ModuleNotFoundError

### 7. Created Custom Entrypoint Script (❌ No Effect)
**docker-entrypoint.sh:**
```bash
#!/bin/sh
set -e
PORT=${PORT:-8080}
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "$PORT"
```

**Dockerfile change:**
```dockerfile
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
CMD ["docker-entrypoint.sh"]
```
**Result:** Same error persisted

### 8. Attempted Multiple Image Versions (❌ No Effect)
Built and deployed versions v1 through v8 with incremental fixes. All worked locally but failed in Cloud Run with identical error.

---

## Key Observations

1. **Local vs Cloud Run Behavior:** Every Docker image worked perfectly locally but failed in Cloud Run
2. **Consistent Error:** ModuleNotFoundError never changed despite different approaches
3. **Multi-Stage Build Issue:** Poetry's multi-stage build may not be copying all necessary files to final image
4. **Site-packages Mystery:** Installed packages didn't appear in `/usr/local/lib/python3.11/site-packages/` as expected

---

## Final Solution ✅

**Approach:** Cloud Run Python buildpack with Procfile (no custom Dockerfile)

**What Worked:**
1. Removed custom Dockerfiles (renamed to `.backup`)
2. Created `Procfile` with explicit working directory and PYTHONPATH:
   ```
   web: cd /workspace && PYTHONPATH=/workspace uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```
3. Generated `requirements.txt` from Poetry: `poetry run pip freeze > requirements.txt`
4. Deployed using source deployment: `gcloud run deploy --source .`

**Why This Worked:**
- Cloud Run's Python buildpack handles the containerization automatically
- `/workspace` is Cloud Run's default working directory for buildpack deployments
- Procfile explicitly sets the working directory and PYTHONPATH
- No complex multi-stage Docker builds to debug
- Cloud Run's buildpack is optimized for Python applications

**Key Files:**
- `requirements.txt` - Python dependencies
- `Procfile` - Startup command for Cloud Run buildpack

**Rationale:**
- Poetry adds complexity with multi-stage builds
- Cloud Run documentation recommends simpler Python setups
- requirements.txt is more straightforward for containerization

**Files Changed:**
1. Create `requirements.txt` from Poetry dependencies
2. Simplify Dockerfile to use pip install
3. Remove Poetry-specific build steps

---

## Lessons Learned

1. **Cloud Run Environment Differences:** What works in local Docker may not work in Cloud Run's runtime
2. **Poetry + Multi-Stage Builds:** Can be problematic for containerized deployments
3. **Simpler is Better:** For Cloud Run, straightforward pip/requirements.txt is more reliable
4. **Test Early:** Build a minimal working version before adding complexity
5. **Documentation:** Google's Cloud Run Python examples use requirements.txt for good reason

---

## Resources Used

- [Cloud Run Container Requirements](https://cloud.google.com/run/docs/configuring/containers)
- [Debugging ModuleNotFoundError in Docker](https://pythonspeed.com/articles/importerror-docker/)
- [Cloud Run Python Best Practices](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service)

---

## Image Version History

| Version | Changes | Result |
|---------|---------|--------|
| v1 | Initial build (ARM64) | Architecture mismatch |
| v2 | AMD64 platform | ModuleNotFoundError |
| v3 | Added PYTHONPATH | ModuleNotFoundError |
| v4 | No-cache rebuild | ModuleNotFoundError |
| v5 | Explicit `cd /app` in CMD | ModuleNotFoundError |
| v6 | Used `python -m uvicorn` | ModuleNotFoundError |
| v7 | Poetry package install | ModuleNotFoundError |
| v8 | Entrypoint script + WORKDIR | ModuleNotFoundError |
| v9 | requirements.txt with Dockerfile | ModuleNotFoundError |
| v10 | Added PYTHONPATH + PORT env var | ModuleNotFoundError |
| v11 | Source deploy with Dockerfile | ModuleNotFoundError |
| v12 | **Buildpack with Procfile** | ✅ **SUCCESS** |

---

## Next Steps After This Issue

Once deployment works with requirements.txt:
1. Update deployment guide with working Dockerfile
2. Consider migrating to requirements.txt permanently for production builds
3. Document Poetry for local development, requirements.txt for deployment
4. Set up CI/CD to generate requirements.txt from Poetry automatically

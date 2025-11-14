# Daily Development Guide

**For**: Developers returning to the project after a break
**Time**: 5-10 minutes to get running
**Prerequisite**: You've already set up the project before (see [First-Time Setup](./first-time-setup.md) if not)

---

## Quick Start (TL;DR)

```bash
# Terminal 1: Start local services
docker-compose up -d

# Terminal 2: Start backend
cd backend
poetry run uvicorn src.main:app --reload --port 8000

# Terminal 3: Start frontend
cd frontend
npm run dev
```

**Access**:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/v1/docs
- Database: localhost:5432 (via psql or GUI)

---

## Step-by-Step Startup

### 1. Start Docker Services (30 seconds)

PostgreSQL and Redis run in Docker containers.

```bash
# From project root
docker-compose up -d
```

**Verify it's running**:
```bash
docker-compose ps
# Should show postgres and redis containers as "Up"
```

**If it fails**: Docker Desktop might not be running. Start Docker Desktop first.

---

### 2. Start Backend (1 minute)

```bash
cd backend

# Start the FastAPI server
poetry run uvicorn src.main:app --reload --port 8000
```

**You should see**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Quick health check**:
- Visit: http://localhost:8000/health
- Should return: `{"status":"healthy","environment":"development"}`

**If it fails**:
- Check `.env` file exists in `backend/` directory
- Check Docker containers are running (database connection)
- See [Troubleshooting](#troubleshooting) section below

---

### 3. Start Frontend (1 minute)

```bash
cd frontend

# Start the Nuxt dev server
npm run dev
```

**You should see**:
```
Nuxt 3.x.x with Nitro x.x.x
  > Local:    http://localhost:3000/
```

**Quick test**:
- Visit: http://localhost:3000
- Should see the landing page

**If it fails**:
- Try `rm -rf .nuxt .output && npm run dev` (clear cache)
- Check `node_modules` exists (run `npm install` if not)

---

## Verification Checklist

Once everything is running, verify the full stack works:

### ✅ Backend Check (30 seconds)

```bash
# In a new terminal
curl http://localhost:8000/health
# Should return: {"status":"healthy","environment":"development"}

curl http://localhost:8000/api/v1/
# Should return API info with version
```

### ✅ Database Check (30 seconds)

```bash
cd backend
poetry run python -c "from src.core.database import engine; print('✅ Database connected' if engine else '❌ Failed')"
```

### ✅ Frontend Check (30 seconds)

1. Open http://localhost:3000
2. Click "Get Started" or "Sign In"
3. Should load without errors in console

### ✅ Full Auth Flow (2 minutes)

1. Go to http://localhost:3000/register
2. Create test account:
   - Email: `test@example.com`
   - Password: `password123`
   - Company: `Test Co`
   - Subdomain: `testco` (must be unique)
3. Should redirect to login
4. Login with same credentials
5. Should reach dashboard

---

## What If Something Broke While You Were Away?

### Check 1: Git Changes
Someone might have pushed changes that require new dependencies or migrations.

```bash
# Pull latest changes
git pull

# Backend: Update dependencies
cd backend
poetry install

# Backend: Run new migrations
poetry run alembic upgrade head

# Frontend: Update dependencies
cd frontend
npm install
```

### Check 2: Database State
If someone added migrations, your local database might be out of sync.

```bash
cd backend

# Check current migration version
poetry run alembic current

# Check if there are pending migrations
poetry run alembic history

# Apply any pending migrations
poetry run alembic upgrade head
```

### Check 3: Environment Variables
New features might require new environment variables.

```bash
# Check if .env.example changed
cd backend
git diff HEAD~10 .env.example

# Add any new required variables to your .env
```

---

## Common Development Tasks

### Run Tests

```bash
cd backend
poetry run pytest                    # All tests (57 total)
poetry run pytest tests/unit/        # Unit tests only
poetry run pytest tests/integration/ # Integration tests only
poetry run pytest -v                 # Verbose output
```

### Database Operations

```bash
cd backend

# Create new migration (after model changes)
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history

# Connect to database via psql
docker exec -it churn_risk_dev psql -U postgres -d churn_risk_dev

# Connect via DBeaver (GUI)
# See connection details below
```

**DBeaver Connection**:

If you prefer a GUI, use these connection settings in DBeaver:

1. **Create New Connection** → PostgreSQL
2. **Connection Settings**:
   - Host: `localhost`
   - Port: `5432`
   - Database: `churn_risk_dev`
   - Username: `postgres`
   - Password: `password`
   - Show all databases: ✓ (checked)
3. **Test Connection** → Should succeed
4. **Save**

**Quick Access**:
- Tables are in: `churn_risk_dev` → `Schemas` → `public` → `Tables`
- View all 11 tables: tenants, users, integrations, companies, contacts, tickets, ticket_topics, ticket_topic_assignments, churn_risk_cards, churn_risk_comments, alembic_version

### Code Quality

```bash
cd backend

# Lint
poetry run ruff check src

# Auto-fix linting issues
poetry run ruff check --fix src

# Format code
poetry run black src

# Type check
poetry run mypy src
```

### Clear Caches (When Things Get Weird)

```bash
# Backend: Clear Python cache
cd backend
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Frontend: Clear Nuxt cache
cd frontend
rm -rf .nuxt .output node_modules/.cache
npm run dev
```

---

## Project Structure Reminder

```
churn-risk-app/
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── api/         # Route handlers
│   │   ├── core/        # Config, database, auth
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic (AI, integrations)
│   │   └── integrations/# External APIs (HubSpot)
│   ├── tests/           # Test files
│   ├── alembic/         # Database migrations
│   └── .env             # Local environment variables
│
├── frontend/            # Nuxt 3 frontend
│   ├── pages/          # File-based routing
│   ├── components/     # Vue components
│   ├── composables/    # Composition API (useAuth, etc.)
│   ├── stores/         # Pinia state management
│   └── types/          # TypeScript types
│
├── docs/
│   ├── dev/            # This guide + setup docs
│   ├── operations/     # GCP operations, deployment
│   └── plans/          # Implementation plans
│
└── docker-compose.yml  # Local PostgreSQL + Redis
```

**See**: [Architecture Overview](./architecture-overview.md) for detailed architecture.

---

## Common Commands Quick Reference

### Docker
```bash
docker-compose up -d              # Start services
docker-compose ps                 # Check status
docker-compose logs postgres      # View postgres logs
docker-compose down               # Stop services
docker-compose down -v            # Stop and remove volumes (fresh DB)
```

### Backend
```bash
cd backend
poetry run uvicorn src.main:app --reload --port 8000  # Start server
poetry run pytest                                      # Run tests
poetry run alembic upgrade head                        # Run migrations
poetry run python scripts/smoke_test.py                # Quick integration test
```

### Frontend
```bash
cd frontend
npm run dev           # Start dev server
npm run build         # Build for production
npm run typecheck     # Check TypeScript
npm run generate      # Generate static site (for deployment)
```

### Git
```bash
git status                    # Check what changed
git pull                      # Get latest changes
git add .                     # Stage all changes
git commit -m "message"       # Commit changes
git push                      # Push to remote
```

---

## Troubleshooting

### "Cannot connect to database"

**Symptoms**: Backend fails to start, database connection errors

**Solutions**:
1. Check Docker is running: `docker-compose ps`
2. Restart Docker services: `docker-compose restart`
3. Check connection string in `backend/.env`:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev
   ```
4. Try connecting manually:
   ```bash
   docker exec -it churn_risk_dev psql -U postgres -d churn_risk_dev
   ```

### "Port already in use"

**Symptoms**: `Address already in use` when starting backend/frontend

**Solutions**:
```bash
# Find process using port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Find process using port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### "Module not found" errors

**Symptoms**: Python import errors or npm errors

**Solutions**:
```bash
# Backend: Reinstall dependencies
cd backend
poetry install

# Frontend: Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
```

### "Firebase error: app does not exist"

**Symptoms**: Backend fails with Firebase initialization error

**Solutions**:
1. Check `FIREBASE_CREDENTIALS_PATH` in `backend/.env`
2. Verify path is relative to backend directory: `../firebase-credentials.json`
3. Check file exists: `ls -la ../firebase-credentials.json` (from backend dir)

### "CORS errors" in browser

**Symptoms**: API calls fail with CORS errors in browser console

**Solutions**:
1. Check `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3000`
2. Restart backend after changing `.env`
3. Clear browser cache / use incognito window

### Frontend shows blank page

**Symptoms**: http://localhost:3000 loads but shows nothing

**Solutions**:
```bash
cd frontend
rm -rf .nuxt .output node_modules/.cache
npm run dev
```

Check browser console for JavaScript errors.

---

## Production Access

While developing locally, you can access production:

- **Production Frontend**: http://136.110.172.10/
- **Production Backend**: https://churn-risk-api-461448724047.us-east1.run.app
- **Production Docs**: https://churn-risk-api-461448724047.us-east1.run.app/api/v1/docs

**See**: [GCP Daily Operations](../operations/gcp-daily-operations.md) for production monitoring.

---

## Shutting Down

When you're done for the day:

```bash
# Stop backend/frontend: Ctrl+C in their terminals

# Stop Docker services (keeps data)
docker-compose stop

# OR stop and remove containers (removes data)
docker-compose down

# OR stop and remove everything including volumes (fresh start next time)
docker-compose down -v
```

**Recommendation**: Use `docker-compose stop` to preserve your local data.

---

## Next Steps After Starting Up

Depending on what you're working on:

- **Adding features**: See [Architecture Overview](./architecture-overview.md) for patterns
- **Backend work**: See [backend/CLAUDE.md](../../backend/CLAUDE.md) for backend-specific patterns
- **Frontend work**: See [frontend/CLAUDE.md](../../frontend/CLAUDE.md) for frontend patterns
- **Testing**: See [Testing Guide](./testing-guide.md) for test patterns
- **Deploying**: See [GCP Operations](../operations/gcp-daily-operations.md) for deployment

---

**Last Updated**: 2025-11-14

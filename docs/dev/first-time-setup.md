# First-Time Developer Setup

**For**: New developers setting up the project for the first time
**Time**: 30-60 minutes (depending on download speeds)
**Prerequisite**: macOS or Linux (Windows with WSL2)

---

## What You're Building

A multi-tenant SaaS app that analyzes HubSpot support tickets using AI to detect churn risk.

**Stack**:
- **Backend**: Python 3.11, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: Vue 3, Nuxt 3, TypeScript, Tailwind CSS
- **Auth**: Firebase
- **AI**: OpenRouter (LLM gateway)
- **Integration**: HubSpot OAuth

**Architecture**: See [Architecture Overview](./architecture-overview.md) for details.

---

## Prerequisites Installation

### 1. Install Homebrew (macOS/Linux)

```bash
# Check if already installed
brew --version

# If not installed:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python 3.11

```bash
# Install Python 3.11
brew install python@3.11

# Verify installation
python3.11 --version
# Should show: Python 3.11.x
```

### 3. Install Poetry (Python Package Manager)

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc

# Verify installation
poetry --version
# Should show: Poetry (version 1.x.x)
```

### 4. Install Node.js 18+

```bash
# Install Node.js
brew install node@18

# Verify installation
node --version
npm --version
# Should show: v18.x.x or higher
```

### 5. Install Docker Desktop

1. **Download**: https://www.docker.com/products/docker-desktop
2. **Install**: Drag to Applications folder
3. **Start**: Open Docker Desktop app
4. **Verify**:
   ```bash
   docker --version
   docker-compose --version
   ```

---

## Project Setup

### 6. Clone the Repository

```bash
# Clone the repo (replace with actual URL)
git clone https://github.com/your-org/churn-risk-app.git
cd churn-risk-app

# Verify you're in the right place
ls -la
# Should see: backend/, frontend/, docs/, docker-compose.yml, etc.
```

### 7. Start Docker Services

PostgreSQL and Redis run in Docker containers for local development.

```bash
# Start Docker Desktop first (if not running)

# Start services
docker-compose up -d

# Verify they're running
docker-compose ps
# Should show postgres and redis containers with "Up" status
```

**What this creates**:
- PostgreSQL 15 on `localhost:5432`
  - Database: `churn_risk_dev`
  - Username: `postgres`
  - Password: `password`
- Redis 7 on `localhost:6379`

---

## Backend Setup

### 8. Install Backend Dependencies

```bash
cd backend

# Install Python dependencies
poetry install

# This creates a virtual environment and installs all packages
# Takes 2-5 minutes
```

### 9. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

**Required variables** (get these from team lead or project owner):

```bash
# Database (local Docker - should work as-is)
DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev

# Firebase Auth (get from project owner)
FIREBASE_PROJECT_ID=churn-risk
FIREBASE_CREDENTIALS_PATH=../firebase-credentials.json

# OpenRouter AI (get API key from https://openrouter.ai/)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=google/gemini-2.5-flash

# HubSpot OAuth (get from project owner)
HUBSPOT_CLIENT_ID=your-client-id
HUBSPOT_CLIENT_SECRET=your-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/hubspot/callback

# App Settings
SECRET_KEY=generate-a-random-secret-key
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
API_V1_PREFIX=/api/v1
```

**Generate SECRET_KEY**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Get Firebase credentials**:
1. Ask project owner for `firebase-credentials.json`
2. Place it in project root: `churn-risk-app/firebase-credentials.json`
3. Path in `.env` should be: `../firebase-credentials.json` (relative to backend dir)

### 10. Run Database Migrations

```bash
# Make sure you're in backend/ directory
cd backend

# Run migrations to create all tables
poetry run alembic upgrade head

# Should see output ending with:
# INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, description
```

### 11. Verify Backend Setup

```bash
# Start the backend server
poetry run uvicorn src.main:app --reload --port 8000
```

**You should see**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Test it**:
- Open browser to: http://localhost:8000/health
- Should see: `{"status":"healthy","environment":"development"}`
- Visit: http://localhost:8000/api/v1/docs
- Should see interactive API documentation

**Stop the server**: Press `Ctrl+C`

---

## Frontend Setup

### 12. Install Frontend Dependencies

```bash
# From project root
cd frontend

# Install npm packages
npm install

# Takes 2-5 minutes
```

### 13. Configure Frontend Environment

The frontend uses environment variables for API and Firebase configuration.

**For local development**, defaults should work. Optionally create `.env`:

```bash
# Optional: Create .env for local overrides
cat > .env << 'EOF'
NUXT_PUBLIC_API_BASE=http://localhost:8000
NUXT_PUBLIC_FIREBASE_API_KEY=AIzaSyAsAfrqGZdfEFpMfA7xPPWGck4l9x3PsCM
NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN=churn-risk.firebaseapp.com
NUXT_PUBLIC_FIREBASE_PROJECT_ID=churn-risk
EOF
```

**Note**: Firebase config values should match what's in the backend Firebase credentials.

### 14. Verify Frontend Setup

```bash
# Start the frontend dev server
npm run dev
```

**You should see**:
```
Nuxt 3.x.x with Nitro x.x.x
  > Local:    http://localhost:3000/
```

**Test it**:
- Open browser to: http://localhost:3000
- Should see the landing page
- Check browser console for errors (should be none)

**Stop the server**: Press `Ctrl+C`

---

## Verify Everything Works

### 15. Run Backend Tests

```bash
cd backend

# Run all tests
poetry run pytest

# Should see:
# ====== 57 passed in X.XXs ======
```

If tests fail, check:
- Docker containers are running (`docker-compose ps`)
- `.env` file is configured correctly
- Migrations ran successfully

### 16. Test Full Stack

**Terminal 1**: Start Docker
```bash
docker-compose up -d
```

**Terminal 2**: Start Backend
```bash
cd backend
poetry run uvicorn src.main:app --reload --port 8000
```

**Terminal 3**: Start Frontend
```bash
cd frontend
npm run dev
```

**Browser Tests**:

1. **Visit frontend**: http://localhost:3000
   - Should load landing page

2. **Test registration**: http://localhost:3000/register
   - Email: `test@example.com`
   - Password: `password123`
   - Company: `Test Company`
   - Subdomain: `testco`
   - Should create account and redirect to login

3. **Test login**: http://localhost:3000/login
   - Use credentials from step 2
   - Should reach dashboard at `/dashboard`

4. **Check API docs**: http://localhost:8000/api/v1/docs
   - Should see Swagger UI with all endpoints

**If everything works**: ✅ You're set up!

---

## Development Workflow

Now that you're set up, here's the daily workflow:

**See**: [Daily Development Guide](./daily-development-guide.md) for day-to-day development tasks.

**Quick reminder**:
```bash
# Start services
docker-compose up -d
cd backend && poetry run uvicorn src.main:app --reload --port 8000
cd frontend && npm run dev
```

---

## Helpful Tools (Optional)

### Database GUI

**Recommended**: Postico (macOS) or pgAdmin

**Connection details**:
- Host: `localhost`
- Port: `5432`
- Database: `churn_risk_dev`
- User: `postgres`
- Password: `password`

### VS Code Extensions

Recommended extensions for VS Code:

**Python**:
- Python (Microsoft)
- Pylance (Microsoft)
- Ruff (Astral Software)

**Frontend**:
- Vue Language Features (Volar)
- TypeScript Vue Plugin (Volar)
- Tailwind CSS IntelliSense
- ESLint

**General**:
- GitLens
- Docker
- PostgreSQL (Chris Kolkman)

### Command Line Tools

```bash
# Install HubSpot CLI (for HubSpot development)
npm install -g @hubspot/cli@latest

# Verify
hs --version
```

---

## Understanding the Codebase

### Backend Structure
```
backend/
├── src/
│   ├── api/              # API routes and endpoints
│   │   ├── dependencies.py   # FastAPI dependencies (auth)
│   │   └── routers/          # Route handlers
│   ├── core/             # Core functionality
│   │   ├── config.py         # Settings from environment
│   │   ├── database.py       # Database connection
│   │   └── auth.py           # Firebase auth
│   ├── models/           # Database models (SQLAlchemy)
│   ├── schemas/          # API request/response schemas (Pydantic)
│   ├── services/         # Business logic
│   │   └── openrouter.py     # AI analysis service
│   └── integrations/     # External API clients
│       └── hubspot.py        # HubSpot API client
├── tests/               # Test files
│   ├── unit/                # Fast tests with mocks
│   └── integration/         # Tests with real DB
├── alembic/            # Database migrations
└── scripts/            # Utility scripts
```

**See**: [backend/CLAUDE.md](../../backend/CLAUDE.md) for backend patterns and conventions.

### Frontend Structure
```
frontend/
├── pages/              # File-based routing
│   ├── index.vue          # Landing page (/)
│   ├── login.vue          # Login page (/login)
│   ├── register.vue       # Registration (/register)
│   └── dashboard.vue      # Dashboard (/dashboard)
├── components/         # Reusable Vue components
├── composables/        # Composition API functions
│   └── useAuth.ts        # Firebase auth composable
├── stores/            # Pinia state management
│   ├── user.ts           # User state
│   └── tickets.ts        # Tickets state
├── types/             # TypeScript type definitions
└── layouts/           # Layout components
```

**See**: [frontend/CLAUDE.md](../../frontend/CLAUDE.md) for frontend patterns and conventions.

---

## Key Patterns to Know

### Backend: Multi-Tenancy

**Every query must filter by tenant_id**:

```python
# ✅ CORRECT
tickets = db.query(Ticket).filter(
    Ticket.tenant_id == current_user.tenant_id
).all()

# ❌ WRONG - Data leak!
tickets = db.query(Ticket).all()
```

### Backend: Authentication

All protected endpoints use FastAPI dependencies:

```python
from src.api.dependencies import get_current_user

@router.get("/tickets")
async def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # current_user is automatically authenticated
    # db session is automatically provided
```

### Frontend: API Calls

**Always use this pattern** for authenticated API calls:

```typescript
const { idToken } = useAuth()
const config = useRuntimeConfig()

const data = await $fetch(`${config.public.apiBase}/api/v1/endpoint`, {
  headers: {
    Authorization: `Bearer ${idToken.value}`
  }
})
```

**See**: [frontend/CLAUDE.md](../../frontend/CLAUDE.md#authentication-pattern) for complete pattern.

---

## Common First-Time Issues

### "poetry: command not found"

**Fix**: Add Poetry to PATH
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### "Python version not available"

**Fix**: Install Python 3.11 via Homebrew
```bash
brew install python@3.11
```

### "Cannot connect to Docker daemon"

**Fix**: Start Docker Desktop app
- Open Docker Desktop from Applications
- Wait for whale icon in menu bar to show "Docker Desktop is running"

### "Port 5432 already in use"

**Fix**: Another Postgres instance is running
```bash
# Check what's using the port
lsof -i :5432

# Stop system Postgres if running
brew services stop postgresql
```

### Firebase credentials error

**Fix**: Check file path
```bash
# From backend directory:
ls -la ../firebase-credentials.json

# Should show the file exists
# If not, ask project owner for the file
```

---

## Getting Help

### Documentation
- **Architecture**: [Architecture Overview](./architecture-overview.md)
- **Daily Development**: [Daily Development Guide](./daily-development-guide.md)
- **Testing**: [Testing Guide](./testing-guide.md)
- **Backend**: [backend/CLAUDE.md](../../backend/CLAUDE.md)
- **Frontend**: [frontend/CLAUDE.md](../../frontend/CLAUDE.md)
- **GCP Operations**: [GCP Daily Operations](../operations/gcp-daily-operations.md)

### External Resources
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Nuxt 3**: https://nuxt.com/
- **Vue 3**: https://vuejs.org/
- **Pydantic**: https://docs.pydantic.dev/
- **Firebase**: https://firebase.google.com/docs

### Team
- Ask in team chat/Slack
- Check existing GitHub issues
- Review closed PRs for examples

---

## Next Steps

After setup, you're ready to:

1. **Explore the codebase**: Read through the main files in `backend/src/` and `frontend/pages/`
2. **Run tests**: Make sure all 57 tests pass
3. **Make a small change**: Try adding a new field or endpoint
4. **Read architecture docs**: Understand the multi-tenant model and auth flow
5. **Pick up a task**: Check project board or backlog for starter issues

**For daily development**: See [Daily Development Guide](./daily-development-guide.md)

---

**Welcome to the team! 🚀**

**Last Updated**: 2025-11-14

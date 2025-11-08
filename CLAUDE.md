# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-tenant SaaS application that analyzes HubSpot support tickets using AI to detect churn risk, perform sentiment analysis, and classify topics. Uses webhook-based real-time ingestion.

**Stack**: FastAPI backend on GCP Cloud Run, Vue 3/Nuxt frontend, PostgreSQL, Firebase Auth, OpenRouter for LLM analysis.

## Development Setup

### Prerequisites

Start local services first:
```bash
docker-compose up -d  # Starts PostgreSQL and Redis
```

**Docker Services**:
- PostgreSQL 15 on `localhost:5432`
  - Database: `churn_risk_dev`
  - Username: `postgres`
  - Password: `password`
- Redis 7 on `localhost:6379`

Use this connection string in `.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev
```

### Backend

```bash
cd backend
poetry install
cp .env.example .env  # Edit with credentials
poetry run alembic upgrade head  # Run migrations
poetry run uvicorn src.main:app --reload --port 8000
```

**Environment Variables**: See `backend/.env.example` for required config. Key vars:
- `DATABASE_URL`: PostgreSQL connection string (Docker: `postgresql://postgres:password@localhost:5432/churn_risk_dev`)
- `FIREBASE_PROJECT_ID` and `FIREBASE_CREDENTIALS_PATH`: Firebase Auth
- `OPENROUTER_API_KEY`: AI service (sign up at https://openrouter.ai/)
- `HUBSPOT_CLIENT_ID`, `HUBSPOT_CLIENT_SECRET`, `HUBSPOT_REDIRECT_URI`: OAuth flow (see `docs/dev/hubspot-oauth-setup.md`)
  - Note: Developer API keys are deprecated - OAuth only
- `SECRET_KEY`: Generate with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### Frontend

```bash
cd frontend
npm install
npm run dev  # Runs on localhost:3000
```

### Access Points

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs
- Frontend: http://localhost:3000

## Common Commands

### Backend

**Tests**:
```bash
cd backend
poetry run pytest                    # All tests
poetry run pytest tests/unit/        # Unit tests only
poetry run pytest tests/integration/ # Integration tests only
poetry run pytest tests/unit/test_auth.py::test_name  # Single test
PYTHONPATH=/Users/davidhague/source/churn-risk-app/backend poetry run pytest  # If path issues
```

**Linting & Formatting**:
```bash
poetry run ruff check src     # Lint
poetry run black src          # Format
poetry run mypy src           # Type check
```

**Database Migrations**:
```bash
poetry run alembic revision --autogenerate -m "description"  # Create migration
poetry run alembic upgrade head     # Apply migrations
poetry run alembic downgrade -1     # Rollback one migration
poetry run alembic history          # View migration history
PYTHONPATH=/Users/davidhague/source/churn-risk-app/backend poetry run alembic upgrade head  # If path issues
```

### Frontend

```bash
npm run dev         # Development server
npm run build       # Production build
npm run typecheck   # TypeScript validation
npm run lint        # ESLint
```

## Architecture

### Multi-Tenancy Model

**Tenant Isolation**: All data is scoped by `tenant_id`. The `Tenant` model is the root entity with cascade deletes to all related data (users, tickets, companies, churn risks, topics, integrations).

**User Authentication Flow**:
1. Firebase Auth handles authentication
2. `verify_firebase_token` dependency validates JWT
3. `get_current_user` dependency fetches User record from DB using `firebase_uid`
4. All protected routes require `current_user: User = Depends(get_current_user)`

**Role-Based Access Control**: Users have roles (`ADMIN`, `MEMBER`, `VIEWER`) enforced via `require_admin` dependency.

### Database Architecture

**Base Models** (`src/models/base.py`):
- `UUIDMixin`: All models use UUID primary keys (`id`)
- `TimestampMixin`: Auto-managed `created_at` and `updated_at` fields

**Core Models**:
- `Tenant`: Root entity for multi-tenancy
- `User`: Linked to Firebase Auth via `firebase_uid`
- `Integration`: OAuth credentials for HubSpot (encrypted tokens)
- `Company`: Customer companies from HubSpot
- `Contact`: People at customer companies
- `Ticket`: Support tickets from HubSpot
- `TicketTopic`: Configured topics for classification
- `ChurnRiskCard`: Generated churn risk alerts with sentiment scores

**Relationships**: All foreign keys use `ondelete="CASCADE"` to ensure data integrity. Tenant deletion removes all associated data.

### AI Service Layer

**Abstraction Pattern** (`src/services/ai_base.py`):
- `SentimentAnalyzer`: Abstract base for sentiment analysis
- `TopicClassifier`: Abstract base for topic classification
- `TicketAnalyzer`: Combined analysis interface

**Implementation** (`src/services/openrouter.py`):
- Implements all three ABC interfaces
- Uses tenacity for retry logic with exponential backoff
- Handles rate limits and transient failures
- Structured output via Pydantic schemas

**Usage**: Always code against the ABC interfaces, not concrete implementations. This allows swapping AI providers without changing business logic.

### API Structure

**Routing**: All API routes prefixed with `/api/v1` (configured in `settings.API_V1_PREFIX`)

**Authentication**: Most routes require Firebase JWT. Use `current_user: User = Depends(get_current_user)` parameter.

**Database Sessions**: Use `db: Session = Depends(get_db)` for database access. Sessions auto-close via dependency.

**Error Handling**: Raise `HTTPException` with appropriate status codes. Frontend expects standardized error responses.

### HubSpot Integration

**OAuth Flow** (`src/integrations/hubspot.py`):
1. User initiates OAuth in frontend
2. Redirect to HubSpot authorization
3. Callback endpoint exchanges code for tokens
4. Tokens stored in `Integration` model (encrypted in production)

**Setup Guide**: See `docs/dev/hubspot-oauth-setup.md` for complete OAuth app creation with HubSpot CLI.

**HubSpot App**: Located in `hs-churn-risk/` directory with OAuth configuration in `public-app.json`.

**Required Scopes**:
- `crm.objects.contacts.read` - Contact information
- `crm.objects.companies.read` - Company data
- `tickets` - Support ticket access

**Webhook Ingestion**:
- HubSpot webhooks trigger real-time ticket ingestion
- Tickets analyzed via AI service layer
- Churn risk cards auto-created for negative sentiment

**Authentication**:
- **OAuth only**: `HUBSPOT_CLIENT_ID` + `HUBSPOT_CLIENT_SECRET`
- Developer API keys removed (deprecated by HubSpot)

## Testing Conventions

**Test Organization**:
- `tests/unit/`: Fast tests with mocked dependencies
- `tests/integration/`: Tests with real database/external services

**Pytest Configuration**: Located in `pytest.ini`. Uses `asyncio_mode = auto` for async tests.

**Running Tests**:
- Always run from `backend/` directory
- Use `PYTHONPATH` prefix if import errors occur
- Tests use async fixtures and `pytest-asyncio`

**Key Test Files**:
- `test_auth.py`: Firebase token validation
- `test_dependencies.py`: FastAPI dependencies
- `test_models.py`: SQLAlchemy models
- `test_openrouter.py`: AI service with mocked HTTP

## Configuration Management

**Settings Class** (`src/core/config.py`):
- Uses `pydantic-settings` for type-safe config
- Loads from `.env` file via `SettingsConfigDict`
- Access via `from src.core.config import settings`

**Required vs Optional**:
- Database, Firebase, OpenRouter: Always required
- HubSpot: Either API key OR OAuth credentials
- GCP: Optional for local dev, required for production

**CORS**: Configured via `CORS_ORIGINS` (comma-separated list). Parsed by `settings.get_cors_origins_list()`.

## Key Patterns

**Dependency Injection**: FastAPI dependencies for auth, DB sessions, and user context. Chain dependencies (e.g., `require_admin` depends on `get_current_user`).

**Database Queries**: Always filter by `tenant_id` to enforce multi-tenancy isolation.

**Async/Await**: All route handlers and service methods are async. Use `await` for DB queries with async engine (if migrated) or external API calls.

**Error Context**: Include tenant/user context in error logs for multi-tenant debugging.

## Deployment Notes

**GCP Cloud Run**: Backend deployed as containerized FastAPI app. Environment variables injected via Cloud Run config.

**Database**: Cloud SQL PostgreSQL with connection pooling (`pool_size=10`, `max_overflow=20`).

**Migrations**: Run `alembic upgrade head` before deploying new backend versions.

**Firebase**: Production uses Firebase credentials from GCP Secret Manager (path in `FIREBASE_CREDENTIALS_PATH`).

## Current Development Status

**Completed (as of 2025-11-08)**:
- ✅ Multi-tenant data model with RBAC (11 tables, UUID-based)
- ✅ Firebase authentication integration with token verification
- ✅ HubSpot OAuth app creation and configuration (via HubSpot CLI)
- ✅ HubSpot client with OAuth token support
- ✅ OpenRouter AI service with retry logic and error handling
- ✅ Database schema with Alembic migrations (initial_schema: c08085465bad)
- ✅ Sentiment analysis working (tested with real tickets)
- ✅ Topic classification working (tested with real tickets)
- ✅ Backend smoke test script (`scripts/smoke_test.py`)
- ✅ Database, OpenRouter, HubSpot integration verified
- ✅ 23/23 tests passing (unit + integration)
- ✅ Backend API server running on port 8000

**Next Steps** (from implementation plan):
- Task 6: Ticket Import & Analysis Service
- Task 7: Churn Risk Card Creation Logic
- Task 8: WebSocket Real-Time Updates
- Tasks 9-13: Frontend implementation
- Task 14: HubSpot Webhook Handling
- Tasks 15-16: GCP Deployment & Testing

**Testing**:
- Smoke test script: `backend/scripts/smoke_test.py` (run with: `poetry run python scripts/smoke_test.py`)
- Frontend test page: http://localhost:3000 (when running)
- Full testing guide: `docs/dev/testing-guide.md`
- Run all tests: `cd backend && poetry run pytest`

**Known Issues**:
- HubSpot OAuth requires user authorization flow (can't test automatically)
- OAuth callback requires Firebase JWT authentication
- Frontend is basic test page only (no real UI yet)

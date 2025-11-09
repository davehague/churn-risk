# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**📚 Specialized Guides:**
- **Backend Development**: See `backend/CLAUDE.md` for backend-specific patterns, testing, and service layer details
- **Frontend Development**: See `frontend/CLAUDE.md` for frontend patterns, auth, API calls, and component structure
- **Additional Documentation**: See `docs/dev/` for architecture, testing guides, and HubSpot OAuth setup

---

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

## Quick Reference

**Common Commands**: See `backend/CLAUDE.md` and `frontend/CLAUDE.md` for detailed command lists.

**Quick Commands**:
```bash
# Start services
docker-compose up -d                              # PostgreSQL & Redis

# Backend
cd backend && poetry run uvicorn src.main:app --reload --port 8000
cd backend && poetry run pytest                   # Run tests
cd backend && poetry run alembic upgrade head     # Run migrations

# Frontend
cd frontend && npm run dev                        # Dev server (port 3000)
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

### Service Layer Architecture

**AI Service** (`backend/src/services/`):
- Abstract base classes define interfaces (`SentimentAnalyzer`, `TopicClassifier`, `TicketAnalyzer`)
- OpenRouter implementation with retry logic and structured output
- **Pattern**: Always code against ABCs, not concrete implementations (enables provider swapping)

**See `backend/CLAUDE.md`** for detailed service layer patterns, dependency injection, and API endpoint structure.

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

## Key Patterns & Conventions

**Multi-Tenancy**: ALL database queries must filter by `tenant_id` to enforce tenant isolation. Return 404 (not 403) for cross-tenant access attempts.

**Testing**: See `backend/CLAUDE.md` for detailed testing patterns. Tests organized in `backend/tests/unit/` (mocked) and `backend/tests/integration/` (real DB).

**Configuration**: Environment-based config via `pydantic-settings`. See `backend/.env.example` for all required variables.

**Authentication**: Firebase JWT tokens validated via `verify_firebase_token` → `get_current_user` dependency chain.

**See specialized guides** (`backend/CLAUDE.md`, `frontend/CLAUDE.md`) for detailed patterns and best practices.

## Deployment Notes

**GCP Cloud Run**: Backend deployed as containerized FastAPI app. Environment variables injected via Cloud Run config.

**Database**: Cloud SQL PostgreSQL with connection pooling (`pool_size=10`, `max_overflow=20`).

**Migrations**: Run `alembic upgrade head` before deploying new backend versions.

**Firebase**: Production uses Firebase credentials from GCP Secret Manager (path in `FIREBASE_CREDENTIALS_PATH`).

## Current Development Status

**Completed (as of 2025-11-09)**:
- ✅ Multi-tenant data model with RBAC (11 tables, UUID-based)
- ✅ Firebase authentication - FULLY IMPLEMENTED & TESTED
  - Backend registration API with subdomain validation
  - Frontend registration page with real-time validation
  - Login/logout with Firebase Client SDK
  - Auth middleware and route protection
  - User state management with Pinia
  - Landing page and dashboard
  - End-to-end auth flow verified
- ✅ HubSpot OAuth app creation and configuration (via HubSpot CLI)
- ✅ HubSpot client with OAuth token support
- ✅ HubSpot OAuth flow COMPLETED (FlxPoint account connected)
- ✅ Fetching real tickets from HubSpot working
- ✅ OpenRouter AI service with retry logic and error handling
- ✅ AI model externalized to OPENROUTER_MODEL environment variable
- ✅ Database schema with Alembic migrations (initial_schema: c08085465bad)
- ✅ Sentiment analysis working (tested with real tickets)
- ✅ Topic classification working (tested with real tickets)
- ✅ Backend smoke test script (`scripts/smoke_test.py`)
- ✅ Database, OpenRouter, HubSpot integration verified
- ✅ 33/33 tests passing (10 auth tests + 23 other tests)
- ✅ Backend API server running on port 8000
- ✅ Frontend running on port 3000 with complete auth UI

**🚀 Next Steps** (as of 2025-11-09):

**IMMEDIATE**: GCP Cloud Deployment
- Set up Cloud Run for backend
- Set up Cloud SQL for PostgreSQL
- Configure production environment variables
- Deploy and verify all integrations work in cloud

**Then Continue with Features**:
- Ticket Import & Analysis Service (bulk import with AI)
- Churn Risk Card Creation Logic
- Frontend Dashboard with Analytics
- Churn Risk Kanban Board
- WebSocket Real-Time Updates
- HubSpot Webhook Handling

**Testing & Verification**:
- Smoke test: `cd backend && poetry run python scripts/smoke_test.py`
- All tests: `cd backend && poetry run pytest` (33/33 passing)
- Full testing guide: `docs/dev/testing-guide.md`

# Churn Risk App

A multi-tenant SaaS application that analyzes HubSpot support tickets for sentiment, creates churn risk cards for frustrated customers, and provides topic-based analytics.

## Architecture

- **Backend**: FastAPI on GCP Cloud Run
- **Frontend**: Vue 3/Nuxt
- **Database**: Cloud SQL PostgreSQL
- **Authentication**: Firebase Auth
- **AI**: OpenRouter for LLM analysis
- **Integration**: Webhook-based real-time ingestion from HubSpot

## Tech Stack

- Python 3.11, FastAPI, SQLAlchemy, Alembic, Pydantic
- Vue 3, Nuxt 3, Tailwind CSS
- PostgreSQL 15, Firebase Auth, OpenRouter API
- GCP Cloud Run, Cloud SQL, Cloud Tasks

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Poetry (for Python dependency management)
- HubSpot CLI: `npm install -g @hubspot/cli@latest`

### Quick Start

1. **Clone the repository**

```bash
git clone <repository-url>
cd churn-risk-app
```

2. **Start local services (PostgreSQL and Redis)**

```bash
docker-compose up -d
```

3. **Setup backend**

```bash
cd backend
poetry install
cp .env.example .env
# Edit .env with your credentials (see Configuration below)
poetry run alembic upgrade head  # Run database migrations
poetry run uvicorn src.main:app --reload --port 8000
```

4. **Setup frontend**

```bash
cd frontend
npm install
npm run dev
```

### Configuration

**Required Environment Variables** (in `backend/.env`):

```bash
# Database (Docker)
DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev

# Firebase Auth
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# OpenRouter AI
OPENROUTER_API_KEY=sk-or-your-key

# HubSpot OAuth
HUBSPOT_CLIENT_ID=your-client-id
HUBSPOT_CLIENT_SECRET=your-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/hubspot/callback

# App Settings
SECRET_KEY=generate-a-random-secret-key
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**See detailed setup guides:**
- [HubSpot OAuth Setup](docs/dev/hubspot-oauth-setup.md)
- [Full Development Guide](CLAUDE.md)

### Access

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs
- Frontend: http://localhost:3000

## Development

### Backend

- Run tests: `cd backend && poetry run pytest`
- Run linting: `poetry run ruff check src`
- Format code: `poetry run black src`

### Frontend

- Run dev server: `npm run dev`
- Build for production: `npm run build`
- Type check: `npm run typecheck`

## Project Structure

```
churn-risk-app/
├── backend/                      # FastAPI backend
│   ├── src/
│   │   ├── api/                  # API routes and routers
│   │   ├── models/               # SQLAlchemy database models
│   │   ├── schemas/              # Pydantic schemas for validation
│   │   ├── services/             # Business logic (AI, email, etc.)
│   │   ├── integrations/         # External API clients (HubSpot)
│   │   └── core/                 # Core utilities (config, auth, database)
│   ├── tests/
│   │   ├── unit/                 # Fast tests with mocked dependencies
│   │   └── integration/          # Tests with real DB/services
│   ├── scripts/
│   │   └── smoke_test.py         # Smoke test script
│   ├── alembic/                  # Database migrations
│   └── pyproject.toml            # Poetry dependencies
├── frontend/                     # Nuxt 3 frontend (WIP)
│   ├── components/
│   ├── composables/
│   ├── layouts/
│   ├── pages/
│   ├── stores/
│   └── types/
├── hs-churn-risk/                # HubSpot OAuth app configuration
│   └── public-app.json           # OAuth scopes and redirect URIs
├── docs/
│   ├── dev/                      # Development guides
│   ├── plans/                    # Architecture and implementation plans
├── docker-compose.yml            # Local PostgreSQL and Redis
├── CLAUDE.md                     # Comprehensive dev guide for Claude Code
└── README.md                     # This file
```

## License

Proprietary

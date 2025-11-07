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

### Setup

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
# Edit .env with your credentials
poetry run uvicorn src.main:app --reload --port 8000
```

4. **Setup frontend**

```bash
cd frontend
npm install
npm run dev
```

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
├── backend/
│   ├── src/
│   │   ├── api/          # API routes
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   ├── integrations/ # External API integrations
│   │   └── core/         # Core utilities (config, auth, db)
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── alembic/          # Database migrations
├── frontend/
│   ├── components/
│   ├── composables/
│   ├── layouts/
│   ├── pages/
│   ├── stores/
│   └── types/
└── docs/                 # Documentation
```

## License

Proprietary

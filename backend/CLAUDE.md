# Backend Development Guide

This file provides guidance to Claude Code when working with the backend codebase.

## Project Overview

FastAPI backend for Churn Risk App - a multi-tenant SaaS platform that analyzes HubSpot support tickets using AI to detect churn risk.

**Tech Stack**: Python 3.11, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Firebase Admin SDK, OpenRouter for LLM analysis

## Development Setup

### Prerequisites

Start local services first:
```bash
# From project root
docker-compose up -d  # Starts PostgreSQL and Redis
```

### Running the Server

```bash
# From backend/ directory
poetry run uvicorn src.main:app --reload --port 8000
```

Access points:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/api/v1/docs
- Health check: http://localhost:8000/health

## Common Commands

All commands below should be run from the `backend/` directory.

### Testing

```bash
poetry run pytest                    # All tests
poetry run pytest tests/unit/        # Unit tests only
poetry run pytest tests/integration/ # Integration tests only
poetry run pytest tests/unit/test_auth.py::test_name  # Single test
poetry run pytest -v                 # Verbose output
poetry run pytest --cov=src          # With coverage

# If import errors occur
PYTHONPATH=/Users/davidhague/source/churn-risk-app/backend poetry run pytest
```

### Database Migrations

```bash
poetry run alembic revision --autogenerate -m "description"  # Create migration
poetry run alembic upgrade head     # Apply migrations
poetry run alembic downgrade -1     # Rollback one migration
poetry run alembic history          # View migration history
poetry run alembic current          # Show current version

# If import errors occur
PYTHONPATH=/Users/davidhague/source/churn-risk-app/backend poetry run alembic upgrade head
```

### Code Quality

```bash
poetry run ruff check src     # Lint
poetry run ruff check --fix src  # Auto-fix issues
poetry run black src          # Format
poetry run mypy src           # Type check
```

## Architecture Patterns

### Multi-Tenancy

**CRITICAL**: All data queries MUST filter by `tenant_id` to enforce tenant isolation.

```python
# ✅ CORRECT - Always filter by tenant_id
tickets = db.query(Ticket).filter(
    Ticket.tenant_id == current_user.tenant_id
).all()

# ❌ WRONG - Missing tenant_id filter (data leak!)
tickets = db.query(Ticket).all()
```

**Access Control Pattern:**
- Return 404 (not 403) for cross-tenant access attempts
- This prevents leaking information about data existence

### Dependency Injection

FastAPI dependencies chain together for auth and database access:

```python
from fastapi import Depends
from src.core.database import get_db
from src.api.dependencies import get_current_user, require_admin

@app.get("/api/v1/tickets")
async def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # current_user is already authenticated and loaded from DB
    # db session will auto-close after request
    tickets = db.query(Ticket).filter(
        Ticket.tenant_id == current_user.tenant_id
    ).all()
    return tickets
```

**Dependency Chain:**
1. `get_db` → Provides database session
2. `verify_firebase_token` → Validates JWT from Authorization header
3. `get_current_user` → Fetches User from DB using Firebase UID
4. `require_admin` → Checks user role is ADMIN

### Service Layer Pattern

**Always code against ABC interfaces, not concrete implementations.**

```python
# ✅ CORRECT - Use abstract base class
from src.services.ai_base import TicketAnalyzer

def analyze_ticket(analyzer: TicketAnalyzer):
    result = await analyzer.analyze_ticket(content)

# ❌ WRONG - Direct dependency on implementation
from src.services.openrouter import OpenRouterAnalyzer

def analyze_ticket(analyzer: OpenRouterAnalyzer):
    result = await analyzer.analyze_ticket(content)
```

**Why:** This allows swapping AI providers (OpenRouter → Anthropic, OpenAI, etc.) without changing business logic.

### Database Query Patterns

**Prevent N+1 Queries with Eager Loading:**

```python
from sqlalchemy.orm import joinedload

# ✅ CORRECT - Eager load relationships
tickets = db.query(Ticket).options(
    joinedload(Ticket.company),
    joinedload(Ticket.contact)
).filter(Ticket.tenant_id == tenant_id).all()

# ❌ WRONG - Will cause N+1 queries
tickets = db.query(Ticket).filter(Ticket.tenant_id == tenant_id).all()
for ticket in tickets:
    print(ticket.company.name)  # Separate query for EACH ticket!
```

**Multi-Tenant Composite Indexes:**

For queries filtering by `tenant_id` + another field, use composite indexes:

```python
__table_args__ = (
    Index("ix_tickets_tenant_sentiment", "tenant_id", "sentiment_score", "created_at"),
)
```

### API Endpoint Patterns

**Standard endpoint structure:**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.api.dependencies import get_current_user
from src.models.user import User
from src.schemas.ticket import TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tickets for current tenant."""
    tickets = db.query(Ticket).filter(
        Ticket.tenant_id == current_user.tenant_id
    ).all()

    return tickets

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single ticket by ID."""
    from uuid import UUID

    ticket = db.query(Ticket).filter(
        Ticket.id == UUID(ticket_id),
        Ticket.tenant_id == current_user.tenant_id  # Enforce tenant isolation
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket
```

**Error Handling:**
- Use `HTTPException` with appropriate status codes
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (or cross-tenant access attempt)
- 400: Bad Request (validation errors)
- 500: Internal Server Error (unhandled exceptions)

## Testing Conventions

### Test Organization

```
tests/
├── unit/           # Fast tests with mocked dependencies
│   ├── test_auth.py
│   ├── test_models.py
│   ├── test_openrouter.py
│   └── test_schemas.py
└── integration/    # Tests with real DB/external services
    ├── test_hubspot.py
    └── test_auth_registration.py
```

### Unit Test Pattern (Mocked Dependencies)

```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_analyze_ticket():
    """Test ticket analysis with mocked OpenRouter API."""
    from src.services.openrouter import OpenRouterAnalyzer

    mock_response = {
        "choices": [{
            "message": {
                "content": '{"sentiment": {"score": "negative", "confidence": 0.85}}'
            }
        }]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        analyzer = OpenRouterAnalyzer(api_key="test-key")
        result = await analyzer.analyze_ticket("This product sucks!")

        assert result.sentiment.sentiment == SentimentScore.NEGATIVE
        assert result.sentiment.confidence == 0.85
```

### Integration Test Pattern (Real Database)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.database import Base
from src.models.tenant import Tenant

@pytest.fixture
def db_session():
    """Create test database session."""
    # Use in-memory SQLite for fast tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_tenant(db_session):
    """Test creating a tenant."""
    tenant = Tenant(name="TestCo", subdomain="testco")
    db_session.add(tenant)
    db_session.commit()

    assert tenant.id is not None
    assert tenant.subdomain == "testco"
```

### Firebase Auth Mocking Pattern

```python
from unittest.mock import patch
from fastapi.security import HTTPAuthorizationCredentials

@pytest.mark.asyncio
async def test_verify_token():
    """Test Firebase token verification."""
    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "test-uid",
            "email": "test@example.com"
        }

        result = await verify_firebase_token(mock_credentials)

        assert result["uid"] == "test-uid"
```

### Key Testing Principles

1. **Unit tests should be fast** - Mock external dependencies (Firebase, OpenRouter, HubSpot)
2. **Integration tests can be slow** - Use real database (in-memory SQLite is fine)
3. **Use `pytest.mark.asyncio`** for async test functions
4. **Use fixtures** for shared setup (database sessions, test data)
5. **Test both success and failure cases** - Invalid tokens, missing data, etc.

## Service Layer Architecture

### AI Service (`src/services/`)

**Abstract Base Classes** (`ai_base.py`):
- `SentimentAnalyzer` - Sentiment analysis interface
- `TopicClassifier` - Topic classification interface
- `TicketAnalyzer` - Combined analysis interface

**Implementation** (`openrouter.py`):
- `OpenRouterAnalyzer` - Implements all three ABC interfaces
- Uses `tenacity` for retry logic with exponential backoff
- Structured output via Pydantic schemas

**Usage:**
```python
from src.services.openrouter import OpenRouterAnalyzer

analyzer = OpenRouterAnalyzer()
result = await analyzer.analyze_ticket(
    ticket_content="Customer is frustrated with API errors",
    available_topics=["API Issues", "Billing", "Performance"],
    training_rules=["API errors should be classified as API Issues"]
)

print(f"Sentiment: {result.sentiment.sentiment.value}")
print(f"Confidence: {result.sentiment.confidence:.2%}")
for topic in result.topics:
    print(f"Topic: {topic.topic_name} ({topic.confidence:.2%})")
```

### HubSpot Integration (`src/integrations/hubspot.py`)

**OAuth Methods:**
- `exchange_code_for_token(code, redirect_uri)` - Get access token
- `refresh_access_token(refresh_token)` - Refresh expired token

**API Methods:**
- `get_tickets(limit, after, properties)` - Fetch tickets (paginated)
- `get_ticket(ticket_id)` - Fetch single ticket
- `get_companies(limit)` - Fetch companies
- `get_contacts(limit)` - Fetch contacts
- `create_webhook_subscription(webhook_url, subscription_type)` - Setup webhooks

**Usage:**
```python
from src.integrations.hubspot import HubSpotClient

# From stored integration credentials
integration = db.query(Integration).first()
access_token = integration.credentials["access_token"]

client = HubSpotClient(access_token=access_token)
tickets_response = await client.get_tickets(limit=20)

for ticket_data in tickets_response["results"]:
    ticket_id = ticket_data["id"]
    properties = ticket_data["properties"]
    # Process ticket...
```

## Configuration Management

**Settings Class** (`src/core/config.py`):
- Uses `pydantic-settings` for type-safe environment variables
- Loads from `.env` file automatically
- Access via `from src.core.config import settings`

**Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# OpenRouter
OPENROUTER_API_KEY=sk-or-xxx
OPENROUTER_MODEL=google/gemini-2.5-flash  # AI model selection

# HubSpot OAuth
HUBSPOT_CLIENT_ID=your-client-id
HUBSPOT_CLIENT_SECRET=your-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/hubspot/callback

# App Settings
ENVIRONMENT=development
SECRET_KEY=your-secret-key
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Accessing Settings:**
```python
from src.core.config import settings

print(settings.DATABASE_URL)
print(settings.ENVIRONMENT)
print(settings.OPENROUTER_API_KEY)
```

## Key File Locations

```
backend/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Settings (env vars)
│   │   ├── database.py         # Database engine & session
│   │   └── auth.py             # Firebase token verification
│   ├── models/                 # SQLAlchemy models
│   │   ├── base.py             # Base mixins (UUID, Timestamp)
│   │   ├── tenant.py           # Tenant model
│   │   ├── user.py             # User model
│   │   ├── integration.py      # Integration model
│   │   ├── company.py          # Company model
│   │   ├── contact.py          # Contact model
│   │   ├── ticket.py           # Ticket model
│   │   ├── topic.py            # Topic models
│   │   └── churn_risk.py       # Churn risk card models
│   ├── schemas/                # Pydantic schemas
│   │   ├── ai.py               # AI analysis schemas
│   │   ├── integration.py      # Integration schemas
│   │   └── auth.py             # Auth schemas
│   ├── services/               # Business logic
│   │   ├── ai_base.py          # AI service ABCs
│   │   └── openrouter.py       # OpenRouter implementation
│   ├── integrations/           # External API clients
│   │   └── hubspot.py          # HubSpot API client
│   └── api/
│       ├── dependencies.py     # FastAPI dependencies (auth)
│       └── routers/            # API route handlers
│           ├── integrations.py # Integration endpoints
│           └── auth.py         # Auth endpoints
├── tests/
│   ├── unit/                   # Fast mocked tests
│   └── integration/            # Real DB/service tests
├── alembic/                    # Database migrations
│   ├── env.py                  # Migration environment
│   └── versions/               # Migration files
├── scripts/                    # Utility scripts
│   └── smoke_test.py           # Quick integration test
├── pyproject.toml              # Poetry dependencies
├── pytest.ini                  # Pytest configuration
└── alembic.ini                 # Alembic configuration
```

## Database Models

**Base Mixins** (`src/models/base.py`):
- `UUIDMixin` - UUID primary key (`id`)
- `TimestampMixin` - Auto-managed `created_at` and `updated_at`

**Core Models:**
- `Tenant` - Root entity for multi-tenancy
- `User` - Users linked to Firebase Auth via `firebase_uid`
- `Integration` - OAuth credentials (HubSpot, etc.)
- `Company` - Customer companies from HubSpot
- `Contact` - People at customer companies
- `Ticket` - Support tickets with sentiment analysis
- `TicketTopic` - Configured topics for classification
- `TicketTopicAssignment` - Many-to-many ticket ↔ topic
- `ChurnRiskCard` - Generated churn risk alerts
- `ChurnRiskComment` - Activity timeline on cards

**Relationships:**
- All foreign keys use `ondelete="CASCADE"` for data integrity
- Tenant deletion cascades to all related data
- Use `relationship()` for navigation between models

## Common Patterns

### Creating a New API Endpoint

1. **Define Pydantic schema** in `src/schemas/`
2. **Create route handler** in `src/api/routers/`
3. **Register router** in `src/main.py`
4. **Write tests** in `tests/unit/` or `tests/integration/`

### Adding a New Service

1. **Define ABC** in `src/services/*_base.py`
2. **Implement service** in `src/services/`
3. **Add to dependency injection** if needed
4. **Write unit tests** with mocked external calls

### Database Schema Change

1. **Modify models** in `src/models/`
2. **Generate migration**: `poetry run alembic revision --autogenerate -m "description"`
3. **Review migration** in `alembic/versions/`
4. **Apply migration**: `poetry run alembic upgrade head`
5. **Update tests** to reflect schema changes

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
# Set PYTHONPATH before commands
PYTHONPATH=/Users/davidhague/source/churn-risk-app/backend poetry run pytest
PYTHONPATH=/Users/davidhague/source/churn-risk-app/backend poetry run alembic upgrade head
```

### Database Connection Issues

```bash
# Check docker-compose is running
docker-compose ps

# Restart if needed
docker-compose down
docker-compose up -d

# Verify connection string in .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev
```

### Firebase Auth Errors

**"The default Firebase app does not exist"**
- Check `FIREBASE_CREDENTIALS_PATH` points to correct location
- If backend is in `backend/` subdirectory, use `../firebase-credentials.json`

**"No auth provider found"**
- Enable Email/Password authentication in Firebase Console
- Go to Authentication → Sign-in method → Enable Email/Password

### Migration Conflicts

```bash
# View current migration state
poetry run alembic current

# View migration history
poetry run alembic history

# Rollback one migration
poetry run alembic downgrade -1

# Start fresh (DEV ONLY - destroys data!)
poetry run alembic downgrade base
poetry run alembic upgrade head
```

## Current Status (as of 2025-11-14)

**✅ Completed:**
- 11-table database schema with multi-tenancy
- Firebase authentication (Admin SDK)
- OpenRouter AI service (sentiment + topic analysis)
- HubSpot OAuth integration (production environment)
- **57/57 tests passing** (automated on every push)
- **Production deployment on GCP**:
  - Cloud Run: https://churn-risk-api-461448724047.us-east1.run.app
  - Cloud SQL PostgreSQL with nullable content support
  - Automated CI/CD with Cloud Build
  - Secret Manager for credentials
- Ticket import working with AI sentiment analysis

**🚀 Next Steps:**
- Churn risk card creation logic
- Background job processing (Cloud Tasks)
- Enhanced analytics and dashboard features
- HubSpot webhook handling

## References

- Main project guide: `../CLAUDE.md`
- Frontend guide: `../frontend/CLAUDE.md`
- Testing guide: `../docs/dev/testing-guide.md`
- Architecture overview: `../docs/dev/architecture-overview.md`
- HubSpot setup: `../docs/dev/hubspot-oauth-setup.md`

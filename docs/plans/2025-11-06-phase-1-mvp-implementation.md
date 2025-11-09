# Churn Risk App - Phase 1 MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a multi-tenant SaaS app that analyzes HubSpot support tickets for sentiment, creates churn risk cards for frustrated customers, and provides topic-based analytics.

**Architecture:** FastAPI backend on GCP Cloud Run, Vue 3/Nuxt frontend, Cloud SQL PostgreSQL database, Firebase Auth, OpenRouter for LLM analysis, webhook-based real-time ingestion.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Alembic, Pydantic, Vue 3, Nuxt 3, Tailwind CSS, PostgreSQL 15, Firebase Auth, OpenRouter API, GCP Cloud Run/SQL/Tasks

---

## Prerequisites

Before starting implementation, ensure you have:
- GCP account with new project created (for free credits)
- Firebase project created and linked to GCP
- OpenRouter API account and key
- HubSpot developer account for OAuth app creation
- Node.js 18+, Python 3.11+, Docker installed locally
- Git repository initialized

---

## Task 1: Project Structure & Environment Setup

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/alembic.ini`
- Create: `backend/.env.example`
- Create: `backend/src/__init__.py`
- Create: `backend/src/main.py`
- Create: `backend/tests/__init__.py`
- Create: `frontend/package.json`
- Create: `frontend/nuxt.config.ts`
- Create: `.gitignore`
- Create: `docker-compose.yml`
- Create: `README.md`

**Step 1: Create backend directory structure**

```bash
mkdir -p backend/src/{api,models,services,integrations,core}
mkdir -p backend/tests/{unit,integration}
mkdir -p backend/alembic/versions
```

**Step 2: Create backend/pyproject.toml**

```toml
[tool.poetry]
name = "churn-risk-backend"
version = "0.1.0"
description = "Churn Risk Detection API"
authors = ["David Hague"]
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
psycopg2-binary = "^2.9.9"
pydantic = {extras = ["email"], version = "^2.5.3"}
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
httpx = "^0.26.0"
firebase-admin = "^6.4.0"
python-dotenv = "^1.0.0"
tenacity = "^8.2.3"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
black = "^24.1.1"
ruff = "^0.1.14"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Step 3: Create backend/.env.example**

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# OpenRouter
OPENROUTER_API_KEY=sk-or-xxx

# HubSpot OAuth
HUBSPOT_CLIENT_ID=your-client-id
HUBSPOT_CLIENT_SECRET=your-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/api/integrations/hubspot/callback

# App Settings
ENVIRONMENT=development
SECRET_KEY=your-secret-key-change-in-production
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# GCP (for production)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
```

**Step 4: Create backend/src/core/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # Firebase
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_PATH: str

    # OpenRouter
    OPENROUTER_API_KEY: str

    # HubSpot
    HUBSPOT_CLIENT_ID: str
    HUBSPOT_CLIENT_SECRET: str
    HUBSPOT_REDIRECT_URI: str

    # App
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # GCP
    GOOGLE_CLOUD_PROJECT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
```

**Step 5: Create backend/src/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings

app = FastAPI(
    title="Churn Risk API",
    version="0.1.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get(f"{settings.API_V1_PREFIX}/")
async def root():
    """API root endpoint."""
    return {"message": "Churn Risk API", "version": "0.1.0"}
```

**Step 6: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: churn_risk_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: churn_risk_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: churn_risk_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

**Step 7: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Environment
.env
.env.local
firebase-credentials.json

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Node
node_modules/
.nuxt/
.output/
dist/

# Database
*.db
*.sqlite

# Logs
*.log
```

**Step 8: Create frontend directory structure**

```bash
mkdir -p frontend/{components,composables,layouts,middleware,pages,plugins,public,server,stores,types}
```

**Step 9: Create frontend/package.json**

```json
{
  "name": "churn-risk-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build",
    "generate": "nuxt generate",
    "preview": "nuxt preview",
    "lint": "eslint .",
    "typecheck": "nuxt typecheck"
  },
  "dependencies": {
    "@nuxtjs/tailwindcss": "^6.11.4",
    "@pinia/nuxt": "^0.5.1",
    "firebase": "^10.8.0",
    "nuxt": "^3.10.0",
    "pinia": "^2.1.7",
    "vue": "^3.4.15"
  },
  "devDependencies": {
    "@nuxt/eslint": "^0.2.0",
    "@types/node": "^20.11.16",
    "eslint": "^8.56.0",
    "typescript": "^5.3.3"
  }
}
```

**Step 10: Create frontend/nuxt.config.ts**

```typescript
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      firebaseApiKey: process.env.NUXT_PUBLIC_FIREBASE_API_KEY,
      firebaseAuthDomain: process.env.NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
      firebaseProjectId: process.env.NUXT_PUBLIC_FIREBASE_PROJECT_ID,
    }
  },
  typescript: {
    strict: true,
    typeCheck: true,
  }
})
```

**Step 11: Initialize backend dependencies**

Run:
```bash
cd backend
poetry install
```

Expected: Dependencies installed, virtual environment created

**Step 12: Initialize frontend dependencies**

Run:
```bash
cd frontend
npm install
```

Expected: Dependencies installed, node_modules created

**Step 13: Start local services**

Run:
```bash
docker-compose up -d
```

Expected: PostgreSQL and Redis containers running

**Step 14: Verify backend runs**

Run:
```bash
cd backend
poetry run uvicorn src.main:app --reload --port 8000
```

Expected: Server starts on http://localhost:8000, visit /health returns {"status": "healthy"}

**Step 15: Verify frontend runs**

Run:
```bash
cd frontend
npm run dev
```

Expected: Nuxt dev server starts on http://localhost:3000

**Step 16: Commit**

```bash
git add .
git commit -m "feat: initial project structure and environment setup"
```

---

## Task 2: Database Models & Migrations

**Files:**
- Create: `backend/src/models/base.py`
- Create: `backend/src/models/tenant.py`
- Create: `backend/src/models/user.py`
- Create: `backend/src/models/integration.py`
- Create: `backend/src/models/company.py`
- Create: `backend/src/models/contact.py`
- Create: `backend/src/models/ticket.py`
- Create: `backend/src/models/topic.py`
- Create: `backend/src/models/churn_risk.py`
- Create: `backend/src/core/database.py`
- Create: `backend/alembic/env.py`
- Create: `backend/tests/unit/test_models.py`

**Step 1: Create backend/src/core/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 2: Create backend/src/models/base.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from src.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UUIDMixin:
    """Mixin for UUID primary key."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**Step 3: Create backend/src/models/tenant.py**

```python
from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class PlanTier(str, enum.Enum):
    """Subscription plan tiers."""
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Tenant(Base, UUIDMixin, TimestampMixin):
    """Tenant model - companies using the churn risk app."""
    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    subdomain = Column(String(63), unique=True, nullable=False, index=True)
    plan_tier = Column(SQLEnum(PlanTier), default=PlanTier.STARTER, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="tenant", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="tenant", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="tenant", cascade="all, delete-orphan")
    topics = relationship("TicketTopic", back_populates="tenant", cascade="all, delete-orphan")
    churn_risks = relationship("ChurnRiskCard", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.subdomain})>"
```

**Step 4: Create backend/src/models/user.py**

```python
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """User model - people at each tenant company."""
    __tablename__ = "users"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    owned_churn_risks = relationship("ChurnRiskCard", foreign_keys="ChurnRiskCard.owner_id", back_populates="owner")
    comments = relationship("ChurnRiskComment", back_populates="user")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
```

**Step 5: Create backend/src/models/integration.py**

```python
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class IntegrationType(str, enum.Enum):
    """Types of integrations."""
    HUBSPOT = "hubspot"
    ZENDESK = "zendesk"
    HELPSCOUT = "helpscout"


class IntegrationStatus(str, enum.Enum):
    """Integration connection status."""
    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class Integration(Base, UUIDMixin, TimestampMixin):
    """Integration model - HubSpot/Zendesk connections."""
    __tablename__ = "integrations"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(IntegrationType), nullable=False)
    status = Column(SQLEnum(IntegrationStatus), default=IntegrationStatus.ACTIVE, nullable=False)
    credentials = Column(JSONB, nullable=False)  # Encrypted in production
    settings = Column(JSONB, default=dict)
    last_synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="integrations")

    def __repr__(self):
        return f"<Integration {self.type} for tenant {self.tenant_id}>"
```

**Step 6: Create backend/src/models/company.py**

```python
from sqlalchemy import Column, String, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base, UUIDMixin, TimestampMixin


class Company(Base, UUIDMixin, TimestampMixin):
    """Company model - the tenant's customers."""
    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_tenant_external", "tenant_id", "external_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)  # HubSpot company ID
    name = Column(String(255), nullable=False)
    mrr = Column(Numeric(10, 2), nullable=True)  # Monthly recurring revenue
    metadata = Column(JSONB, default=dict)  # Custom fields from CRM

    # Relationships
    tenant = relationship("Tenant", back_populates="companies")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="company")
    churn_risks = relationship("ChurnRiskCard", back_populates="company")

    def __repr__(self):
        return f"<Company {self.name} (MRR: ${self.mrr})>"
```

**Step 7: Create backend/src/models/contact.py**

```python
from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base, UUIDMixin, TimestampMixin


class Contact(Base, UUIDMixin, TimestampMixin):
    """Contact model - people at the companies."""
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_tenant_external", "tenant_id", "external_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    external_id = Column(String(255), nullable=False)  # HubSpot contact ID
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    company = relationship("Company", back_populates="contacts")
    tickets = relationship("Ticket", back_populates="contact")
    churn_risks = relationship("ChurnRiskCard", back_populates="contact")

    def __repr__(self):
        return f"<Contact {self.name} ({self.email})>"
```

**Step 8: Create backend/src/models/ticket.py**

```python
from sqlalchemy import Column, String, ForeignKey, Text, Enum as SQLEnum, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class TicketStatus(str, enum.Enum):
    """Ticket status."""
    NEW = "new"
    OPEN = "open"
    WAITING = "waiting"
    CLOSED = "closed"


class SentimentScore(str, enum.Enum):
    """Sentiment analysis scores."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class Ticket(Base, UUIDMixin, TimestampMixin):
    """Support ticket model."""
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_tenant_external", "tenant_id", "external_id"),
        Index("ix_tickets_tenant_sentiment", "tenant_id", "sentiment_score", "created_at"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)  # HubSpot ticket ID
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)

    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.NEW, nullable=False)

    # Sentiment analysis
    sentiment_score = Column(SQLEnum(SentimentScore), nullable=True, index=True)
    sentiment_confidence = Column(Float, nullable=True)
    sentiment_analyzed_at = Column(DateTime, nullable=True)

    external_url = Column(String(500), nullable=True)  # Deep link to HubSpot
    metadata = Column(JSONB, default=dict)  # Raw data from source

    # Relationships
    tenant = relationship("Tenant", back_populates="tickets")
    company = relationship("Company", back_populates="tickets")
    contact = relationship("Contact", back_populates="tickets")
    topic_assignments = relationship("TicketTopicAssignment", back_populates="ticket", cascade="all, delete-orphan")
    churn_risk = relationship("ChurnRiskCard", back_populates="ticket", uselist=False)

    def __repr__(self):
        return f"<Ticket {self.subject[:30]}... ({self.sentiment_score})>"
```

**Step 9: Create backend/src/models/topic.py**

```python
from sqlalchemy import Column, String, ForeignKey, Text, Boolean, Float, DateTime, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class TicketTopic(Base, UUIDMixin, TimestampMixin):
    """Ticket topic model - AI-generated categories."""
    __tablename__ = "ticket_topics"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_topic_name"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    training_prompt = Column(Text, nullable=True)  # User feedback for AI
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="topics")
    ticket_assignments = relationship("TicketTopicAssignment", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TicketTopic {self.name}>"


class AssignedBy(str, enum.Enum):
    """Who assigned the topic."""
    AI = "ai"
    USER = "user"


class TicketTopicAssignment(Base, UUIDMixin, TimestampMixin):
    """Many-to-many mapping between tickets and topics."""
    __tablename__ = "ticket_topic_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ticket_id", "topic_id", name="uq_ticket_topic"),
        Index("ix_assignments_tenant_ticket", "tenant_id", "ticket_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("ticket_topics.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, nullable=True)  # AI confidence score
    assigned_by = Column(SQLEnum(AssignedBy), default=AssignedBy.AI, nullable=False)
    assigned_at = Column(DateTime, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    ticket = relationship("Ticket", back_populates="topic_assignments")
    topic = relationship("TicketTopic", back_populates="ticket_assignments")

    def __repr__(self):
        return f"<Assignment ticket={self.ticket_id} topic={self.topic_id} ({self.assigned_by})>"
```

**Step 10: Create backend/src/models/churn_risk.py**

```python
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class TriggerType(str, enum.Enum):
    """Types of churn risk triggers."""
    FRUSTRATED = "frustrated"
    SIGNIFICANT_SUPPORT = "significant_support"
    SILENTLY_STRUGGLING = "silently_struggling"


class ChurnRiskStatus(str, enum.Enum):
    """Churn risk card status."""
    NEW = "new"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"


class ChurnRiskCard(Base, UUIDMixin, TimestampMixin):
    """Churn risk card model - Kanban cards for at-risk customers."""
    __tablename__ = "churn_risk_cards"
    __table_args__ = (
        Index("ix_churn_risks_tenant_status", "tenant_id", "status", "created_at"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_type = Column(SQLEnum(TriggerType), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True)  # Triggering ticket

    status = Column(SQLEnum(ChurnRiskStatus), default=ChurnRiskStatus.NEW, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="churn_risks")
    company = relationship("Company", back_populates="churn_risks")
    contact = relationship("Contact", back_populates="churn_risks")
    ticket = relationship("Ticket", back_populates="churn_risk")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_churn_risks")
    comments = relationship("ChurnRiskComment", back_populates="card", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChurnRiskCard {self.trigger_type} for company {self.company_id}>"


class ChurnRiskComment(Base, UUIDMixin, TimestampMixin):
    """Comment on a churn risk card."""
    __tablename__ = "churn_risk_comments"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey("churn_risk_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    mentions = Column(ARRAY(UUID(as_uuid=True)), default=list)  # User IDs tagged

    # Relationships
    tenant = relationship("Tenant")
    card = relationship("ChurnRiskCard", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Comment on card {self.card_id} by user {self.user_id}>"
```

**Step 11: Create backend/alembic.ini**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://postgres:password@localhost:5432/churn_risk_dev

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Step 12: Create backend/alembic/env.py**

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from src.core.database import Base
from src.core.config import settings

# Import all models so Alembic can detect them
from src.models.tenant import Tenant
from src.models.user import User
from src.models.integration import Integration
from src.models.company import Company
from src.models.contact import Contact
from src.models.ticket import Ticket
from src.models.topic import TicketTopic, TicketTopicAssignment
from src.models.churn_risk import ChurnRiskCard, ChurnRiskComment

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 13: Create initial migration**

Run:
```bash
cd backend
poetry run alembic revision --autogenerate -m "Initial schema"
```

Expected: Migration file created in `alembic/versions/`

**Step 14: Apply migration**

Run:
```bash
poetry run alembic upgrade head
```

Expected: All tables created in PostgreSQL

**Step 15: Write test for models**

Create `backend/tests/unit/test_models.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.tenant import Tenant, PlanTier
from src.models.user import User, UserRole
from src.models.company import Company


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_tenant(db_session):
    """Test creating a tenant."""
    tenant = Tenant(
        name="FlxPoint",
        subdomain="flxpoint",
        plan_tier=PlanTier.PRO
    )
    db_session.add(tenant)
    db_session.commit()

    assert tenant.id is not None
    assert tenant.name == "FlxPoint"
    assert tenant.subdomain == "flxpoint"
    assert tenant.plan_tier == PlanTier.PRO


def test_tenant_user_relationship(db_session):
    """Test tenant to user relationship."""
    tenant = Tenant(name="TestCo", subdomain="testco")
    db_session.add(tenant)
    db_session.commit()

    user = User(
        tenant_id=tenant.id,
        firebase_uid="test-firebase-uid",
        email="test@example.com",
        name="Test User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()

    assert len(tenant.users) == 1
    assert tenant.users[0].email == "test@example.com"
    assert user.tenant.name == "TestCo"


def test_company_cascade_delete(db_session):
    """Test cascade delete when tenant is deleted."""
    tenant = Tenant(name="TestCo", subdomain="testco")
    db_session.add(tenant)
    db_session.commit()

    company = Company(
        tenant_id=tenant.id,
        external_id="hubspot-123",
        name="Acme Corp",
        mrr=1000.00
    )
    db_session.add(company)
    db_session.commit()

    tenant_id = tenant.id
    db_session.delete(tenant)
    db_session.commit()

    # Company should be deleted due to cascade
    assert db_session.query(Company).filter_by(tenant_id=tenant_id).count() == 0
```

**Step 16: Run tests**

Run:
```bash
poetry run pytest tests/unit/test_models.py -v
```

Expected: All 3 tests pass

**Step 17: Commit**

```bash
git add .
git commit -m "feat: add database models and migrations"
```

---

## Task 3: Firebase Authentication Integration

**Files:**
- Create: `backend/src/core/auth.py`
- Create: `backend/src/api/dependencies.py`
- Create: `backend/tests/unit/test_auth.py`

**Step 1: Download Firebase credentials**

1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `backend/firebase-credentials.json`
4. Add to `.gitignore` (already done)

**Step 2: Create backend/src/core/auth.py**

```python
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.core.config import settings
from typing import Dict

# Initialize Firebase Admin SDK
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, str]:
    """
    Verify Firebase ID token from Authorization header.

    Returns:
        Dict with 'uid' and 'email' from decoded token.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email", ""),
        }
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )
```

**Step 3: Create backend/src/api/dependencies.py**

```python
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.auth import verify_firebase_token
from src.models.user import User
from typing import Dict


async def get_current_user(
    db: Session = Depends(get_db),
    token_data: Dict[str, str] = Depends(verify_firebase_token)
) -> User:
    """
    Get current authenticated user from database.

    Raises:
        HTTPException: If user not found in database.
    """
    user = db.query(User).filter(
        User.firebase_uid == token_data["uid"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please complete registration."
        )

    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have admin role."""
    from src.models.user import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user
```

**Step 4: Write test for auth (mock Firebase)**

Create `backend/tests/unit/test_auth.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.core.auth import verify_firebase_token


@pytest.mark.asyncio
async def test_verify_valid_token():
    """Test verifying a valid Firebase token."""
    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "test-uid-123",
            "email": "test@example.com"
        }

        result = await verify_firebase_token(mock_credentials)

        assert result["uid"] == "test-uid-123"
        assert result["email"] == "test@example.com"
        mock_verify.assert_called_once_with("valid-token")


@pytest.mark.asyncio
async def test_verify_invalid_token():
    """Test verifying an invalid Firebase token."""
    from firebase_admin import auth as firebase_auth

    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        mock_verify.side_effect = firebase_auth.InvalidIdTokenError("Invalid token")

        with pytest.raises(HTTPException) as exc_info:
            await verify_firebase_token(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_verify_expired_token():
    """Test verifying an expired Firebase token."""
    from firebase_admin import auth as firebase_auth

    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="expired-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        mock_verify.side_effect = firebase_auth.ExpiredIdTokenError("Token expired")

        with pytest.raises(HTTPException) as exc_info:
            await verify_firebase_token(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
```

**Step 5: Run tests**

Run:
```bash
poetry run pytest tests/unit/test_auth.py -v
```

Expected: All 3 tests pass

**Step 6: Update main.py to include auth endpoints**

Modify `backend/src/main.py`:

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.dependencies import get_current_user
from src.models.user import User

app = FastAPI(
    title="Churn Risk API",
    version="0.1.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get(f"{settings.API_V1_PREFIX}/")
async def root():
    """API root endpoint."""
    return {"message": "Churn Risk API", "version": "0.1.0"}


@app.get(f"{settings.API_V1_PREFIX}/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value,
        "tenant_id": str(current_user.tenant_id)
    }
```

**Step 7: Commit**

```bash
git add .
git commit -m "feat: add Firebase authentication integration"
```

---

## Task 4: OpenRouter AI Service Layer

**Files:**
- Create: `backend/src/services/ai_base.py`
- Create: `backend/src/services/openrouter.py`
- Create: `backend/src/schemas/ai.py`
- Create: `backend/tests/unit/test_openrouter.py`

**Step 1: Create backend/src/schemas/ai.py**

```python
from pydantic import BaseModel, Field
from typing import List
from src.models.ticket import SentimentScore


class TopicClassification(BaseModel):
    """Topic classification result."""
    topic_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class SentimentAnalysisResult(BaseModel):
    """Sentiment analysis result."""
    sentiment: SentimentScore
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str | None = None


class TicketAnalysisResult(BaseModel):
    """Combined ticket analysis result."""
    sentiment: SentimentAnalysisResult
    topics: List[TopicClassification]
```

**Step 2: Create backend/src/services/ai_base.py**

```python
from abc import ABC, abstractmethod
from typing import List
from src.schemas.ai import SentimentAnalysisResult, TopicClassification, TicketAnalysisResult


class SentimentAnalyzer(ABC):
    """Abstract base class for sentiment analysis."""

    @abstractmethod
    async def analyze_sentiment(self, ticket_content: str) -> SentimentAnalysisResult:
        """Analyze sentiment of ticket content."""
        pass


class TopicClassifier(ABC):
    """Abstract base class for topic classification."""

    @abstractmethod
    async def classify_topics(
        self,
        ticket_content: str,
        available_topics: List[str],
        training_rules: List[str] | None = None
    ) -> List[TopicClassification]:
        """Classify ticket into topics."""
        pass


class TicketAnalyzer(ABC):
    """Abstract base class for combined ticket analysis."""

    @abstractmethod
    async def analyze_ticket(
        self,
        ticket_content: str,
        available_topics: List[str] | None = None,
        training_rules: List[str] | None = None
    ) -> TicketAnalysisResult:
        """Analyze ticket for both sentiment and topics."""
        pass
```

**Step 3: Create backend/src/services/openrouter.py**

```python
import httpx
import json
from typing import List
from src.services.ai_base import TicketAnalyzer
from src.schemas.ai import SentimentAnalysisResult, TopicClassification, TicketAnalysisResult
from src.models.ticket import SentimentScore
from src.core.config import settings


class OpenRouterAnalyzer(TicketAnalyzer):
    """OpenRouter-based ticket analyzer using LLMs."""

    def __init__(
        self,
        api_key: str = settings.OPENROUTER_API_KEY,
        model: str = "openai/gpt-4o-mini"
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def analyze_ticket(
        self,
        ticket_content: str,
        available_topics: List[str] | None = None,
        training_rules: List[str] | None = None
    ) -> TicketAnalysisResult:
        """
        Analyze ticket using OpenRouter LLM.

        Performs both sentiment analysis and topic classification in a single call.
        """
        prompt = self._build_analysis_prompt(ticket_content, available_topics, training_rules)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert at analyzing customer support tickets."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            return self._parse_analysis_result(parsed)

    def _build_analysis_prompt(
        self,
        ticket_content: str,
        available_topics: List[str] | None,
        training_rules: List[str] | None
    ) -> str:
        """Build the prompt for ticket analysis."""
        prompt = f"""Analyze this customer support ticket for sentiment and topics.

Ticket Content:
{ticket_content}

Tasks:
1. Determine the sentiment (very_negative, negative, neutral, positive, very_positive)
2. Provide a confidence score (0.0 to 1.0) for the sentiment
3. Briefly explain your sentiment reasoning
"""

        if available_topics:
            prompt += f"""
4. Classify the ticket into one or more of these topics:
{', '.join(available_topics)}
5. For each topic, provide a confidence score (0.0 to 1.0)
"""

            if training_rules:
                prompt += f"""
User Training Rules (apply these when classifying):
{chr(10).join(f'- {rule}' for rule in training_rules)}
"""
        else:
            prompt += """
4. Suggest 2-3 topic categories for this ticket
5. For each suggested topic, provide a confidence score (0.0 to 1.0)
"""

        prompt += """
Return your analysis as JSON with this structure:
{
  "sentiment": {
    "score": "negative",
    "confidence": 0.85,
    "reasoning": "Customer expresses frustration..."
  },
  "topics": [
    {"name": "Performance Issues", "confidence": 0.9},
    {"name": "API Errors", "confidence": 0.7}
  ]
}
"""
        return prompt

    def _parse_analysis_result(self, parsed: dict) -> TicketAnalysisResult:
        """Parse the LLM response into structured result."""
        sentiment_data = parsed.get("sentiment", {})
        topics_data = parsed.get("topics", [])

        sentiment = SentimentAnalysisResult(
            sentiment=SentimentScore(sentiment_data.get("score", "neutral")),
            confidence=sentiment_data.get("confidence", 0.5),
            reasoning=sentiment_data.get("reasoning")
        )

        topics = [
            TopicClassification(
                topic_name=topic["name"],
                confidence=topic["confidence"]
            )
            for topic in topics_data
        ]

        return TicketAnalysisResult(sentiment=sentiment, topics=topics)
```

**Step 4: Write tests for OpenRouter service**

Create `backend/tests/unit/test_openrouter.py`:

```python
import pytest
from unittest.mock import patch, AsyncMock
from src.services.openrouter import OpenRouterAnalyzer
from src.models.ticket import SentimentScore


@pytest.mark.asyncio
async def test_analyze_ticket_with_topics():
    """Test analyzing a ticket with available topics."""
    analyzer = OpenRouterAnalyzer(api_key="test-key")

    mock_response_data = {
        "choices": [{
            "message": {
                "content": """{
                    "sentiment": {
                        "score": "negative",
                        "confidence": 0.85,
                        "reasoning": "Customer is frustrated with API errors"
                    },
                    "topics": [
                        {"name": "API Errors", "confidence": 0.9},
                        {"name": "Integration Help", "confidence": 0.6}
                    ]
                }"""
            }
        }]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response_data
        mock_post.return_value.raise_for_status = lambda: None

        result = await analyzer.analyze_ticket(
            ticket_content="The API keeps returning 500 errors!",
            available_topics=["API Errors", "Integration Help", "Performance Issues"]
        )

        assert result.sentiment.sentiment == SentimentScore.NEGATIVE
        assert result.sentiment.confidence == 0.85
        assert len(result.topics) == 2
        assert result.topics[0].topic_name == "API Errors"
        assert result.topics[0].confidence == 0.9


@pytest.mark.asyncio
async def test_analyze_ticket_without_topics():
    """Test analyzing a ticket without predefined topics."""
    analyzer = OpenRouterAnalyzer(api_key="test-key")

    mock_response_data = {
        "choices": [{
            "message": {
                "content": """{
                    "sentiment": {
                        "score": "positive",
                        "confidence": 0.95,
                        "reasoning": "Customer is very happy with the support"
                    },
                    "topics": [
                        {"name": "Support Quality", "confidence": 0.9}
                    ]
                }"""
            }
        }]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response_data
        mock_post.return_value.raise_for_status = lambda: None

        result = await analyzer.analyze_ticket(
            ticket_content="Thank you for the excellent support!",
            available_topics=None
        )

        assert result.sentiment.sentiment == SentimentScore.POSITIVE
        assert result.sentiment.confidence == 0.95
        assert len(result.topics) == 1
        assert result.topics[0].topic_name == "Support Quality"
```

**Step 5: Run tests**

Run:
```bash
poetry run pytest tests/unit/test_openrouter.py -v
```

Expected: Both tests pass

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add OpenRouter AI service layer"
```

---

## Task 5: HubSpot Integration & OAuth Flow

**Files:**
- Create: `backend/src/integrations/hubspot.py`
- Create: `backend/src/api/routers/integrations.py`
- Create: `backend/src/schemas/integration.py`
- Create: `backend/tests/integration/test_hubspot.py`

**Step 1: Create backend/src/schemas/integration.py**

```python
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from src.models.integration import IntegrationType, IntegrationStatus


class IntegrationBase(BaseModel):
    """Base integration schema."""
    type: IntegrationType


class IntegrationCreate(IntegrationBase):
    """Schema for creating an integration."""
    pass


class IntegrationResponse(IntegrationBase):
    """Schema for integration response."""
    id: str
    status: IntegrationStatus
    last_synced_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class HubSpotOAuthCallbackRequest(BaseModel):
    """Schema for HubSpot OAuth callback."""
    code: str
    redirect_uri: str
```

**Step 2: Create backend/src/integrations/hubspot.py**

```python
import httpx
from typing import Dict, List, Any
from datetime import datetime
from src.core.config import settings


class HubSpotClient:
    """Client for interacting with HubSpot API."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def exchange_code_for_token(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange OAuth authorization code for access token.

        Returns:
            Dict with 'access_token', 'refresh_token', 'expires_in'
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            return response.json()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.

        Returns:
            Dict with new 'access_token', 'refresh_token', 'expires_in'
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_tickets(
        self,
        limit: int = 100,
        after: str | None = None,
        properties: List[str] | None = None
    ) -> Dict[str, Any]:
        """
        Fetch tickets from HubSpot.

        Args:
            limit: Number of tickets to fetch (max 100)
            after: Pagination cursor
            properties: List of properties to fetch

        Returns:
            Dict with 'results' and 'paging' keys
        """
        default_properties = [
            "subject",
            "content",
            "hs_ticket_id",
            "hs_ticket_priority",
            "hs_pipeline_stage",
            "createdate",
            "hs_lastmodifieddate",
        ]

        params = {
            "limit": min(limit, 100),
            "properties": properties or default_properties,
        }

        if after:
            params["after"] = after

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/tickets",
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Fetch a single ticket by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/tickets/{ticket_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_companies(self, limit: int = 100) -> Dict[str, Any]:
        """Fetch companies from HubSpot."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/companies",
                headers=self.headers,
                params={"limit": min(limit, 100)},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_contacts(self, limit: int = 100) -> Dict[str, Any]:
        """Fetch contacts from HubSpot."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers=self.headers,
                params={"limit": min(limit, 100)},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def create_webhook_subscription(
        self,
        webhook_url: str,
        subscription_type: str = "ticket.creation"
    ) -> Dict[str, Any]:
        """
        Create a webhook subscription for real-time events.

        Args:
            webhook_url: URL to receive webhook events
            subscription_type: Type of event (e.g., "ticket.creation", "ticket.propertyChange")
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/webhooks/v3/{settings.HUBSPOT_CLIENT_ID}/subscriptions",
                headers=self.headers,
                json={
                    "enabled": True,
                    "subscriptionDetails": {
                        "subscriptionType": subscription_type,
                        "propertyName": None,
                    },
                    "webhookUrl": webhook_url,
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
```

**Step 3: Create backend/src/api/routers/integrations.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.api.dependencies import get_current_user, require_admin
from src.models.user import User
from src.models.integration import Integration, IntegrationType, IntegrationStatus
from src.schemas.integration import IntegrationResponse, HubSpotOAuthCallbackRequest
from src.integrations.hubspot import HubSpotClient
from datetime import datetime

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all integrations for the current tenant."""
    integrations = db.query(Integration).filter(
        Integration.tenant_id == current_user.tenant_id
    ).all()

    return [
        IntegrationResponse(
            id=str(integration.id),
            type=integration.type,
            status=integration.status,
            last_synced_at=integration.last_synced_at,
            created_at=integration.created_at
        )
        for integration in integrations
    ]


@router.get("/hubspot/authorize")
async def hubspot_authorize_url(
    current_user: User = Depends(require_admin)
):
    """Get HubSpot OAuth authorization URL."""
    from src.core.config import settings

    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={settings.HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={settings.HUBSPOT_REDIRECT_URI}"
        f"&scope=crm.objects.contacts.read crm.objects.companies.read tickets"
    )

    return {"authorization_url": auth_url}


@router.post("/hubspot/callback")
async def hubspot_oauth_callback(
    request: HubSpotOAuthCallbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Handle HubSpot OAuth callback."""
    try:
        # Exchange code for access token
        token_data = await HubSpotClient.exchange_code_for_token(
            code=request.code,
            redirect_uri=request.redirect_uri
        )

        # Check if integration already exists
        existing = db.query(Integration).filter(
            Integration.tenant_id == current_user.tenant_id,
            Integration.type == IntegrationType.HUBSPOT
        ).first()

        if existing:
            # Update existing integration
            existing.credentials = token_data
            existing.status = IntegrationStatus.ACTIVE
            existing.error_message = None
            integration = existing
        else:
            # Create new integration
            integration = Integration(
                tenant_id=current_user.tenant_id,
                type=IntegrationType.HUBSPOT,
                status=IntegrationStatus.ACTIVE,
                credentials=token_data
            )
            db.add(integration)

        db.commit()
        db.refresh(integration)

        return IntegrationResponse(
            id=str(integration.id),
            type=integration.type,
            status=integration.status,
            last_synced_at=integration.last_synced_at,
            created_at=integration.created_at
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to HubSpot: {str(e)}"
        )


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete an integration."""
    from uuid import UUID

    integration = db.query(Integration).filter(
        Integration.id == UUID(integration_id),
        Integration.tenant_id == current_user.tenant_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    db.delete(integration)
    db.commit()

    return {"message": "Integration deleted successfully"}
```

**Step 4: Update backend/src/main.py to include integration router**

Modify `backend/src/main.py`:

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.dependencies import get_current_user
from src.api.routers import integrations
from src.models.user import User

app = FastAPI(
    title="Churn Risk API",
    version="0.1.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(integrations.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get(f"{settings.API_V1_PREFIX}/")
async def root():
    """API root endpoint."""
    return {"message": "Churn Risk API", "version": "0.1.0"}


@app.get(f"{settings.API_V1_PREFIX}/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value,
        "tenant_id": str(current_user.tenant_id)
    }
```

**Step 5: Write integration test (manual testing required for OAuth)**

Create `backend/tests/integration/test_hubspot.py`:

```python
import pytest
from unittest.mock import patch, AsyncMock
from src.integrations.hubspot import HubSpotClient


@pytest.mark.asyncio
async def test_exchange_code_for_token():
    """Test exchanging OAuth code for access token."""
    mock_response = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 21600
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        result = await HubSpotClient.exchange_code_for_token(
            code="test-code",
            redirect_uri="http://localhost:8000/callback"
        )

        assert result["access_token"] == "test-access-token"
        assert result["refresh_token"] == "test-refresh-token"


@pytest.mark.asyncio
async def test_get_tickets():
    """Test fetching tickets from HubSpot."""
    client = HubSpotClient(access_token="test-token")

    mock_response = {
        "results": [
            {
                "id": "123",
                "properties": {
                    "subject": "Test ticket",
                    "content": "This is a test"
                }
            }
        ],
        "paging": {}
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = lambda: None

        result = await client.get_tickets(limit=10)

        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == "123"
```

**Step 6: Run tests**

Run:
```bash
poetry run pytest tests/integration/test_hubspot.py -v
```

Expected: Both tests pass

**Step 7: Commit**

```bash
git add .
git commit -m "feat: add HubSpot integration and OAuth flow"
```

---

## Next Steps Summary

**Updated Task Order** (as of 2025-11-08):

Tasks 1-5 completed (database, Firebase auth, OpenRouter AI, HubSpot OAuth).
Task 6 completed (Firebase frontend auth).

**HubSpot OAuth Status**: ✅ COMPLETED - Successfully connected to FlxPoint HubSpot, fetching real tickets, AI sentiment analysis working.

Remaining tasks:

- ~~**Task 6:** Frontend - Firebase Auth & Layout~~ ✅ COMPLETED
- **Task 7:** Ticket Import & Analysis Service (NEXT - bulk import 200 tickets, analyze with AI)
- **Task 8:** Churn Risk Card Creation Logic (create cards for negative sentiment)
- **Task 9:** Frontend - Dashboard with Analytics
- **Task 10:** Frontend - Churn Risk Kanban Board
- **Task 11:** Frontend - Topic Management UI
- **Task 12:** Frontend - Onboarding Flow UI
- **Task 13:** WebSocket Real-Time Updates (onboarding progress, new tickets)
- **Task 14:** HubSpot Webhook Handling (real-time ticket ingestion)
- **Task 15:** GCP Deployment (Cloud Run, Cloud SQL, Cloud Tasks)
- **Task 16:** End-to-End Testing & Polish

---

**Plan saved to:** `docs/plans/2025-11-06-phase-1-mvp-implementation.md`

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints between task groups

**Which approach would you like?**

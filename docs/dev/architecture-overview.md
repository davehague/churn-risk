# Architecture Overview - Churn Risk App

**Last Updated:** 2025-11-08

A simple, high-level view of the Churn Risk App architecture and how components connect.

---

## System Diagram

```mermaid
graph TB
    subgraph "Frontend (Nuxt 3)"
        UI[Vue 3 UI Components]
        WS[WebSocket Client]
    end

    subgraph "Backend (FastAPI)"
        API[REST API Endpoints]
        Auth[Firebase Auth Middleware]
        Services[Business Logic Services]
        AIService[OpenRouter AI Service]
        HubSpotClient[HubSpot OAuth Client]
        WebSocket[WebSocket Handler]
    end

    subgraph "Database (PostgreSQL)"
        DB[(Cloud SQL)]
        Migrations[Alembic Migrations]
    end

    subgraph "External Services"
        Firebase[Firebase Auth]
        OpenRouter[OpenRouter API<br/>LLM Gateway]
        HubSpot[HubSpot CRM<br/>OAuth + API]
    end

    subgraph "Background Jobs"
        Queue[Cloud Tasks Queue]
        Workers[Analysis Workers]
    end

    %% User interactions
    UI -->|HTTPS| API
    UI -->|WSS| WebSocket

    %% Backend authentication
    API --> Auth
    Auth -->|Verify JWT| Firebase

    %% Backend services
    API --> Services
    Services --> AIService
    Services --> HubSpotClient
    Services -->|Read/Write| DB

    %% AI analysis
    AIService -->|Analyze Tickets| OpenRouter

    %% HubSpot integration
    HubSpotClient -->|OAuth Flow| HubSpot
    HubSpotClient -->|Fetch Tickets| HubSpot

    %% Background processing
    Services -->|Enqueue| Queue
    Queue --> Workers
    Workers --> AIService
    Workers -->|Store Results| DB

    %% Database migrations
    Migrations -->|Create/Update Tables| DB

    %% Webhooks (future)
    HubSpot -.->|Webhook Events| API

    %% Styling
    classDef implemented fill:#90EE90,stroke:#333,stroke-width:2px
    classDef partial fill:#FFD700,stroke:#333,stroke-width:2px
    classDef notImplemented fill:#FFB6C1,stroke:#333,stroke-width:2px

    class API,Auth,Services,AIService,HubSpotClient,DB,Migrations,Firebase,OpenRouter,HubSpot implemented
    class UI,WebSocket,WS partial
    class Queue,Workers notImplemented
```

**Legend:**
- 🟢 **Green** = Fully implemented and tested
- 🟡 **Yellow** = Partially implemented
- 🔴 **Pink** = Not yet implemented

---

## Component Descriptions

### Frontend (Nuxt 3 + Vue 3)
**Status:** 🟡 Basic test page only

**Purpose:** User interface for viewing churn risks, managing topics, and configuring integrations.

**What Exists:**
- Project scaffolding with Nuxt 3, Tailwind CSS
- Basic test page for API validation
- CORS-enabled API calls to backend

**What's Missing:**
- Login/authentication UI
- Dashboard with charts
- Churn risk kanban board
- Topic management interface
- Onboarding flow UI

---

### Backend API (FastAPI)
**Status:** 🟢 Core endpoints implemented

**Purpose:** REST API handling authentication, business logic, and orchestrating services.

**Endpoints Implemented:**
- `GET /health` - Health check
- `GET /api/v1/` - API root information
- `GET /api/v1/integrations/hubspot/authorize` - Get OAuth URL
- `POST /api/v1/integrations/hubspot/callback` - OAuth callback
- `GET /api/v1/integrations` - List integrations
- `DELETE /api/v1/integrations/{id}` - Delete integration
- `GET /api/v1/users/me` - Current user info

**What's Missing:**
- Ticket import endpoints
- Churn risk card endpoints
- Topic management endpoints
- Webhook handlers

---

### Authentication (Firebase)
**Status:** 🟢 Backend ready, no users created yet

**Purpose:** User authentication and JWT token verification.

**What Works:**
- Firebase Admin SDK initialized
- JWT token verification middleware
- User lookup by Firebase UID
- Role-based access control (ADMIN, MEMBER, VIEWER)

**What's Missing:**
- Frontend Firebase SDK integration
- User registration flow
- Login UI
- No actual users created in Firebase

---

### Database (PostgreSQL + SQLAlchemy)
**Status:** 🟢 Fully implemented and migrated

**Tables Created (11 total):**
- `tenants` - Multi-tenant root entity
- `users` - User accounts linked to Firebase
- `integrations` - OAuth credentials storage
- `companies` - Customer companies (from HubSpot)
- `contacts` - People at customer companies
- `tickets` - Support tickets with sentiment
- `ticket_topics` - Configurable topics for classification
- `ticket_topic_assignments` - Many-to-many ticket ↔ topic
- `churn_risk_cards` - Generated churn risk alerts
- `churn_risk_comments` - Activity timeline on cards
- `alembic_version` - Migration tracking

**Migration:** `c08085465bad` (initial schema)

---

### AI Service (OpenRouter)
**Status:** 🟢 Fully working

**Purpose:** Sentiment analysis and topic classification using LLMs.

**Features:**
- Single LLM call for sentiment + topics (cost optimization)
- 5-level sentiment scoring (very_negative to very_positive)
- Confidence scores for all predictions
- Topic extraction with reasoning
- Retry logic with exponential backoff
- Error handling and validation

**Tested:** ✅ Analyzed sample tickets with 85% confidence

---

### HubSpot Integration
**Status:** 🟡 OAuth configured, not connected yet

**Purpose:** Fetch support tickets and company data from HubSpot CRM.

**Authentication:** OAuth 2.0 only (Developer API keys deprecated)

**What Exists:**
- HubSpot OAuth app created via CLI (`hs-churn-risk/`)
- OAuth client ID and secret configured
- OAuth authorization URL generation
- Token exchange and refresh methods
- API client for tickets, companies, contacts (OAuth tokens only)
- Webhook subscription method (not used yet)

**What's Missing:**
- Completed OAuth flow (needs user to authorize)
- Real ticket data import
- Webhook ingestion pipeline
- Incremental sync logic

---

### Background Jobs (Cloud Tasks)
**Status:** 🔴 Not implemented

**Purpose:** Asynchronous ticket analysis and bulk imports.

**Planned:**
- `ticket-analysis` queue - Process tickets through AI
- `bulk-import` queue - Initial 200 ticket import
- `notifications` queue - Email/Slack alerts

**Current Workaround:** Direct synchronous calls for now

---

## Data Flow Examples

### Onboarding Flow (Future)
```
User → Frontend → Backend → HubSpot OAuth
                           ← OAuth tokens stored
                           → Enqueue bulk import
Cloud Tasks Worker → Fetch 200 tickets from HubSpot
                  → Analyze each with OpenRouter
                  → Store tickets + sentiment in DB
                  → Create churn risk cards for negative tickets
                  → WebSocket push to frontend
Frontend ← Real-time progress updates
```

### Real-Time Ticket Ingestion (Future)
```
HubSpot → Webhook POST to /webhooks/hubspot
Backend → Validate signature
       → Enqueue analysis task
       → Return 200 OK
Cloud Tasks Worker → Fetch full ticket details
                  → Analyze sentiment + topics
                  → Create churn risk card if negative
                  → WebSocket push to frontend
```

### Current Working Flow
```
User → Frontend test page
     → Click "Get OAuth URL"
Backend → Generate HubSpot authorization URL
       → Return to frontend
User → Click link, authorize in HubSpot
HubSpot → Redirect to callback with code
Backend → Exchange code for tokens
       → Store in Integration model (requires auth)
```

---

## Technology Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| **Frontend** | Vue 3, Nuxt 3, Tailwind CSS | 🟡 Basic |
| **Backend** | FastAPI (Python 3.11) | 🟢 Core done |
| **Database** | PostgreSQL 15, SQLAlchemy | 🟢 Complete |
| **Auth** | Firebase Admin SDK | 🟢 Backend ready |
| **AI/ML** | OpenRouter (LLM gateway) | 🟢 Working |
| **Integrations** | HubSpot OAuth 2.0 | 🟡 Configured |
| **Background Jobs** | Cloud Tasks (GCP) | 🔴 Not implemented |
| **WebSockets** | FastAPI WebSocket | 🔴 Not implemented |
| **Migrations** | Alembic | 🟢 Complete |
| **Testing** | pytest, AsyncMock | 🟢 23/23 passing |
| **Hosting** | GCP Cloud Run, Cloud SQL | 🔴 Not deployed |

---

## Security Architecture

### Authentication Flow
1. User logs in via Firebase Auth (frontend)
2. Firebase returns JWT token
3. Frontend includes JWT in `Authorization: Bearer <token>` header
4. Backend middleware validates JWT with Firebase Admin SDK
5. Backend looks up User record by `firebase_uid`
6. Request proceeds with authenticated user context

### Multi-Tenancy
- Every table has `tenant_id` column
- All queries automatically filtered by tenant
- API returns 404 (not 403) for cross-tenant access attempts
- PostgreSQL Row-Level Security as safety net (future)

### Secrets Management
- Local development: `.env` file (not committed)
- Production: GCP Secret Manager (planned)
- OAuth tokens stored in encrypted JSONB column (encryption pending)

---

## Current Limitations

1. **No Real Users Yet**
   - Firebase project created but no users
   - Can't test authenticated endpoints end-to-end

2. **OAuth Not Connected**
   - HubSpot app configured
   - User needs to authorize to get access tokens
   - Can't fetch real tickets yet

3. **No Background Processing**
   - All operations are synchronous
   - Won't scale for bulk imports
   - Cloud Tasks queue not set up

4. **No Real UI**
   - Only a test page exists
   - Dashboard, kanban board, onboarding flow all pending

5. **Not Deployed**
   - Running locally only
   - GCP infrastructure not provisioned

---

## What's Next (Tasks 6-16)

See detailed plan in: `docs/plans/2025-11-06-phase-1-mvp-implementation.md`

**Immediate Next Steps:**
- **Task 6:** Ticket Import & Analysis Service (bulk processing)
- **Task 7:** Churn Risk Card Creation Logic (auto-create from sentiment)
- **Task 8:** WebSocket Real-Time Updates (onboarding progress)

**Then:**
- Tasks 9-13: Frontend UI (auth, dashboard, kanban, topics)
- Task 14: Webhook handling (real-time ingestion)
- Tasks 15-16: GCP deployment & end-to-end testing

---

## Testing

- **Unit Tests:** 23/23 passing (auth, models, AI, HubSpot)
- **Smoke Tests:** `backend/scripts/smoke_test.py`
- **Manual Testing:** Frontend test page at http://localhost:3000
- **Full Guide:** `docs/dev/testing-guide.md`

---

**Document Owner:** David Hague
**Last Review:** 2025-11-08

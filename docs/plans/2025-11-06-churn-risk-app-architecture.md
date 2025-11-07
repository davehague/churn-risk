# Churn Risk App - Architecture Design

**Date:** 2025-11-06
**Status:** Approved
**Product Name:** TBD (working name: ChurnGuard)

## Executive Summary

A multi-tenant SaaS application that identifies at-risk customers by analyzing support ticket sentiment and patterns. Integrates with ticketing systems (starting with HubSpot) to provide real-time churn risk detection, intelligent topic categorization, and actionable insights for SaaS companies.

**Target Market:** SMB to mid-market SaaS companies (10-30 employees, $200K+ ARR, 500+ support tickets/month)

**Key Differentiators:**
- Immediate "wow moment" during onboarding (analyze 200 tickets, show insights instantly)
- AI-powered topic classification with bi-directional learning (system + user train each other)
- Multi-phase rollout strategy with clear value at each tier

---

## Architecture Overview

### High-Level Components

```
┌─────────────────┐
│   Nuxt (Vue 3)  │  Frontend (Cloud Run / Firebase Hosting)
│   Multi-tenant  │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────────────────────────┐
│            FastAPI Backend (Cloud Run)              │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ REST API     │  │ WebSocket   │  │ Webhook    │ │
│  │ Endpoints    │  │ (Real-time) │  │ Handlers   │ │
│  └──────────────┘  └─────────────┘  └────────────┘ │
└──────────┬──────────────────┬───────────────────────┘
           │                  │
           ▼                  ▼
┌──────────────────┐   ┌─────────────────┐
│  Cloud SQL       │   │  Cloud Tasks    │
│  (PostgreSQL)    │   │  (Job Queue)    │
│  Multi-tenant DB │   │  AI Analysis    │
└──────────────────┘   └─────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  External Integrations           │
│  • HubSpot API (OAuth)           │
│  • OpenRouter (LLM Gateway)      │
│  • Firebase Auth                 │
└──────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- Vue 3 + Nuxt 3 (SSR)
- Tailwind CSS
- WebSocket for real-time updates

**Backend:**
- FastAPI (Python async)
- SQLAlchemy (ORM)
- Alembic (migrations)
- Pydantic (validation)

**Infrastructure (GCP):**
- Cloud Run (API + Frontend hosting)
- Cloud SQL (PostgreSQL 15+)
- Cloud Tasks (background jobs)
- Cloud Storage (attachments, optional)
- Firebase Auth (user authentication)
- Cloud Build (CI/CD)

**AI/ML:**
- OpenRouter API (LLM gateway)
- Initial models: GPT-4o-mini, Claude 3.5 Sonnet
- Architecture supports swapping to hybrid ML approach later

---

## Data Model (High-Level)

### Multi-Tenant Structure

**Core Tenant Entities:**
- `tenants` - Companies using the app (e.g., FlxPoint)
- `users` - People at each tenant
- `integrations` - HubSpot/Zendesk connections with encrypted credentials

**Customer Data (Tenant's Customers):**
- `companies` - The tenant's customers (imported from HubSpot)
- `contacts` - People at those companies
- `tickets` - Support tickets with sentiment analysis
- `ticket_topics` - AI-generated + user-refined categories
- `ticket_topic_assignments` - Many-to-many mapping

**Churn Risk Management:**
- `churn_risk_cards` - Kanban cards for at-risk customers
- `churn_risk_comments` - Comments/activity timeline
- `topic_training_rules` - User feedback for AI learning

**Tenant Isolation:**
- Every table has `tenant_id` column
- All queries filtered by tenant
- PostgreSQL Row-Level Security as safety net
- API returns 404 (not 403) for cross-tenant access attempts

---

## Phase 1: Frustrated Customers (MVP)

### Features

1. **HubSpot Integration**
   - OAuth connection
   - Initial import of 200 recent tickets
   - Webhook subscription for real-time new tickets

2. **Sentiment Analysis**
   - Every ticket analyzed: very_negative, negative, neutral, positive, very_positive
   - Confidence score tracked
   - Negative/very negative → creates churn risk card

3. **Topic Classification**
   - AI generates 8-12 initial topics from 200 tickets
   - User can merge, rename, delete topics during onboarding
   - Each ticket tagged with 1+ topics

4. **Churn Risk Board (Kanban)**
   - Columns: New, Working, Waiting, Completed
   - Cards show: contact, company, MRR, ticket link, topics
   - Comment timeline with @mentions
   - Owner assignment

5. **Basic Reporting**
   - Dashboard with metrics (Total Tickets, High-Risk Companies, etc.)
   - 30-day churn risk trend
   - Top companies by ticket volume
   - Ticket topic distribution (pie chart)

### Onboarding Flow (The "Wow Moment")

1. **Sign Up** (Firebase Auth - email/password or Google OAuth)
2. **Connect HubSpot** (OAuth flow - 30 seconds)
3. **Real-Time Analysis Screen**
   - Live feed of tickets being analyzed
   - Shows: company name, subject, sentiment badge as classified
   - Running counter: "47 of 200 analyzed..."
   - Topics appear in growing word cloud
4. **After ~50 tickets (2-3 min):**
   - Redirect to Dashboard with preliminary data
   - Banner: "Still analyzing - dashboard updates automatically"
5. **Topic Refinement** (optional, can skip)
   - Review AI-generated topics
   - Merge similar topics (prompted for reason)
   - System learns from feedback
6. **Full Analysis Complete**
   - Toast notification + email
   - Dashboard fully populated
   - Ready to use

**Technical Implementation:**
- WebSocket connection for real-time UI updates
- Cloud Tasks queue for background ticket processing
- Batch processing with progress tracking
- Dashboard cache updates as tickets complete

---

## Topic Management & AI Training (Secret Sauce)

### Bi-Directional Learning System

**Initial Discovery (Onboarding):**
- AI analyzes 200 tickets → generates 8-12 topics
- User reviews and refines:
  - Merge topics → explain why
  - Rename → AI adjusts understanding
  - Delete → ignore similar patterns

**Ongoing Learning (Two-Way):**

**User → System (Manual Rules):**
- "New Rule" interface: natural language input
- Example: "Anything mentioning slow load times or performance should go into Performance Issues"
- Stored as `training_prompt` on topic
- Applied to future classifications

**System → User (AI Suggestions):**
- AI detects patterns: "Last 5 'inventory not updating' tickets manually moved to Data Sync"
- Suggests new rule: "💡 'Inventory update problems' → Data Sync Issues"
- User can accept, edit, reject, or silence

**Continuous Improvement:**
- Low-confidence classifications (<70%) flagged for review
- User corrections become highest-value training data
- System tracks which rules are most effective

**Topic Intelligence UI:**
- Active Rules (user-approved, in effect)
- Suggested Rules (AI-detected patterns)
- Recent Low-Confidence Classifications (need review)
- Topic Analytics (growing/declining topics)

### LLM Prompt Structure

```
You are analyzing a support ticket. Classify it into one or more topics.

Available Topics:
- Performance Issues
- Integration Help
- Data Sync Issues
- API Errors
...

User Training Rules:
- Performance Issues: "slow load times, timeout errors, laggy UI"
- Data Sync Issues: "quantity sync and pricing sync are always data sync, not general integration"
...

Ticket Content:
[ticket text]

Return: topic IDs and confidence scores (0-1)
```

---

## AI/ML Service Architecture

### Abstraction Layer

```python
# Interface (contract)
class SentimentAnalyzer:
    def analyze_sentiment(self, ticket_content: str) -> tuple[str, float]:
        """Returns (sentiment_score, confidence)"""
        pass

class TopicClassifier:
    def classify_topics(
        self,
        ticket_content: str,
        available_topics: list[Topic],
        training_rules: list[str]
    ) -> list[tuple[Topic, float]]:
        """Returns [(topic, confidence), ...]"""
        pass

    def suggest_new_rules(self, recent_tickets: list[Ticket]) -> list[str]:
        """Analyzes patterns, suggests new training rules"""
        pass
```

### Phase 1: LLM-Based Implementation

**Provider:** OpenRouter API
- Single API for multiple LLM providers
- Easy model switching: GPT-4o-mini ↔ Claude 3.5 Sonnet ↔ Gemini
- Cost tracking per tenant per model
- Tenant-level model preference: `tenant.settings.ai_model`

**Combined Analysis (Efficient):**
- Single LLM call analyzes both sentiment + topics
- Reduces latency and cost
- Structured output (JSON mode)

**Initial Model:** GPT-4o-mini
- Cost: ~$0.15 per 1M input tokens
- Fast, cheap, good accuracy
- Can upgrade to Claude/GPT-4 for better results

### Future: Hybrid Approach (Phase 2+)

**When to migrate:**
- If LLM costs become significant (>$500/month)
- If latency matters (sub-second analysis needed)

**Hybrid Strategy:**
- Traditional ML sentiment model (VADER, fine-tuned BERT) as first pass
- Fast, cheap, handles 80% of cases
- LLM only for edge cases (borderline sentiment, complex topics)
- Same interface → swap implementation without changing app code

---

## Real-Time Data Sync

### Webhook-Based Ingestion (Phase 1)

**HubSpot Webhooks:**
1. During onboarding, subscribe to ticket events:
   - `ticket.created`
   - `ticket.updated`
2. HubSpot sends POST to `/webhooks/hubspot/tickets`
3. Webhook handler:
   - Validates signature
   - Enqueues Cloud Task for analysis
   - Returns 200 immediately
4. Background task:
   - Fetches full ticket from HubSpot API
   - Runs sentiment + topic analysis
   - Creates churn risk card if negative sentiment
   - Sends real-time update to frontend (WebSocket)

**Error Handling:**
- Webhook retries (HubSpot retries on 5xx)
- Dead letter queue for failed analysis jobs
- Alert if webhook endpoint unreachable >5 min

### Future: Polling Backup (Phase 2)

- Hourly cron job checks for missed tickets
- Catches webhook failures
- Ensures no tickets slip through

---

## Authentication & Authorization

### Firebase Auth Integration

**User Authentication:**
- Email/password sign-up
- Google OAuth (primary for SaaS personas)
- JWT tokens for API authentication
- FastAPI validates JWT on every request

**Flow:**
1. User signs up → Firebase creates account
2. User record created in Cloud SQL with `tenant_id`
3. Frontend stores Firebase JWT
4. API requests include `Authorization: Bearer <jwt>`
5. FastAPI middleware:
   - Validates JWT with Firebase
   - Extracts `user_id` → looks up `tenant_id`
   - Attaches to request context

### Tenant Isolation

**Query-Level Filtering:**
```python
# Every query automatically filtered
def get_tickets(db: Session, current_user: User):
    return db.query(Ticket).filter(
        Ticket.tenant_id == current_user.tenant_id
    ).all()
```

**PostgreSQL Row-Level Security (Safety Net):**
```sql
-- Prevent cross-tenant queries at DB level
CREATE POLICY tenant_isolation ON tickets
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**API Security:**
- 404 responses for cross-tenant access (not 403 - don't leak existence)
- Rate limiting per tenant
- API keys for webhook endpoints (HMAC signature validation)

### Role-Based Access Control (RBAC)

**Roles:**
- `admin` - full access, can manage users/integrations
- `member` - can view/edit churn risks, add comments
- `viewer` - read-only access to dashboards

**Future:** Custom roles per tenant

---

## GCP Infrastructure Details

### Cloud Run Configuration

**API Service:**
- Container: Python 3.11 FastAPI app
- Min instances: 1 (avoid cold starts during business hours)
- Max instances: 10 (Phase 1), scale up later
- CPU: 1 vCPU, Memory: 512MB (start small)
- Concurrency: 80 requests per instance
- Timeout: 300s (for long-running imports)

**Frontend Service:**
- Nuxt SSR or static build
- Min instances: 0 (can tolerate cold start)
- Max instances: 5
- CPU: 1 vCPU, Memory: 256MB

### Cloud SQL Configuration

**Instance:**
- PostgreSQL 15
- Machine type: db-f1-micro (start small, upgrade as needed)
- Storage: 10GB SSD (auto-expand)
- Private IP only (not exposed to internet)
- Automated backups: daily, 7-day retention
- Point-in-time recovery enabled

**Connection:**
- Cloud SQL Proxy from Cloud Run
- Connection pooling (SQLAlchemy)

### Cloud Tasks (Background Jobs)

**Queues:**
- `ticket-analysis` - sentiment/topic analysis (high priority)
- `bulk-import` - onboarding imports (can be slower)
- `notifications` - emails, webhooks (low priority)

**Configuration:**
- Max concurrent: 10 (Phase 1)
- Retry: 3 attempts with exponential backoff
- Dead letter queue for failures

### CI/CD Pipeline

**Cloud Build:**
1. Push to `main` branch → triggers build
2. Run tests (pytest)
3. Build Docker image
4. Push to Artifact Registry
5. Deploy to Cloud Run (with --no-traffic)
6. Run smoke tests
7. Route traffic to new revision

**Environments:**
- `dev` - manual deploys from feature branches
- `staging` - auto-deploy from `main`
- `production` - manual promotion from staging

---

## Phase 2 & 3 (Future)

### Phase 2: Significant Support Customers

**Triggers (configurable per tenant):**
- Support ticket with 10+ emails in last 5 days
- Company with 3+ support tickets in last 7 days
- Company with 25+ total emails in last 30 days

**Implementation:**
- Additional churn risk card type: `trigger_type = 'significant_support'`
- Cron job evaluates rules hourly
- Different plan tier (Pro plan)

### Phase 3: Silently Struggling Customers

**Triggers (custom CRM fields):**
- Company without login in last 8 days
- Registration >30 days, onboarding step 3 incomplete
- High MRR (>$999/mo) but low product usage

**Implementation:**
- HubSpot custom field mapping UI
- User maps product metrics → CRM custom fields
- Rule builder: "IF [login_days] > 8 THEN create churn risk"
- Enterprise plan feature

---

## Security Considerations

**Data Protection:**
- All credentials encrypted at rest (Cloud SQL encryption)
- HubSpot API keys stored in Secret Manager
- TLS 1.3 for all connections
- No PII in logs

**API Security:**
- Rate limiting (per tenant, per IP)
- CORS configured for known origins only
- CSRF protection on state-changing endpoints
- Webhook signature validation

**Compliance:**
- GDPR-ready: tenant data deletion endpoint
- SOC 2 considerations for future
- Audit logging for sensitive operations

---

## Monitoring & Observability

**Google Cloud Monitoring:**
- Cloud Run metrics (latency, errors, instance count)
- Cloud SQL metrics (connections, queries, storage)
- Custom metrics: tickets analyzed per hour, LLM costs per tenant

**Logging:**
- Structured JSON logs (Cloud Logging)
- Log levels: ERROR for alerts, INFO for audit trail
- Correlation IDs for request tracing

**Alerting:**
- Error rate >5% for 5 minutes
- Cloud SQL storage >80%
- Webhook endpoint down >5 minutes
- LLM API errors

**Cost Tracking:**
- GCP billing alerts ($100, $500, $1000 thresholds)
- Per-tenant LLM cost tracking (OpenRouter usage API)
- Monthly cost dashboard

---

## MVP Success Criteria

**Technical:**
- Onboard FlxPoint successfully
- Analyze 200 tickets in <5 minutes
- Real-time webhook ingestion working
- Zero data leaks between tenants
- 99% uptime during business hours

**Product:**
- "Wow moment" achieved (user sees value in first 3 minutes)
- Topic classification >80% accurate after user training
- At least 5 churn risk cards created in first week
- User trains AI at least 3 times (merge/new rule)

**Business:**
- FlxPoint uses it daily for 30 days
- Travis can point to 1 customer saved from churn
- 3 other beta customers onboarded
- <$50/month infrastructure costs (within GCP free tier)

---

## Open Questions / Future Decisions

1. **Product name** - ChurnGuard, ChurnShield, RiskRadar?
2. **Pricing model** - Per seat, per ticket volume, flat monthly?
3. **Free tier** - What features/limits?
4. **Subdomain strategy** - `flxpoint.churnguard.com` or single app with tenant switcher?
5. **Email notifications** - SendGrid, AWS SES, or Cloud Tasks?
6. **Should we build a mobile app eventually?** (Probably not Phase 1)

---

## Next Steps

1. **Set up GCP project** (new account for free credits)
2. **Initialize repository** (monorepo vs separate frontend/backend)
3. **Database schema** (detailed ERD, Alembic migrations)
4. **HubSpot OAuth flow** (test with FlxPoint account)
5. **Prototype sentiment analysis** (test OpenRouter with real tickets)
6. **Build onboarding flow** (focus on "wow moment")

---

**Document Owner:** David Hague
**Contributors:** Travis (product vision), Claude (architecture)
**Last Updated:** 2025-11-06

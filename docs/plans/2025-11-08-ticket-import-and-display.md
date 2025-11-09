# Ticket Import and Display Feature Design

**Date:** 2025-11-08
**Status:** Approved for Implementation

## Overview

Implement ticket fetching from HubSpot, sentiment analysis caching, and dashboard display with filtered tabs. Users will see tickets from the last 7 days with AI-powered sentiment analysis in a card-based interface.

## Requirements

- Fetch tickets created in the last 7 days from HubSpot
- Store tickets in database with unique `external_id` to prevent duplicates
- Analyze sentiment only for new tickets (cache results to avoid re-analysis)
- Display tickets in card format on dashboard with tabs for filtering by sentiment
- Click card to open modal with full ticket details
- Hybrid sync approach: auto-fetch on first load if no recent tickets, manual refresh button available

## Backend Architecture

### Ticket Import Service

**Location:** `src/services/ticket_import.py`

**Responsibilities:**
1. Fetch tickets from HubSpot API filtered by creation date (last 7 days)
2. Upsert tickets to database using `external_id` as unique key
3. Skip sentiment analysis for tickets that already have `sentiment_score`
4. Analyze new tickets using OpenRouter AI service
5. Update `sentiment_score`, `sentiment_confidence`, and `sentiment_analyzed_at` fields

**Key Logic:**
```python
async def import_and_analyze_tickets(tenant_id: UUID, db: Session) -> ImportResult:
    # 1. Get HubSpot integration for tenant
    # 2. Fetch tickets from last 7 days using HubSpot API
    # 3. For each ticket:
    #    - Upsert to database (match on external_id)
    #    - If sentiment_score is None: analyze with AI
    #    - Update sentiment fields
    # 4. Return summary: imported, analyzed, skipped, failed
```

**Caching Strategy:**
- Trust existing sentiment analysis completely (never re-analyze)
- Check: `if ticket.sentiment_score is not None: skip analysis`
- This saves API costs and processing time

### API Endpoints

**POST /api/v1/tickets/import**

Triggers ticket import and analysis for current user's tenant.

```python
Request: (empty body, tenant from auth token)
Response: {
  "imported": 15,      # New tickets added to DB
  "analyzed": 12,      # Tickets analyzed with AI
  "skipped": 3,        # Already had sentiment
  "failed": 0          # Analysis failures
}
```

**GET /api/v1/tickets**

Fetch tickets for current user's tenant with optional filtering.

```python
Query params:
  - sentiment?: "positive" | "negative" | "neutral" | "very_positive" | "very_negative"
  - limit?: number (default 100)
  - offset?: number (default 0)

Response: {
  "tickets": [
    {
      "id": "uuid",
      "external_id": "12345",
      "subject": "Cannot login",
      "content": "I've been trying to login for the past hour...",
      "sentiment_score": "negative",
      "sentiment_confidence": 0.87,
      "sentiment_analyzed_at": "2025-11-08T14:30:00Z",
      "created_at": "2025-11-01T10:30:00Z",
      "status": "open",
      "company": {"id": "uuid", "name": "Acme Corp"},
      "contact": {"id": "uuid", "name": "John Doe", "email": "john@acme.com"},
      "external_url": "https://app.hubspot.com/contacts/123/ticket/456"
    }
  ],
  "total": 15
}
```

### Database Strategy

**Existing Model:** `Ticket` (no changes needed)

Key fields used:
- `external_id` - HubSpot ticket ID (unique per tenant)
- `sentiment_score` - Cached AI analysis result
- `sentiment_confidence` - Confidence level (0.0-1.0)
- `sentiment_analyzed_at` - Timestamp of analysis
- `created_at` - Ticket creation date (for 7-day filter)

**Index:** Already exists on `(tenant_id, external_id)` for fast upsert lookups

### Error Handling (Backend)

| Scenario | Response | Behavior |
|----------|----------|----------|
| No HubSpot integration | 404 | "HubSpot not connected" |
| HubSpot rate limit | 429 | Return retry-after header |
| OAuth token expired | 401 | "Re-authenticate required" |
| OpenRouter API failure | 200 (partial) | Skip failed tickets, return summary with `failed` count |
| No tickets found | 200 | `{imported: 0, analyzed: 0, skipped: 0}` |

**Data Consistency:**
- Use database transaction for ticket upsert + sentiment update
- Idempotent: safe to call import multiple times
- Partial failures: successfully analyzed tickets remain saved

## Frontend Architecture

### Dashboard Layout

**Location:** `frontend/pages/dashboard.vue`

**Header Section:**
- Dashboard title
- "Refresh Tickets" button → calls `POST /tickets/import`
- Last sync timestamp (from most recent ticket)

**Tab Navigation:**
- "All Tickets" - Show all tickets
- "Negative Sentiment" - Filter to negative/very_negative (churn risk focus)
- "Positive Sentiment" - Filter to positive/very_positive
- "Neutral" - Filter to neutral only

**Ticket Grid:**
- Responsive: 1 column (mobile), 2-3 columns (tablet/desktop)
- Sort: Newest first by `created_at`

**Card Content:**
- Sentiment badge (color-coded: red=negative, green=positive, gray=neutral)
- Ticket subject (bold, truncate to 2 lines)
- Content preview (first 150 characters + "...")
- Company name (if available)
- Created date (relative: "2 days ago")
- Confidence score (small text: "87% confidence")

**Click Behavior:** Open ticket detail modal

### Ticket Detail Modal

**Component:** `frontend/components/TicketDetailModal.vue`

**Header:**
- Large sentiment badge with confidence percentage
- Ticket subject (full, no truncation)
- Close button (X in top-right)

**Body (scrollable):**

**Metadata Section:**
- Created date (full timestamp)
- Status badge (new/open/waiting/closed)
- Company name (text for MVP, link in future)
- Contact name and email (if available)
- "View in HubSpot" button → `external_url`

**Content Section:**
- Full ticket content (preserve line breaks)
- Topic tags (if available from future topic classification)

**Analysis Section:**
- Sentiment: badge (POSITIVE/NEGATIVE/NEUTRAL)
- Confidence: progress bar (e.g., 85%)
- Analyzed at: timestamp

**Footer:**
- "Close" button
- (Future) "Re-analyze" button (grayed out for MVP)

**Behavior:**
- ESC key closes modal
- Click outside closes modal
- Focus trap for accessibility

### State Management

**Pinia Store:** `frontend/stores/tickets.ts`

```typescript
interface TicketsState {
  tickets: Ticket[]
  loading: boolean
  selectedTicket: Ticket | null
  lastSync: Date | null
}

Actions:
- fetchTickets(sentiment?: string) - GET /tickets
- importTickets() - POST /tickets/import
- selectTicket(ticket: Ticket) - Open modal
- closeTicket() - Close modal

Getters:
- negativeTickets - Filter by negative/very_negative
- positiveTickets - Filter by positive/very_positive
- neutralTickets - Filter by neutral
```

### Auto-fetch Logic

**On Dashboard Mount:**
1. Check if any tickets exist with `created_at` in last 7 days
2. If no tickets found → automatically call `importTickets()`
3. Show loading state with progress message
4. Once complete, call `fetchTickets()` to display results

**Manual Refresh:**
- User clicks "Refresh Tickets" button
- Call `importTickets()` → `fetchTickets()`
- Show loading spinner on button

### Error Handling (Frontend)

| Scenario | UI Behavior |
|----------|-------------|
| No HubSpot integration | Error banner: "Connect HubSpot to import tickets" with setup link |
| Rate limit (429) | Toast: "Rate limit reached. Try again in X minutes" |
| Token expired (401) | Redirect to integration setup page |
| Network timeout | Error toast with retry button |
| No tickets found | Empty state: "No tickets found in the last 7 days" with illustration |
| Partial import failure | Warning banner: "3 tickets failed analysis" + display successful ones |

**Loading States:**
- Skeleton cards while fetching
- Progress indicator during import: "Importing tickets... 5/20 analyzed"

## Sequence Flow

**First-Time User:**
1. User navigates to `/dashboard`
2. Dashboard checks: "Are there tickets from last 7 days?"
3. No → Auto-trigger `POST /tickets/import`
4. Show progress: "Fetching tickets from HubSpot..."
5. Import completes → call `GET /tickets`
6. Display cards in "All Tickets" tab

**Returning User:**
1. User navigates to `/dashboard`
2. Tickets exist → call `GET /tickets`
3. Display cards immediately
4. User can click "Refresh" to re-import

**Clicking a Card:**
1. User clicks ticket card
2. Set `selectedTicket` in store
3. Open `TicketDetailModal` component
4. Display full ticket details

## Implementation Notes

### HubSpot Date Filtering

Use HubSpot API filter for `createdate`:
```python
filters = {
    "filterGroups": [{
        "filters": [{
            "propertyName": "createdate",
            "operator": "GTE",
            "value": (datetime.now() - timedelta(days=7)).timestamp() * 1000
        }]
    }]
}
```

### Sentiment Color Scheme

```css
very_negative: red-600 (#dc2626)
negative: red-400 (#f87171)
neutral: gray-400 (#9ca3af)
positive: green-400 (#4ade80)
very_positive: green-600 (#16a34a)
```

### Performance Considerations

- Limit HubSpot API to 100 tickets per import (configurable)
- Process tickets in batches of 10 for AI analysis
- Use async/await to parallelize API calls where possible
- Client-side filtering for tabs (no extra API calls)

## Out of Scope (Future Enhancements)

- Configurable date ranges (7/30/90 days)
- Re-analyze button in modal
- Webhook-based real-time ingestion
- Topic classification display
- Company/contact deep links
- Pagination for large ticket volumes
- Export tickets to CSV

## Success Criteria

- ✅ User can see tickets from last 7 days on dashboard
- ✅ Sentiment analysis runs only once per ticket
- ✅ Cards display subject, preview, sentiment, and metadata
- ✅ Tabs filter by sentiment (all/positive/negative/neutral)
- ✅ Modal shows full ticket details
- ✅ Auto-import on first load
- ✅ Manual refresh button works
- ✅ No duplicate tickets in database
- ✅ Error states handled gracefully

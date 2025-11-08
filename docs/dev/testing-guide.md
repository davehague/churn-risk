# Testing Guide - Sanity Tests

**Last Updated:** 2025-11-08

This guide provides step-by-step instructions for validating the Churn Risk App is working correctly before continuing development.

---

## Prerequisites

Make sure the following are running:

1. **PostgreSQL & Redis** (Docker):
   ```bash
   docker-compose up -d
   ```

2. **Backend Server**:
   ```bash
   cd backend
   poetry run uvicorn src.main:app --reload --port 8000
   ```

3. **Frontend Server**:
   ```bash
   cd frontend
   npm run dev
   ```

---

## Test 1: Backend Health & API

### Using the Frontend UI (Easiest)

1. **Open the test page**: http://localhost:3000

2. **Test Backend Health**:
   - Click "Test Health Endpoint" button
   - Should see: `{"status": "healthy", "environment": "development"}`

3. **Test API Root**:
   - Click "Test API Root" button
   - Should see: `{"message": "Churn Risk API", "version": "1.0.0", ...}`

4. **Test HubSpot OAuth**:
   - Click "Get OAuth Authorization URL" button
   - Should see OAuth URL returned with your client ID
   - Click "Open HubSpot Authorization →" to test full OAuth flow
   - You'll be redirected to HubSpot, authorize, then redirected back to callback

**Expected Results:**
- ✅ All three tests should show green success
- ✅ Test Summary at bottom should show all three as "✅"

### Using curl (Alternative)

```bash
# Health check
curl http://localhost:8000/health

# API root
curl http://localhost:8000/api/v1/

# OAuth authorization URL
curl http://localhost:8000/api/v1/integrations/hubspot/authorize
```

---

## Test 2: Database Connection

### Check Tables Exist

```bash
cd backend
poetry run python -c "
from src.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = \'public\'
        ORDER BY table_name
    '''))
    tables = [row[0] for row in result]
    print('Tables:', ', '.join(tables))
"
```

**Expected Output:**
```
Tables: alembic_version, churn_risk_cards, churn_risk_comments, companies, contacts, integrations, tenants, ticket_topic_assignments, ticket_topics, tickets, users
```

### Run Database Tests

```bash
cd backend
poetry run pytest tests/unit/test_models.py -v
```

**Expected:** All model tests passing

---

## Test 3: OpenRouter AI Service

### Using the Smoke Test Script

```bash
cd backend
poetry run python scripts/smoke_test.py
```

**Expected Output:**
```
🗄️  Testing Database Connection...
✅ Connected to PostgreSQL

🔍 Testing HubSpot Integration...
OAuth configured: Client ID abc123...
⚠️  OAuth requires user authorization flow

🤖 Testing OpenRouter AI Integration...
✅ Analysis complete!

  Sentiment: negative
  Confidence: 85.00%
  Reasoning: Customer expresses frustration...
  Topics: 3 found

    - Inventory Management (confidence: 90.00%)
    - System Performance (confidence: 85.00%)
    - Customer Urgency (confidence: 80.00%)

📊 SUMMARY
Database:   ✅ PASS
HubSpot:    ⏳ SKIPPED (requires OAuth)
OpenRouter: ✅ PASS
```

### Test with Custom Ticket Content

Create a test file:

```python
# test_ai_manual.py
import asyncio
from src.services.openrouter import OpenRouterAnalyzer

async def test():
    analyzer = OpenRouterAnalyzer()

    ticket_content = """
    Subject: Can't access my account
    Content: I've been trying to log in for 2 hours. I need access NOW.
    This is completely unacceptable. I'm losing money every minute.
    """

    result = await analyzer.analyze_ticket(
        ticket_content=ticket_content,
        available_topics=[],
        training_rules=[]
    )

    print(f"Sentiment: {result.sentiment.sentiment.value}")
    print(f"Confidence: {result.sentiment.confidence:.2%}")
    print(f"Reasoning: {result.sentiment.reasoning}")
    print(f"\nTopics detected: {len(result.topics)}")
    for topic in result.topics:
        print(f"  - {topic.topic_name} ({topic.confidence:.2%})")

asyncio.run(test())
```

Run it:
```bash
poetry run python test_ai_manual.py
```

---

## Test 4: HubSpot OAuth Flow (End-to-End)

### Complete OAuth Flow

1. **Start both servers** (backend on 8000, frontend on 3000)

2. **Navigate to test page**: http://localhost:3000

3. **Click "Get OAuth Authorization URL"**
   - Should return URL with your Client ID

4. **Click "Open HubSpot Authorization →"**
   - Opens new tab to HubSpot
   - Log in with FlxPoint account
   - Click "Authorize"

5. **Verify Redirect**
   - Should redirect to: `http://localhost:8000/api/v1/integrations/hubspot/callback?code=...`
   - Backend should exchange code for tokens
   - Should return integration details (or 401 if no auth yet)

**Note:** OAuth callback currently requires Firebase authentication. To test fully, you'll need:
- Firebase user created
- JWT token in request
- See Task 9 in implementation plan for frontend auth setup

---

## Test 5: Unit & Integration Tests

### Run All Tests

```bash
cd backend
poetry run pytest
```

**Expected:** 23/23 tests passing

### Run Specific Test Files

```bash
# Auth tests
poetry run pytest tests/unit/test_auth.py -v

# Dependency tests
poetry run pytest tests/unit/test_dependencies.py -v

# Model tests
poetry run pytest tests/unit/test_models.py -v

# OpenRouter tests
poetry run pytest tests/unit/test_openrouter.py -v

# HubSpot tests
poetry run pytest tests/integration/test_hubspot.py -v
```

---

## Test 6: Frontend Build & TypeScript

### Check for Type Errors

```bash
cd frontend
npm run typecheck
```

**Expected:** No type errors (tsconfig.json now exists)

### Build for Production

```bash
npm run build
```

**Expected:** Clean build with no errors

---

## Common Issues & Fixes

### Issue: "Cannot connect to database"

**Fix:**
```bash
# Check docker-compose is running
docker-compose ps

# Restart if needed
docker-compose down
docker-compose up -d

# Check connection string in .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev
```

### Issue: "OpenRouter API error"

**Fix:**
- Verify `OPENROUTER_API_KEY` in `.env`
- Check API key is valid: https://openrouter.ai/keys
- Check rate limits: https://openrouter.ai/account

### Issue: "HubSpot OAuth returns 401"

**Expected** - OAuth requires authenticated user (Firebase JWT).

**To fully test:**
1. Create Firebase user first
2. Get JWT token
3. Include in request: `Authorization: Bearer <jwt>`

**For now:** OAuth URL generation working is sufficient validation.

### Issue: "CORS error in browser"

**Fix:**
- Check `CORS_ORIGINS` in `.env` includes `http://localhost:3000`
- Restart backend after changing `.env`

### Issue: "Frontend shows blank page"

**Fix:**
```bash
# Check for JS errors in browser console
# Clear Nuxt cache
rm -rf frontend/.nuxt
cd frontend && npm run dev
```

---

## Success Criteria

Before continuing to Task 6, verify:

- ✅ Backend health endpoint responding
- ✅ Database connection working
- ✅ All 11 tables created
- ✅ OpenRouter AI analyzing tickets correctly
- ✅ Sentiment analysis returning 5-level scores with confidence
- ✅ Topic extraction working (even without configured topics)
- ✅ HubSpot OAuth URL generation working
- ✅ Frontend test page displaying correctly
- ✅ Frontend can call backend APIs (CORS working)
- ✅ 23/23 tests passing
- ✅ No TypeScript errors in frontend

---

## Next Steps

Once all tests pass, you're ready to proceed with:
- **Task 6:** Ticket Import & Analysis Service
- **Task 7:** Churn Risk Card Creation Logic
- **Task 8:** WebSocket Real-Time Updates

See: `docs/plans/2025-11-06-phase-1-mvp-implementation.md`

---

**Last Tested:** 2025-11-08
**Test Environment:** macOS, Docker Desktop, Python 3.12, Node.js 18+

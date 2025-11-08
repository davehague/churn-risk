#!/usr/bin/env python3
"""
Smoke test script to verify HubSpot and OpenRouter integrations.
Run with: poetry run python scripts/smoke_test.py
"""
import asyncio
from src.core.config import settings
from src.integrations.hubspot import HubSpotClient
from src.services.openrouter import OpenRouterAnalyzer


async def test_hubspot():
    """Test HubSpot OAuth configuration."""
    print("\n🔍 Testing HubSpot Integration...")

    if not (settings.HUBSPOT_CLIENT_ID and settings.HUBSPOT_CLIENT_SECRET):
        print("❌ HubSpot OAuth not configured in .env")
        print("   Required: HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, HUBSPOT_REDIRECT_URI")
        return None

    print(f"✅ OAuth configured: Client ID {settings.HUBSPOT_CLIENT_ID[:10]}...")
    print("⚠️  OAuth requires user authorization flow (can't test automatically)")
    print("\n   To complete OAuth and fetch real tickets:")
    print("   1. Start backend: poetry run uvicorn src.main:app --port 8000")
    print("   2. Start frontend: cd frontend && npm run dev")
    print("   3. Visit: http://localhost:3000")
    print("   4. Click 'Get OAuth Authorization URL'")
    print("   5. Click the link to authorize in HubSpot")
    print("   6. After authorization, you'll have access tokens to fetch tickets")
    print("\n   Once authorized, update this test to use real access tokens.")

    return None


async def test_openrouter(sample_ticket=None):
    """Test OpenRouter AI analysis."""
    print("\n🤖 Testing OpenRouter AI Integration...")
    print(f"Using API Key: {settings.OPENROUTER_API_KEY[:10]}..." if settings.OPENROUTER_API_KEY else "No API key found")

    if not settings.OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not found in .env")
        return False

    # Use sample ticket or create test content
    if sample_ticket:
        properties = sample_ticket.get('properties', {})
        ticket_content = f"""
Subject: {properties.get('subject', 'Test ticket')}
Content: {properties.get('content', 'This is a test ticket to verify AI analysis.')}
        """.strip()
    else:
        ticket_content = """
Subject: Cannot sync inventory data
Content: We've been trying to sync our inventory for the past 3 hours and it keeps failing.
This is extremely frustrating as we have orders backing up. Please help ASAP!
        """.strip()

    try:
        analyzer = OpenRouterAnalyzer()

        print(f"\nAnalyzing ticket content...")
        print(f"Content preview: {ticket_content[:100]}...")

        # Test sentiment analysis only (no topics yet)
        print("\nRunning sentiment analysis...")
        result = await analyzer.analyze_ticket(
            ticket_content=ticket_content,
            available_topics=[],  # No topics configured yet
            training_rules=[]
        )

        print(f"✅ Analysis complete!")
        print(f"\nResults:")
        print(f"  Sentiment: {result.sentiment.sentiment.value}")
        print(f"  Confidence: {result.sentiment.confidence:.2%}")
        if result.sentiment.reasoning:
            print(f"  Reasoning: {result.sentiment.reasoning}")
        print(f"  Topics: {len(result.topics)} found")

        if result.topics:
            print(f"\n  Detected topics:")
            for topic in result.topics:
                print(f"    - {topic.topic_name} (confidence: {topic.confidence:.2%})")

        return True

    except Exception as e:
        print(f"❌ OpenRouter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database():
    """Test database connection."""
    print("\n🗄️  Testing Database Connection...")
    print(f"Database URL: {settings.DATABASE_URL}")

    try:
        from src.core.database import engine
        from sqlalchemy import text

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL")
            print(f"  Version: {version.split(',')[0]}")

            # Check tables exist
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"  Tables: {len(tables)} found")
            for table in tables:
                print(f"    - {table}")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("🚀 SMOKE TEST - Churn Risk App")
    print("=" * 60)

    # Test database
    db_ok = await test_database()

    # Test HubSpot
    sample_ticket = await test_hubspot()
    hubspot_ok = sample_ticket is not None

    # Test OpenRouter (with real ticket if available)
    openrouter_ok = await test_openrouter(sample_ticket)

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Database:   {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"HubSpot:    {'✅ CONFIGURED' if hubspot_ok is None else '❌ NOT CONFIGURED'}")
    print(f"OpenRouter: {'✅ PASS' if openrouter_ok else '❌ FAIL'}")

    all_critical_pass = db_ok and openrouter_ok
    print(f"\nOverall:    {'✅ CORE SYSTEMS WORKING' if all_critical_pass else '⚠️  SOME TESTS FAILED'}")
    print("Note: HubSpot requires OAuth flow completion (see instructions above)")
    print("=" * 60)

    return all_critical_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

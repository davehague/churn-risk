#!/usr/bin/env python3
"""
Script to fetch tickets from HubSpot and analyze sentiment using AI.

This script will:
1. Guide you through OAuth flow if needed
2. Fetch 20 tickets from HubSpot
3. Analyze sentiment using Google Gemini Flash via OpenRouter
4. Display results
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.models.integration import Integration, IntegrationType, IntegrationStatus
from src.integrations.hubspot import HubSpotClient
from src.services.openrouter import OpenRouterAnalyzer
import webbrowser


async def get_or_create_integration(db, oauth_code=None):
    """Get existing HubSpot integration or guide user through OAuth."""
    integration = db.query(Integration).filter(
        Integration.type == IntegrationType.HUBSPOT
    ).first()

    if integration and integration.credentials and "access_token" in integration.credentials:
        print(f"✓ Found existing HubSpot integration (ID: {integration.id})")
        print(f"  Status: {integration.status}")
        return integration

    print("\n" + "="*70)
    print("  HubSpot OAuth Setup Required")
    print("="*70)
    print("\nNo HubSpot integration found. You need to complete OAuth flow.")

    # Generate OAuth URL
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={settings.HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={settings.HUBSPOT_REDIRECT_URI}"
        f"&scope=crm.objects.contacts.read crm.objects.companies.read tickets"
    )

    if not oauth_code:
        print("\nSteps:")
        print("1. Visit the authorization URL below")
        print("2. Authorize the app in your browser")
        print("3. HubSpot will redirect to a URL with a 'code' parameter")
        print("4. Run this script again with: python scripts/fetch_and_analyze_tickets.py YOUR_CODE")

        print(f"\n📋 Authorization URL:")
        print(f"   {auth_url}")
        print(f"\n🌐 Opening in browser...")

        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"   Could not open browser: {e}")
            print(f"   Please open the URL manually")

        print(f"\n⏳ After authorizing, you'll be redirected to:")
        print(f"   {settings.HUBSPOT_REDIRECT_URI}?code=XXXXX")
        print(f"\n   The page may show an error (that's OK - we just need the code)")
        print(f"\n📝 Copy the 'code' parameter and run:")
        print(f"   poetry run python scripts/fetch_and_analyze_tickets.py YOUR_CODE")
        sys.exit(0)

    code = oauth_code

    if not code:
        print("❌ No code provided. Exiting.")
        sys.exit(1)

    print("\n🔄 Exchanging code for access token...")

    try:
        token_data = await HubSpotClient.exchange_code_for_token(
            code=code,
            redirect_uri=settings.HUBSPOT_REDIRECT_URI
        )

        print("✓ Successfully obtained access token")

        # Create a temporary tenant for testing (you can change this)
        # In a real app, this would be associated with the logged-in user's tenant
        from src.models.tenant import Tenant

        # Check if we have any tenant
        tenant = db.query(Tenant).first()
        if not tenant:
            print("\n⚠️  No tenant found in database. Creating a test tenant...")
            from src.models.tenant import PlanTier
            tenant = Tenant(
                name="Test Company",
                subdomain="test",
                plan_tier=PlanTier.STARTER
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"✓ Created test tenant (ID: {tenant.id})")

        # Save integration
        integration = Integration(
            tenant_id=tenant.id,
            type=IntegrationType.HUBSPOT,
            status=IntegrationStatus.ACTIVE,
            credentials=token_data
        )
        db.add(integration)
        db.commit()
        db.refresh(integration)

        print(f"✓ Saved integration to database (ID: {integration.id})")

        return integration

    except Exception as e:
        print(f"❌ Error exchanging code: {e}")
        sys.exit(1)


async def fetch_tickets(integration, limit=20):
    """Fetch tickets from HubSpot."""
    access_token = integration.credentials.get("access_token")

    print(f"\n📥 Fetching {limit} tickets from HubSpot...")

    client = HubSpotClient(access_token=access_token)

    try:
        response = await client.get_tickets(limit=limit)
        tickets = response.get("results", [])

        print(f"✓ Fetched {len(tickets)} tickets")

        return tickets

    except Exception as e:
        print(f"❌ Error fetching tickets: {e}")

        # Check if it's an auth error
        if "401" in str(e) or "403" in str(e):
            print("\n⚠️  Authentication failed. Token may have expired.")
            print("   Trying to refresh token...")

            refresh_token = integration.credentials.get("refresh_token")
            if refresh_token:
                try:
                    new_token_data = await HubSpotClient.refresh_access_token(refresh_token)
                    integration.credentials = new_token_data

                    # Save to database
                    from sqlalchemy.orm import Session
                    db = Session.object_session(integration)
                    db.commit()

                    print("✓ Token refreshed successfully. Retrying...")

                    # Retry with new token
                    client = HubSpotClient(access_token=new_token_data["access_token"])
                    response = await client.get_tickets(limit=limit)
                    tickets = response.get("results", [])

                    print(f"✓ Fetched {len(tickets)} tickets")
                    return tickets

                except Exception as refresh_error:
                    print(f"❌ Token refresh failed: {refresh_error}")
                    sys.exit(1)
            else:
                print("❌ No refresh token available. Please re-authorize.")
                sys.exit(1)
        else:
            sys.exit(1)


async def analyze_tickets(tickets):
    """Analyze sentiment for each ticket using Gemini Flash."""
    print(f"\n🤖 Analyzing sentiment with AI...")
    print(f"   Model: {settings.OPENROUTER_MODEL}")

    # Initialize analyzer (uses model from settings)
    analyzer = OpenRouterAnalyzer()

    results = []

    for i, ticket in enumerate(tickets, 1):
        ticket_id = ticket.get("id")
        properties = ticket.get("properties", {})
        subject = properties.get("subject", "No subject")
        content = properties.get("content", "")

        # Combine subject and content for analysis
        full_text = f"{subject}\n\n{content}" if content else subject

        print(f"\n[{i}/{len(tickets)}] Analyzing ticket {ticket_id}...")
        print(f"   Subject: {subject[:60]}{'...' if len(subject) > 60 else ''}")

        try:
            # Analyze (no topics, just sentiment)
            analysis = await analyzer.analyze_ticket(
                ticket_content=full_text,
                available_topics=None
            )

            sentiment = analysis.sentiment.sentiment.value
            confidence = analysis.sentiment.confidence
            is_negative = sentiment in ["negative", "very_negative"]

            print(f"   Sentiment: {sentiment.upper()} (confidence: {confidence:.2f})")
            if is_negative:
                print(f"   ⚠️  NEGATIVE - potential churn risk")

            results.append({
                "ticket_id": ticket_id,
                "subject": subject,
                "sentiment": sentiment,
                "confidence": confidence,
                "is_negative": is_negative,
                "reasoning": analysis.sentiment.reasoning,
                "topics": [t.topic_name for t in analysis.topics]
            })

        except Exception as e:
            print(f"   ❌ Error analyzing ticket: {e}")
            results.append({
                "ticket_id": ticket_id,
                "subject": subject,
                "sentiment": "error",
                "confidence": 0.0,
                "is_negative": False,
                "error": str(e)
            })

    return results


def display_summary(results):
    """Display summary of analysis results."""
    print("\n" + "="*70)
    print("  Analysis Summary")
    print("="*70)

    total = len(results)
    negative_count = sum(1 for r in results if r.get("is_negative", False))
    error_count = sum(1 for r in results if r.get("sentiment") == "error")

    print(f"\nTotal tickets analyzed: {total}")
    print(f"Negative/Very Negative: {negative_count} ({negative_count/total*100:.1f}%)")
    print(f"Errors: {error_count}")

    if negative_count > 0:
        print(f"\n⚠️  Negative Tickets (Potential Churn Risk):")
        print("-" * 70)

        for r in results:
            if r.get("is_negative", False):
                print(f"\n• Ticket ID: {r['ticket_id']}")
                print(f"  Subject: {r['subject']}")
                print(f"  Sentiment: {r['sentiment'].upper()} (confidence: {r['confidence']:.2f})")
                if r.get("reasoning"):
                    print(f"  Reasoning: {r['reasoning']}")
                if r.get("topics"):
                    print(f"  Topics: {', '.join(r['topics'])}")

    print("\n" + "="*70)


async def main():
    """Main script execution."""
    print("="*70)
    print("  HubSpot Ticket Sentiment Analysis")
    print("="*70)

    # Check if OAuth code was provided as command-line argument
    oauth_code = None
    if len(sys.argv) > 1:
        oauth_code = sys.argv[1]
        print(f"\n✓ Using OAuth code from command line")

    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Step 1: Get or create integration
        integration = await get_or_create_integration(db, oauth_code)

        # Step 2: Fetch tickets
        tickets = await fetch_tickets(integration, limit=20)

        if not tickets:
            print("⚠️  No tickets found")
            return

        # Step 3: Analyze tickets
        results = await analyze_tickets(tickets)

        # Step 4: Display summary
        display_summary(results)

        print("\n✅ Done!")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

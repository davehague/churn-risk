#!/usr/bin/env python3
"""
Script to fetch tickets from HubSpot using a Private App access token and analyze sentiment.

This script bypasses OAuth and uses a simpler Private App token.

Setup:
1. Go to HubSpot Settings → Integrations → Private Apps
2. Create a new Private App with these scopes:
   - crm.objects.contacts.read
   - crm.objects.companies.read
   - tickets
3. Copy the access token
4. Run: poetry run python scripts/fetch_tickets_private_app.py YOUR_ACCESS_TOKEN
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.integrations.hubspot import HubSpotClient
from src.services.openrouter import OpenRouterAnalyzer
from src.core.config import settings


async def fetch_tickets(access_token, limit=20):
    """Fetch tickets from HubSpot."""
    print(f"\n📥 Fetching {limit} tickets from HubSpot...")

    client = HubSpotClient(access_token=access_token)

    try:
        response = await client.get_tickets(limit=limit)
        tickets = response.get("results", [])

        print(f"✓ Fetched {len(tickets)} tickets")

        return tickets

    except Exception as e:
        print(f"❌ Error fetching tickets: {e}")

        if "401" in str(e) or "403" in str(e):
            print("\n⚠️  Authentication failed. Please check:")
            print("   1. Your access token is correct")
            print("   2. The Private App has the required scopes:")
            print("      - crm.objects.contacts.read")
            print("      - crm.objects.companies.read")
            print("      - tickets")

        raise


async def analyze_tickets(tickets):
    """Analyze sentiment for each ticket using AI."""
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
    print("\n💡 Tip: Save this access token to use OAuth later:")
    print("   You can store it in the database as an Integration record")


async def main():
    """Main script execution."""
    print("="*70)
    print("  HubSpot Ticket Sentiment Analysis (Private App)")
    print("="*70)

    # Check if access token was provided
    if len(sys.argv) < 2:
        print("\n❌ Error: No access token provided")
        print("\nUsage:")
        print("   poetry run python scripts/fetch_tickets_private_app.py YOUR_ACCESS_TOKEN")
        print("\nTo get an access token:")
        print("   1. Go to HubSpot Settings → Integrations → Private Apps")
        print("   2. Create a new Private App")
        print("   3. Grant these scopes:")
        print("      - crm.objects.contacts.read")
        print("      - crm.objects.companies.read")
        print("      - tickets")
        print("   4. Copy the access token")
        sys.exit(1)

    access_token = sys.argv[1]

    try:
        # Step 1: Fetch tickets
        tickets = await fetch_tickets(access_token, limit=20)

        if not tickets:
            print("⚠️  No tickets found")
            return

        # Step 2: Analyze tickets
        results = await analyze_tickets(tickets)

        # Step 3: Display summary
        display_summary(results)

        print("\n✅ Done!")

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

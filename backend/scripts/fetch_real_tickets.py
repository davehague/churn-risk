#!/usr/bin/env python3
"""Fetch and analyze real HubSpot tickets from the connected integration."""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.models.integration import Integration, IntegrationType
from src.integrations.hubspot import HubSpotClient
from src.services.openrouter import OpenRouterAnalyzer


async def main():
    print("="*70)
    print("  FlxPoint Ticket Sentiment Analysis")
    print("="*70)

    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Get the HubSpot integration
        integration = db.query(Integration).filter(
            Integration.type == IntegrationType.HUBSPOT
        ).first()

        if not integration:
            print("❌ No HubSpot integration found. Run OAuth flow first.")
            return

        print(f"\n✓ Found HubSpot integration (ID: {integration.id})")
        print(f"  Status: {integration.status}")
        
        access_token = integration.credentials.get("access_token")
        
        # Fetch tickets
        print(f"\n📥 Fetching tickets from FlxPoint HubSpot...")
        client = HubSpotClient(access_token=access_token)
        
        response = await client.get_tickets(limit=20)
        tickets = response.get("results", [])
        
        print(f"✓ Fetched {len(tickets)} tickets")
        
        if not tickets:
            print("\n⚠️  No tickets found in FlxPoint HubSpot account")
            return
        
        # Analyze with AI
        print(f"\n🤖 Analyzing sentiment with {settings.OPENROUTER_MODEL}...")
        analyzer = OpenRouterAnalyzer()
        
        results = []
        
        for i, ticket in enumerate(tickets, 1):
            ticket_id = ticket.get("id")
            properties = ticket.get("properties", {})
            subject = properties.get("subject", "No subject")
            content = properties.get("content", "")
            
            full_text = f"{subject}\n\n{content}" if content else subject
            
            print(f"\n[{i}/{len(tickets)}] {subject[:50]}...")

            try:
                analysis = await analyzer.analyze_ticket(full_text, available_topics=None)
                
                sentiment = analysis.sentiment.sentiment.value
                confidence = analysis.sentiment.confidence
                is_negative = sentiment in ["negative", "very_negative"]
                
                print(f"   → {sentiment.upper()} ({confidence:.0%} confidence)")
                
                if is_negative:
                    print(f"   ⚠️  CHURN RISK")
                
                results.append({
                    "ticket_id": ticket_id,
                    "subject": subject,
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "is_negative": is_negative,
                    "reasoning": analysis.sentiment.reasoning
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Summary
        print("\n" + "="*70)
        print("  Summary")
        print("="*70)
        
        total = len(results)
        negative_count = sum(1 for r in results if r["is_negative"])
        
        print(f"\nTotal tickets analyzed: {total}")
        print(f"Churn risk tickets: {negative_count} ({negative_count/total*100:.1f}%)")
        
        if negative_count > 0:
            print(f"\n⚠️  Tickets flagged as churn risk:")
            print("-" * 70)
            
            for r in results:
                if r["is_negative"]:
                    print(f"\n• Ticket {r['ticket_id']}")
                    print(f"  {r['subject'][:60]}")
                    print(f"  Sentiment: {r['sentiment'].upper()} ({r['confidence']:.0%})")
                    if r.get("reasoning"):
                        print(f"  Reasoning: {r['reasoning'][:100]}...")
        
        print("\n" + "="*70)
        print("\n✅ Done!")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

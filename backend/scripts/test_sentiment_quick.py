#!/usr/bin/env python3
"""Quick sentiment analysis test with 5 sample tickets."""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.openrouter import OpenRouterAnalyzer
from src.core.config import settings

# Just 5 diverse sample tickets
SAMPLE_TICKETS = [
    {
        "id": "001",
        "subject": "Urgent: API keeps returning 500 errors - losing customers!",
        "content": "This is the third time this week. We're losing sales and customers are furious. Completely unacceptable."
    },
    {
        "id": "002",
        "subject": "Thank you for the quick fix!",
        "content": "Thanks to the support team for fixing that billing issue so quickly. Really appreciate it!"
    },
    {
        "id": "003",
        "subject": "Question about webhook configuration",
        "content": "Hi, I'm trying to set up webhooks. Followed the docs but not seeing events. Could you help?"
    },
    {
        "id": "004",
        "subject": "Ready to cancel - too many issues",
        "content": "We've been patient but this is ridiculous. Authentication breaking, slow responses, missing features. Moving to competitor unless things improve."
    },
    {
        "id": "005",
        "subject": "Great webinar yesterday!",
        "content": "Really enjoyed the webinar on best practices. Learned a lot and already implemented some tips!"
    }
]

async def main():
    print("="*70)
    print("  Quick Sentiment Analysis Test (5 Tickets)")
    print("="*70)
    print(f"Model: {settings.OPENROUTER_MODEL}\n")

    # Initialize analyzer (uses model from settings)
    analyzer = OpenRouterAnalyzer()
    
    results = []
    
    for i, ticket in enumerate(SAMPLE_TICKETS, 1):
        if i > 1:
            await asyncio.sleep(3)  # 3 second delay between requests
            
        print(f"\n[{i}/5] {ticket['subject'][:50]}...")
        
        try:
            analysis = await analyzer.analyze_ticket(
                ticket_content=f"{ticket['subject']}\n\n{ticket['content']}",
                available_topics=None
            )
            
            sentiment = analysis.sentiment.sentiment.value
            confidence = analysis.sentiment.confidence
            is_negative = sentiment in ["negative", "very_negative"]
            
            print(f"   → {sentiment.upper()} (confidence: {confidence:.2f})")
            if is_negative:
                print(f"   ⚠️  CHURN RISK")
            
            results.append({
                "id": ticket["id"],
                "subject": ticket["subject"],
                "sentiment": sentiment,
                "confidence": confidence,
                "is_negative": is_negative
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({"id": ticket["id"], "sentiment": "error"})
    
    # Summary
    print("\n" + "="*70)
    print("  Summary")
    print("="*70)
    
    successful = [r for r in results if r["sentiment"] != "error"]
    negative = [r for r in successful if r.get("is_negative", False)]
    
    print(f"\nAnalyzed: {len(successful)}/{len(SAMPLE_TICKETS)} tickets")
    print(f"Churn Risk: {len(negative)} tickets")
    
    if negative:
        print("\n⚠️  Tickets flagged as churn risk:")
        for r in negative:
            print(f"   • {r['id']}: {r['subject'][:50]}")
            print(f"     {r['sentiment'].upper()} ({r['confidence']:.0%} confidence)")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(main())

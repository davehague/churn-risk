#!/usr/bin/env python3
"""
Script to test sentiment analysis using mock ticket data.

This demonstrates the sentiment analysis functionality without requiring HubSpot access.
Uses Google Gemini Flash via OpenRouter to analyze ticket sentiment.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.openrouter import OpenRouterAnalyzer
from src.core.config import settings


# Sample ticket data (realistic support ticket scenarios)
SAMPLE_TICKETS = [
    {
        "id": "mock-001",
        "subject": "Urgent: API keeps returning 500 errors - losing customers!",
        "content": "This is the third time this week our integration has gone down. We're losing sales and our customers are furious. This is completely unacceptable. We need this fixed IMMEDIATELY or we'll have to consider other options."
    },
    {
        "id": "mock-002",
        "subject": "Thank you for the quick fix!",
        "content": "Just wanted to say thanks to the support team for fixing that billing issue so quickly. Really appreciate the fast response and clear communication. Great service!"
    },
    {
        "id": "mock-003",
        "subject": "Question about webhook configuration",
        "content": "Hi, I'm trying to set up webhooks for our new integration. I've followed the docs but I'm not seeing events come through. Could you help me understand what I might be missing? Thanks!"
    },
    {
        "id": "mock-004",
        "subject": "Performance has been terrible lately",
        "content": "We've noticed significant slowdowns over the past two weeks. API response times have gone from ~200ms to 3-5 seconds. This is impacting our users' experience. Very disappointed with the recent degradation in service quality."
    },
    {
        "id": "mock-005",
        "subject": "Feature request: Bulk export",
        "content": "Would be great if we could export all our data in bulk. Right now we have to paginate through everything which is slow. Not urgent but would be a nice quality of life improvement."
    },
    {
        "id": "mock-006",
        "subject": "CRITICAL: Data sync failed - missing records",
        "content": "We just discovered that yesterday's data sync failed silently and we're missing hundreds of records. This is a major problem for our reporting. How could this happen without any notification? We need those records recovered ASAP and better monitoring in place."
    },
    {
        "id": "mock-007",
        "subject": "Great webinar yesterday!",
        "content": "Really enjoyed the webinar on best practices. Learned a lot and already implemented some of the tips. Looking forward to the next one!"
    },
    {
        "id": "mock-008",
        "subject": "Help with rate limiting",
        "content": "We're hitting rate limits more frequently now that our usage has grown. Can you explain the limits and whether there are options to increase them? Thanks for the help."
    },
    {
        "id": "mock-009",
        "subject": "Ready to cancel - too many issues",
        "content": "We've been patient but this is getting ridiculous. Authentication breaking every other week, slow response times, missing features you promised six months ago. Our team has lost confidence. Unless things improve dramatically in the next week, we're moving to a competitor."
    },
    {
        "id": "mock-010",
        "subject": "Documentation clarification",
        "content": "The docs for the new analytics endpoint are a bit unclear about the date format. Should it be ISO 8601? Could you clarify? Otherwise everything is working great."
    },
    {
        "id": "mock-011",
        "subject": "Frustrated with support response times",
        "content": "We've been waiting 5 days for a response to our high-priority ticket. This is not acceptable for a paid enterprise plan. Our engineers are blocked and we're falling behind schedule."
    },
    {
        "id": "mock-012",
        "subject": "Love the new dashboard!",
        "content": "The new analytics dashboard is fantastic! So much easier to see our metrics at a glance. Great work on the UI improvements. Keep it up!"
    },
    {
        "id": "mock-013",
        "subject": "Migration assistance needed",
        "content": "We're planning to migrate from v1 to v2 API. Do you have any migration guides or best practices? Happy to schedule a call to discuss if that helps."
    },
    {
        "id": "mock-014",
        "subject": "Another outage?! This is unacceptable",
        "content": "Third outage this month. Our SLA says 99.9% uptime but we're nowhere near that. Customers are asking why they should keep using us when our infrastructure is this unreliable. Need answers."
    },
    {
        "id": "mock-015",
        "subject": "Feature working perfectly - thanks!",
        "content": "Just wanted to confirm that the CSV import feature is working exactly as we needed. Your team did a great job implementing our feedback. Much appreciated!"
    },
    {
        "id": "mock-016",
        "subject": "Webhook payloads missing fields",
        "content": "We're receiving webhook events but several documented fields are missing from the payload. This is breaking our integration. Is this a known issue?"
    },
    {
        "id": "mock-017",
        "subject": "Billing discrepancy",
        "content": "Our invoice shows charges that don't match our usage. We were billed for 1M API calls but our logs show only 750K. Please review and correct."
    },
    {
        "id": "mock-018",
        "subject": "Excellent customer support!",
        "content": "Sarah from your support team went above and beyond to help us troubleshoot our integration issue. She was patient, knowledgeable, and found the solution quickly. Please pass along our thanks!"
    },
    {
        "id": "mock-019",
        "subject": "Connection timeouts increasing",
        "content": "We're seeing more and more connection timeouts when calling your API. Started about a week ago. Error rate went from <0.1% to almost 5%. What's going on?"
    },
    {
        "id": "mock-020",
        "subject": "Quick question about pricing tiers",
        "content": "We're growing and might need to upgrade our plan soon. Could you send info about the enterprise tier pricing and features? Thanks!"
    }
]


async def analyze_tickets(tickets):
    """Analyze sentiment for each ticket using AI."""
    print(f"\n🤖 Analyzing {len(tickets)} sample tickets with AI...")
    print(f"   Model: {settings.OPENROUTER_MODEL}")
    print(f"   Provider: OpenRouter")
    print(f"   Note: Adding 2-second delays between requests to avoid rate limits")

    # Initialize analyzer (uses model from settings)
    analyzer = OpenRouterAnalyzer()

    results = []

    for i, ticket in enumerate(tickets, 1):
        # Add delay to avoid rate limiting (except for first ticket)
        if i > 1:
            await asyncio.sleep(2)
        ticket_id = ticket.get("id")
        subject = ticket.get("subject")
        content = ticket.get("content", "")

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

    # Count by sentiment
    sentiment_counts = {}
    for r in results:
        sentiment = r.get("sentiment", "error")
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    print(f"\nTotal tickets analyzed: {total}")
    print(f"\nSentiment Breakdown:")
    for sentiment, count in sorted(sentiment_counts.items()):
        pct = count / total * 100
        print(f"  {sentiment.upper():15} {count:3} ({pct:5.1f}%)")

    print(f"\n⚠️  Churn Risk Indicators:")
    print(f"  Negative/Very Negative: {negative_count} tickets ({negative_count/total*100:.1f}%)")
    if error_count > 0:
        print(f"  Errors: {error_count}")

    if negative_count > 0:
        print(f"\n" + "="*70)
        print(f"  Negative Tickets (Potential Churn Risk)")
        print("="*70)

        for r in results:
            if r.get("is_negative", False):
                print(f"\n📌 Ticket {r['ticket_id']}")
                print(f"   Subject: {r['subject']}")
                print(f"   Sentiment: {r['sentiment'].upper()} (confidence: {r['confidence']:.2f})")
                if r.get("reasoning"):
                    print(f"   Reasoning: {r['reasoning']}")
                if r.get("topics"):
                    print(f"   Topics: {', '.join(r['topics'])}")

    print("\n" + "="*70)
    print("\n💡 Next Steps:")
    print("   1. These tickets would trigger churn risk cards in production")
    print("   2. Each negative ticket would create a card in the kanban board")
    print("   3. Cards would be assigned to CSM team for follow-up")
    print("\n   When HubSpot access is available, this same analysis will run on real tickets!")


async def main():
    """Main script execution."""
    print("="*70)
    print("  Sentiment Analysis Test (Mock Ticket Data)")
    print("="*70)
    print("\nThis script demonstrates the AI sentiment analysis functionality")
    print("using sample ticket data. No HubSpot access required!")

    try:
        # Analyze sample tickets
        results = await analyze_tickets(SAMPLE_TICKETS)

        # Display summary
        display_summary(results)

        print("\n✅ Test complete!")
        print("\n📊 Performance:")
        print(f"   Analyzed {len(SAMPLE_TICKETS)} tickets successfully")
        print(f"   Using: Google Gemini 2.0 Flash (free tier)")
        print(f"   Via: OpenRouter API")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

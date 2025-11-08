#!/usr/bin/env python3
"""Debug script to test the model configuration."""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.openrouter import OpenRouterAnalyzer
from src.core.config import settings

async def main():
    print(f"Testing OpenRouter configuration:")
    print(f"  API Key: {settings.OPENROUTER_API_KEY[:20]}...")
    print(f"  Model: {settings.OPENROUTER_MODEL}")
    
    analyzer = OpenRouterAnalyzer()
    
    print(f"\nAnalyzer initialized:")
    print(f"  Model: {analyzer.model}")
    print(f"  API Key set: {bool(analyzer.api_key)}")
    
    test_text = "This is a test ticket. Everything is working great!"
    
    print(f"\nTesting analysis...")
    try:
        result = await analyzer.analyze_ticket(test_text, available_topics=None)
        print(f"✅ Success!")
        print(f"   Sentiment: {result.sentiment.sentiment.value}")
        print(f"   Confidence: {result.sentiment.confidence}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

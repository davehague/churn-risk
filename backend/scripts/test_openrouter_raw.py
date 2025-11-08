#!/usr/bin/env python3
"""Test raw OpenRouter API response."""

import asyncio
import httpx
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.core.config import settings

async def main():
    print(f"Testing OpenRouter API directly...")
    print(f"Model: {settings.OPENROUTER_MODEL}\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello"}
                ],
                "response_format": {"type": "json_object"}
            },
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"\nResponse body:")
        print(response.text)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                print(f"\nMessage content:")
                print(content)

if __name__ == "__main__":
    asyncio.run(main())

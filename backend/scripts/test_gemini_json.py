#!/usr/bin/env python3
"""Test Gemini JSON mode."""

import asyncio
import httpx
import json
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.core.config import settings

async def test_with_format_constraint():
    print("Test 1: WITH json_object format constraint")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": "You are an expert at analyzing text."},
                    {"role": "user", "content": 'Analyze sentiment of: "This is terrible!" Return JSON: {"sentiment": "negative", "confidence": 0.9}'}
                ],
                "response_format": {"type": "json_object"}
            },
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"Raw content: {content}")
            try:
                parsed = json.loads(content)
                print(f"Parsed successfully: {parsed}")
            except:
                print("❌ Failed to parse as JSON")

async def test_without_format_constraint():
    print("\nTest 2: WITHOUT json_object format constraint")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": "You are an expert at analyzing text."},
                    {"role": "user", "content": 'Analyze sentiment of: "This is terrible!" Return ONLY valid JSON: {"sentiment": "negative", "confidence": 0.9}'}
                ]
            },
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"Raw content: {content}")
            try:
                parsed = json.loads(content)
                print(f"✅ Parsed successfully: {parsed}")
            except Exception as e:
                print(f"❌ Failed to parse: {e}")

async def main():
    await test_with_format_constraint()
    await asyncio.sleep(2)
    await test_without_format_constraint()

if __name__ == "__main__":
    asyncio.run(main())

import httpx
import json
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from src.services.ai_base import TicketAnalyzer
from src.schemas.ai import SentimentAnalysisResult, TopicClassification, TicketAnalysisResult
from src.models.ticket import SentimentScore
from src.core.config import settings


class OpenRouterAnalyzer(TicketAnalyzer):
    """OpenRouter-based ticket analyzer using LLMs."""

    def __init__(
        self,
        api_key: str = settings.OPENROUTER_API_KEY,
        model: str | None = None
    ):
        self.api_key = api_key
        self.model = model or settings.OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def analyze_ticket(
        self,
        ticket_content: str,
        available_topics: List[str] | None = None,
        training_rules: List[str] | None = None
    ) -> TicketAnalysisResult:
        """
        Analyze ticket using OpenRouter LLM.

        Performs both sentiment analysis and topic classification in a single call.
        """
        prompt = self._build_analysis_prompt(ticket_content, available_topics, training_rules)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert at analyzing customer support tickets."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0
            )
            response.raise_for_status()

            result = response.json()

            # Debug logging (can be removed in production)
            if not result.get("choices"):
                raise ValueError(f"No choices in response: {result}")

            content = result["choices"][0]["message"]["content"]

            # Debug logging
            if not content or not content.strip():
                raise ValueError(f"Empty content in response. Full response: {result}")

            # Strip markdown code blocks if present (some models wrap JSON in ```json...```)
            content = content.strip()
            if content.startswith("```"):
                # Remove opening ```json or ```
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines).strip()

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse LLM response as JSON. Content was: '{content[:200]}...'. Error: {e}") from e

            return self._parse_analysis_result(parsed)

    def _build_analysis_prompt(
        self,
        ticket_content: str,
        available_topics: List[str] | None,
        training_rules: List[str] | None
    ) -> str:
        """Build the prompt for ticket analysis."""
        prompt = f"""Analyze this customer support ticket for sentiment and topics.

Ticket Content:
{ticket_content}

Tasks:
1. Determine the sentiment (very_negative, negative, neutral, positive, very_positive)
2. Provide a confidence score (0.0 to 1.0) for the sentiment
3. Briefly explain your sentiment reasoning
"""

        if available_topics:
            prompt += f"""
4. Classify the ticket into one or more of these topics:
{', '.join(available_topics)}
5. For each topic, provide a confidence score (0.0 to 1.0)
"""

            if training_rules:
                prompt += f"""
User Training Rules (apply these when classifying):
{chr(10).join(f'- {rule}' for rule in training_rules)}
"""
        else:
            prompt += """
4. Suggest 2-3 topic categories for this ticket
5. For each suggested topic, provide a confidence score (0.0 to 1.0)
"""

        prompt += """
Return your analysis as JSON with this structure:
{
  "sentiment": {
    "score": "negative",
    "confidence": 0.85,
    "reasoning": "Customer expresses frustration..."
  },
  "topics": [
    {"name": "Performance Issues", "confidence": 0.9},
    {"name": "API Errors", "confidence": 0.7}
  ]
}
"""
        return prompt

    def _parse_analysis_result(self, parsed: dict) -> TicketAnalysisResult:
        """Parse the LLM response into structured result."""
        # Validate required fields
        if "sentiment" not in parsed:
            raise ValueError("Missing required field 'sentiment' in LLM response")
        if "topics" not in parsed:
            raise ValueError("Missing required field 'topics' in LLM response")

        sentiment_data = parsed.get("sentiment", {})
        topics_data = parsed.get("topics", [])

        sentiment = SentimentAnalysisResult(
            sentiment=SentimentScore(sentiment_data.get("score", "neutral")),
            confidence=sentiment_data.get("confidence", 0.5),
            reasoning=sentiment_data.get("reasoning")
        )

        topics = [
            TopicClassification(
                topic_name=topic["name"],
                confidence=topic["confidence"]
            )
            for topic in topics_data
        ]

        return TicketAnalysisResult(sentiment=sentiment, topics=topics)

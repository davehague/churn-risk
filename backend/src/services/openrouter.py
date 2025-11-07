import httpx
import json
from typing import List
from src.services.ai_base import TicketAnalyzer
from src.schemas.ai import SentimentAnalysisResult, TopicClassification, TicketAnalysisResult
from src.models.ticket import SentimentScore
from src.core.config import settings


class OpenRouterAnalyzer(TicketAnalyzer):
    """OpenRouter-based ticket analyzer using LLMs."""

    def __init__(
        self,
        api_key: str = settings.OPENROUTER_API_KEY,
        model: str = "openai/gpt-4o-mini"
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

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
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)

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

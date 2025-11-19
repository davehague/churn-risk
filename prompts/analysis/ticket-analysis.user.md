---
name: "ticket-analysis-user"
version: "1.0.0"
description: "User prompt for analyzing ticket sentiment and topics"
# model: Optional - defaults to OPENROUTER_MODEL from .env (currently google/gemini-2.5-flash)
temperature: 0.7
max_tokens: 2000

variables:
  - name: ticket_content
    type: string
    required: true
    description: "The full content of the support ticket to analyze"
  - name: has_topics
    type: boolean
    required: true
    description: "Whether available_topics is provided"
  - name: topics_section
    type: string
    required: false
    description: "Section describing topic classification (conditional)"
  - name: training_rules_section
    type: string
    required: false
    description: "Section with user-defined training rules (conditional)"
  - name: json_schema
    type: string
    required: true
    description: "The JSON schema for the response format"
---

# Ticket Sentiment and Topic Analysis

Analyze this customer support ticket for sentiment and topics.

Ticket Content:
{{ticket_content}}

Tasks:
1. Determine the sentiment (very_negative, negative, neutral, positive, very_positive)
2. Provide a confidence score (0.0 to 1.0) for the sentiment
3. Briefly explain your sentiment reasoning
{{topics_section}}{{training_rules_section}}

Return your analysis as JSON with this structure:
{{json_schema}}

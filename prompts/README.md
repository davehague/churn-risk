# Prompts as Code

This directory contains all LLM prompts used in the Churn Risk App, following the **Prompts-as-Code** pattern.

## Overview

Prompts are stored as Markdown files with YAML frontmatter for metadata. This approach provides:

- **Version control**: Track prompt changes with Git
- **Readable diffs**: See exactly what changed in code reviews
- **Self-documentation**: Metadata and variable definitions in each file
- **Language-agnostic**: Same format works in Python and TypeScript
- **Separation of concerns**: Logic in code, content in prompts

## Directory Structure

```
prompts/
├── analysis/
│   ├── ticket-analysis.system.md      # System message for ticket analysis
│   ├── ticket-analysis.user.md        # User prompt for sentiment + topic analysis
│   └── ticket-escalation.user.md      # Advanced escalation classifier (future use)
└── README.md
```

## Prompt File Format

Each prompt file follows this structure:

```markdown
---
name: "unique-prompt-name"
version: "1.0.0"
description: "What this prompt does"
model: "google/gemini-2.5-flash"
temperature: 0.7
max_tokens: 2000

variables:
  - name: "variable_name"
    type: "string"
    required: true
    description: "What this variable is for"
---

# Prompt Title

Your prompt content here. Use {{variable_name}} for substitution.
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier for this prompt |
| `version` | Yes | Semantic version (MAJOR.MINOR.PATCH) |
| `description` | Yes | What this prompt does |
| `model` | No | Default model (can be overridden at runtime) |
| `temperature` | No | Default temperature (0.0-2.0) |
| `max_tokens` | No | Default max tokens |
| `variables` | Yes | List of variable definitions |

### Variable Definition

Each variable must specify:

- `name`: Exact match for `{{variable_name}}` in content
- `type`: `string`, `number`, `boolean`, `array`, `object`
- `required`: `true` or `false`
- `description`: Human-readable explanation
- `default`: (optional) Default value if not provided

## Usage

### In Python (Backend)

```python
from src.prompt_engine import PromptLoader, PromptCompiler

# Load a prompt
loader = PromptLoader()
prompt_data = loader.load('analysis/ticket-analysis.user')

# Compile with variables
compiler = PromptCompiler()
compiled = compiler.compile(
    template=prompt_data['content'],
    variables={
        'ticket_content': 'Customer is frustrated...',
        'topics_section': '...',
        'json_schema': '...'
    },
    definitions=prompt_data['variables']
)

# Use in LLM call
response = await llm_api.call(
    messages=[{'role': 'user', 'content': compiled}],
    model=prompt_data['metadata'].get('model', 'gpt-4o-mini')
)
```

### Handling Logic

**Keep logic in code, not templates.** Templates only do simple `{{variable}}` substitution.

```python
# ✅ CORRECT: Handle conditionals in code
if available_topics:
    topics_section = f"Topics: {', '.join(available_topics)}"
else:
    topics_section = "Suggest 2-3 topics"

variables = {'topics_section': topics_section}
```

```markdown
<!-- ❌ WRONG: Don't try to add logic to templates -->
{% if has_topics %}Topics: {{topics}}{% endif %}
```

## Development Workflow

### Creating a New Prompt

```bash
cd backend
python scripts/create_prompt.py analysis/new-prompt
```

This scaffolds a new prompt file with the correct structure.

### Validating Prompts

Before committing changes, validate all prompts:

```bash
cd backend
python scripts/validate_prompts.py
```

This checks:
- Valid YAML frontmatter
- Required metadata fields present
- Proper variable definitions
- Semantic versioning format

### Versioning

Follow semantic versioning for prompts:

- **MAJOR**: Breaking changes to variables or output format
- **MINOR**: New features, additional variables (backward compatible)
- **PATCH**: Bug fixes, wording improvements

Example:
- `1.0.0` → Initial version
- `1.1.0` → Added optional `context` variable
- `2.0.0` → Changed `topics` from string to array (breaking)

## Current Prompts

### Ticket Analysis (`analysis/ticket-analysis.*`)

**System prompt** (`ticket-analysis.system.md`):
- Simple system message defining the AI's role
- No variables

**User prompt** (`ticket-analysis.user.md`):
- Analyzes ticket content for sentiment and topics
- Returns structured JSON with sentiment scores and topic classifications
- Variables:
  - `ticket_content`: The support ticket text
  - `topics_section`: Conditional section for topic classification
  - `training_rules_section`: Optional user training rules
  - `json_schema`: Expected JSON response format

### Ticket Escalation (`analysis/ticket-escalation.user.md`)

**Status**: Available but not yet integrated

A sophisticated escalation classifier that:
- Detects negative sentiment across multiple dimensions
- Uses a 3-stage decision framework
- Provides detailed reasoning and confidence scores
- Handles edge cases (sarcasm, professional dissatisfaction, etc.)

To integrate this prompt, update `OpenRouterAnalyzer` to use it instead of the simpler sentiment analysis.

## Best Practices

1. **Document your prompts**: Use clear descriptions and variable definitions
2. **Version carefully**: Increment versions when making changes
3. **Test changes**: Run existing tests after modifying prompts
4. **Validate before committing**: Always run `validate_prompts.py`
5. **Keep it simple**: Don't add templating logic - handle that in code
6. **Review diffs**: Prompt changes are code changes - review them carefully

## CI/CD Integration

Consider adding prompt validation to your CI/CD pipeline:

```yaml
# .github/workflows/validate-prompts.yml
name: Validate Prompts

on:
  pull_request:
    paths:
      - 'prompts/**/*.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd backend && poetry install
      - run: cd backend && python scripts/validate_prompts.py
```

## Migration Notes

**Previous approach**: Prompts were hardcoded in `src/services/openrouter.py:_build_analysis_prompt()`

**New approach**: Prompts are in version-controlled Markdown files with metadata

**Benefits**:
- Non-developers can review and suggest prompt improvements
- Clear history of what changed and why
- Easy A/B testing of different prompt versions
- Reusable across Python and TypeScript codebases

## Questions?

See the [Prompts as Code SOP](https://github.com/anthropics/prompts-as-code) for more details on this pattern.

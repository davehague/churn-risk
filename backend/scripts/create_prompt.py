#!/usr/bin/env python3
"""
Scaffold a new prompt file with YAML frontmatter template.

Usage:
    python scripts/create_prompt.py analysis/new-prompt
    python scripts/create_prompt.py chat/greeting.system
"""

import sys
from pathlib import Path

# Template for new prompt files
TEMPLATE = """---
name: "{name}"
version: "1.0.0"
description: "TODO: Describe what this prompt does"
model: "google/gemini-2.5-flash"
temperature: 0.7
max_tokens: 2000

variables:
  - name: "example_var"
    type: "string"
    required: true
    description: "TODO: Describe this variable"
---

# {title}

TODO: Write your prompt here. Use {{{{example_var}}}} for variable substitution.
"""


def create_prompt(prompt_path: str):
    """
    Create a new prompt file from template.

    Args:
        prompt_path: Path relative to prompts/ directory (e.g., 'analysis/new-prompt')
    """
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    prompts_dir = project_root / 'prompts'

    # Add .md extension if not present
    if not prompt_path.endswith('.md'):
        prompt_path = f"{prompt_path}.md"

    full_path = prompts_dir / prompt_path

    # Check if file already exists
    if full_path.exists():
        print(f"❌ File already exists: {full_path}")
        sys.exit(1)

    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate name and title from filename
    name = full_path.stem
    title = name.replace('-', ' ').replace('_', ' ').title()

    # Write template to file
    content = TEMPLATE.format(name=name, title=title)
    full_path.write_text(content)

    print(f"✅ Created: {full_path.relative_to(project_root)}")
    print()
    print("Next steps:")
    print("1. Edit the frontmatter metadata")
    print("2. Define your variables")
    print("3. Write your prompt content")
    print("4. Validate with: python scripts/validate_prompts.py")


def main():
    """Entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/create_prompt.py <prompt-path>")
        print()
        print("Examples:")
        print("  python scripts/create_prompt.py analysis/new-analysis")
        print("  python scripts/create_prompt.py chat/greeting.system")
        sys.exit(1)

    prompt_path = sys.argv[1]
    create_prompt(prompt_path)


if __name__ == '__main__':
    main()

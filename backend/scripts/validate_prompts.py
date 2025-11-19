#!/usr/bin/env python3
"""
Validate all prompt files in the prompts directory.

This script checks:
1. Valid YAML frontmatter
2. Required metadata fields present
3. Valid variable definitions
4. Proper Markdown structure

Exit code: 0 if all prompts valid, 1 if any errors found
"""

import sys
from pathlib import Path

# Add project root to path so we can import the prompt engine
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'backend'))

from src.prompt_engine import PromptLoader

REQUIRED_FIELDS = ['name', 'version', 'description', 'variables']


def validate_prompt(prompt_path: Path, loader: PromptLoader) -> list[str]:
    """
    Validate a single prompt file.

    Args:
        prompt_path: Path to the prompt file
        loader: PromptLoader instance

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    relative_path = prompt_path.relative_to(project_root / 'prompts')

    try:
        # Try to load the prompt
        prompt_data = loader.load(str(relative_path))

        # Check required metadata fields
        metadata = prompt_data['metadata']
        for field in REQUIRED_FIELDS:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")

        # Validate variable definitions
        variables = prompt_data.get('variables', [])
        for i, var_def in enumerate(variables):
            if 'name' not in var_def:
                errors.append(f"Variable {i} missing 'name' field")
            if 'type' not in var_def:
                errors.append(f"Variable {i} ('{var_def.get('name', '?')}') missing 'type' field")
            if 'required' not in var_def:
                errors.append(f"Variable {i} ('{var_def.get('name', '?')}') missing 'required' field")
            if 'description' not in var_def:
                errors.append(f"Variable {i} ('{var_def.get('name', '?')}') missing 'description' field")

        # Validate version format (semantic versioning)
        version = metadata.get('version', '')
        if version:
            parts = version.split('.')
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                errors.append(f"Invalid version format: {version} (should be MAJOR.MINOR.PATCH)")

    except FileNotFoundError as e:
        errors.append(f"File not found: {e}")
    except ValueError as e:
        errors.append(f"Parse error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error: {type(e).__name__}: {e}")

    return errors


def main():
    """Validate all prompt files."""
    prompts_dir = project_root / 'prompts'
    loader = PromptLoader(str(prompts_dir))

    print(f"Validating prompts in {prompts_dir}...")
    print()

    all_errors = []
    total_prompts = 0

    # Find all .md files in prompts directory
    for prompt_file in prompts_dir.rglob('*.md'):
        total_prompts += 1
        errors = validate_prompt(prompt_file, loader)

        if errors:
            print(f"✗ {prompt_file.relative_to(prompts_dir)}")
            for error in errors:
                print(f"  - {error}")
            all_errors.extend(errors)
        else:
            print(f"✓ {prompt_file.relative_to(prompts_dir)}")

    print()
    print(f"Validated {total_prompts} prompt(s)")

    if all_errors:
        print(f"❌ Found {len(all_errors)} error(s)")
        sys.exit(1)
    else:
        print("✅ All prompts valid")
        sys.exit(0)


if __name__ == '__main__':
    main()

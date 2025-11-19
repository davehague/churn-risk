"""
Prompt Compiler - Compiles prompts by substituting variables.
"""

import re
from typing import Any, Dict, List


class PromptCompiler:
    """Compiles prompts by replacing {{variables}} with values."""

    @staticmethod
    def compile(
        template: str,
        variables: Dict[str, Any],
        definitions: List[Dict[str, Any]]
    ) -> str:
        """
        Replace {{variables}} with values.

        Args:
            template: The prompt template with {{variable}} placeholders
            variables: Dictionary mapping variable names to values
            definitions: List of variable definitions from frontmatter

        Returns:
            Compiled prompt string with variables replaced

        Raises:
            ValueError: If a required variable is missing
        """
        # Check required variables
        for var_def in definitions:
            if var_def.get('required') and var_def['name'] not in variables:
                raise ValueError(f"Missing required variable: {var_def['name']}")

        # Apply defaults
        for var_def in definitions:
            if var_def['name'] not in variables and 'default' in var_def:
                variables[var_def['name']] = var_def['default']

        # Replace variables
        result = template
        for name, value in variables.items():
            # Match {{variable_name}} with optional whitespace
            pattern = r'\{\{\s*' + re.escape(name) + r'\s*\}\}'
            # Convert value to string, handle None as empty string
            replacement = str(value) if value is not None else ''
            result = re.sub(pattern, replacement, result)

        return result

    @staticmethod
    def validate_variables(
        variables: Dict[str, Any],
        definitions: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Validate variables against their definitions.

        Args:
            variables: Dictionary mapping variable names to values
            definitions: List of variable definitions from frontmatter

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        for var_def in definitions:
            name = var_def['name']
            required = var_def.get('required', False)
            var_type = var_def.get('type', 'string')

            # Check if required variable is missing
            if required and name not in variables:
                errors.append(f"Missing required variable: {name}")
                continue

            # Skip type checking if variable not provided and not required
            if name not in variables:
                continue

            value = variables[name]

            # Type validation (basic)
            if var_type == 'string' and not isinstance(value, str):
                errors.append(f"Variable '{name}' should be string, got {type(value).__name__}")
            elif var_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Variable '{name}' should be number, got {type(value).__name__}")
            elif var_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Variable '{name}' should be boolean, got {type(value).__name__}")
            elif var_type == 'array' and not isinstance(value, list):
                errors.append(f"Variable '{name}' should be array, got {type(value).__name__}")
            elif var_type == 'object' and not isinstance(value, dict):
                errors.append(f"Variable '{name}' should be object, got {type(value).__name__}")

        return errors

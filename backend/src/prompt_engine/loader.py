"""
Prompt Loader - Loads prompts from Markdown files with YAML frontmatter.
"""

import re
from pathlib import Path
from typing import Any, Dict, List
import yaml


class PromptLoader:
    """Loads prompts from Markdown files with YAML frontmatter."""

    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the prompt loader.

        Args:
            prompts_dir: Path to the prompts directory (relative to project root)
        """
        self.prompts_dir = Path(prompts_dir)

    def load(self, prompt_path: str) -> Dict[str, Any]:
        """
        Load a prompt file.

        Args:
            prompt_path: Path to prompt file relative to prompts_dir
                        (e.g., 'analysis/ticket-analysis.user')
                        The .md extension is optional.

        Returns:
            Dictionary with:
            - metadata: Dict of frontmatter fields
            - content: Markdown content (without frontmatter)
            - variables: List of variable definitions from frontmatter

        Raises:
            FileNotFoundError: If prompt file doesn't exist
            ValueError: If frontmatter is missing or invalid
        """
        if not prompt_path.endswith('.md'):
            prompt_path = f"{prompt_path}.md"

        full_path = self.prompts_dir / prompt_path

        if not full_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {full_path}")

        content = full_path.read_text()

        # Parse frontmatter using regex
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        if not match:
            raise ValueError(f"No frontmatter found in {prompt_path}")

        frontmatter = match.group(1)
        markdown = match.group(2).strip()

        # Parse YAML frontmatter
        try:
            metadata = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in frontmatter of {prompt_path}: {e}") from e

        return {
            'metadata': metadata,
            'content': markdown,
            'variables': metadata.get('variables', [])
        }

    def list_prompts(self, pattern: str = "**/*.md") -> List[Path]:
        """
        List all prompt files matching a pattern.

        Args:
            pattern: Glob pattern (default: all .md files)

        Returns:
            List of Path objects for matching prompt files
        """
        return list(self.prompts_dir.glob(pattern))

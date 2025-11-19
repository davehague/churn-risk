"""
Prompt Engine for managing LLM prompts as code.

This module provides a lightweight system for loading and compiling prompts
stored as Markdown files with YAML frontmatter.
"""

from .loader import PromptLoader
from .compiler import PromptCompiler

__all__ = ["PromptLoader", "PromptCompiler"]

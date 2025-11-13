"""Shared filesystem paths for the Scout AI PoC."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "base_prompt.txt"

__all__ = ["PROJECT_ROOT", "DEFAULT_PROMPT_PATH"]

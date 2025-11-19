"""Argument parsing for the scout-ai-poc CLI."""
from __future__ import annotations

import argparse
import os
from typing import List


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scout-ai-poc",
        description="LangChain-powered vulnerability triage for Rust smart contracts.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Root directory where contract files live (default: current directory).",
    )
    parser.add_argument(
        "--config",
        "-c",
        help=(
            "Path to a directory or file used to locate the canonical '.scout' "
            "(default: search within the target directory)."
        ),
    )
    parser.add_argument(
        "--extraPrompt",
        dest="extra_prompt",
        help="Optional JSON/text file with additional instructions for the LLM.",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic"],
        default=os.getenv("SCOUT_AI_PROVIDER", "openai"),
        help="AI provider to use (default: SCOUT_AI_PROVIDER or openai).",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("SCOUT_AI_MODEL", "gpt-5"),
        help="Model name passed to LangChain (default: SCOUT_AI_MODEL or gpt-5 for openai, claude-sonnet-4-5-20250929 for anthropic).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip the LLM call and only print the composed prompt.",
    )
    return parser.parse_args(argv)


__all__ = ["parse_args"]

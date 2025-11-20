"""Argument parsing for the scout-ai-poc CLI."""
from __future__ import annotations

import argparse
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
        "--model",
        default=None,
        help="Override the model defined in the '.scout' config for this run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip the LLM call and only print the composed prompt.",
    )
    parser.add_argument(
        "--include-deps",
        action="store_true",
        help="Scan listed files for local module dependencies and include them.",
    )
    parser.add_argument(
        "--dependency-depth",
        type=int,
        default=1,
        help=(
            "Maximum dependency depth when --include-deps is active (default: 1). "
            "Ignored unless --include-deps is provided."
        ),
    )
    return parser.parse_args(argv)


__all__ = ["parse_args"]

from __future__ import annotations

import argparse
from typing import List

from .llm_modes import LLM_MODES


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
            "Path to a directory or file used to locate the canonical 'scout.json' "
            "(default: search within the target directory)."
        ),
    )
    parser.add_argument(
        "--extra-prompt",
        dest="extra_prompt",
        help=("Optional .txt file with additional instructions for the LLM."),
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the model defined in the 'scout.json' config for this run.",
    )
    parser.add_argument(
        "--llm-mode",
        choices=LLM_MODES,
        type=str.lower,
        default=None,
        help=(
            "LLM configuration mode (consistent or creative). Overrides the "
            "'mode' in scout.json when provided."
        ),
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

"""Entry point for the scout-ai-poc CLI."""
from __future__ import annotations

import logging
import os
import sys
from typing import List

from dotenv import load_dotenv

from .cli import parse_args
from .runner import run_analysis

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging() -> None:
    """Configure a simple stdout logger honoring SCOUT_LOG_LEVEL."""
    level_name = os.getenv("SCOUT_LOG_LEVEL", "INFO").upper()
    if not hasattr(logging, level_name):
        level = logging.INFO
        logging.basicConfig(level=level, format=LOG_FORMAT)
        logging.getLogger(__name__).warning(
            "Unknown SCOUT_LOG_LEVEL '%s'; defaulting to INFO.", level_name
        )
        return

    level = getattr(logging, level_name)
    logging.basicConfig(level=level, format=LOG_FORMAT)


def load_environment() -> None:
    """Pull variables from a local .env if present."""
    load_dotenv()


def main(argv: List[str] | None = None) -> int:
    load_environment()
    configure_logging()
    args = parse_args(argv)
    return run_analysis(args)


if __name__ == "__main__":
    sys.exit(main())

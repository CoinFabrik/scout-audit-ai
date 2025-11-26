from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")

    logger.info("Loading config from %s", path)
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON inside {path}: {exc}") from exc

    contract_type = data.get("contract_type")
    files = data.get("files", [])
    model = data.get("model")

    if not contract_type:
        raise ValueError("config file must include 'contract_type'")
    if not isinstance(files, Iterable) or isinstance(files, (str, bytes)):
        raise ValueError("'files' must be a list of paths")
    if model is not None and not isinstance(model, str):
        raise ValueError("'model' must be a string when provided")

    normalized_files = [str(item) for item in files]

    return {
        "contract_type": contract_type,
        "files": normalized_files,
        "model": model,
    }


def read_prompt_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    logger.info("Reading base prompt from %s", path)
    return path.read_text()


def load_extra_inputs(path: Path | None) -> str:
    if path is None:
        logger.info("No extra prompt file provided.")
        return "None provided."
    if not path.exists():
        raise FileNotFoundError(f"Extra prompt file not found: {path}")

    logger.info("Loading extra prompt from %s", path)
    raw = path.read_text().strip()
    if not raw:
        logger.warning("Extra prompt file %s is empty.", path)
        return "Extra prompt file is empty."

    if path.suffix.lower() == ".json":
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse %s as JSON; returning raw contents.", path)
            return raw
        return json.dumps(parsed, indent=2)

    return raw


def build_files_context(file_paths: List[str], root: Path) -> str:
    if not file_paths:
        return "No files listed in config."

    logger.info("Building files context for %d files.", len(file_paths))
    chunks: List[str] = []
    for relative in file_paths:
        resolved = (root / relative).resolve()
        if not resolved.exists():
            logger.warning("File listed in config not found: %s", relative)
            chunks.append(f"// File not found: {relative}")
            continue

        try:
            content = resolved.read_text()
        except UnicodeDecodeError:
            # TODO: maybe throw an error here?
            logger.warning("Unable to decode file as UTF-8: %s", relative)
            chunks.append(f"// Unable to decode file as UTF-8: {relative}")
            continue

        try:
            rel_display = resolved.relative_to(root)
        except ValueError:
            rel_display = resolved
        chunks.append(f"// File: {rel_display}\n{content.strip()}\n")

    return "\n\n".join(chunks)


__all__ = [
    "load_config",
    "read_prompt_file",
    "load_extra_inputs",
    "build_files_context",
]

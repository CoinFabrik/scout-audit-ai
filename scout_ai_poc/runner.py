"""High-level orchestration for scout-ai-poc."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Iterable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

from .data_loader import (
    build_files_context,
    load_config,
    load_extra_inputs,
    read_prompt_file,
)
from .paths import DEFAULT_PROMPT_PATH
from .vulnerability_catalog import get_vulnerabilities

CONFIG_FILENAME = ".scout"
logger = logging.getLogger(__name__)


def should_execute_llm(explicit_dry_run: bool) -> bool:
    if explicit_dry_run:
        logger.info("Dry-run flag active; LLM execution disabled.")
        return False
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if not has_key:
        logger.warning("OPENAI_API_KEY not set; defaulting to dry-run output.")
    return has_key


def build_prompt(prompt_text: str) -> ChatPromptTemplate:
    """Return a chat prompt that keeps system rules separate from file context."""
    return ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(prompt_text),
            HumanMessagePromptTemplate.from_template(
                """Analyze the following files and report exploitable vulnerabilities only:\n{files_context}"""
            ),
        ]
    )


def create_chain(prompt: ChatPromptTemplate, model_name: str) -> RunnableSequence:
    logger.info("Creating LangChain pipeline with model '%s'.", model_name)
    llm = ChatOpenAI(
        model=model_name,
        temperature=1,
        model_kwargs={"reasoning_effort": "high"},
    )
    return prompt | llm | StrOutputParser()


def format_known_vulnerabilities(vulnerabilities: Iterable[str]) -> str:
    """Present catalog entries as a numbered list with a graceful empty fallback."""
    entries = [entry.strip() for entry in vulnerabilities if entry and entry.strip()]
    if not entries:
        return "\n- None documented."
    return "\n" + "\n".join(
        f"    {idx}. {entry}" for idx, entry in enumerate(entries, 1)
    )


def assemble_chain_inputs(
    contract_type: str,
    file_paths: Iterable[str],
    target_root: Path,
    extra_prompt_path: Path | None,
) -> Dict[str, str]:
    file_list = list(file_paths)
    files_context = build_files_context(file_list, target_root)
    vulnerabilities = get_vulnerabilities(contract_type)
    extra_inputs = load_extra_inputs(extra_prompt_path)
    logger.info(
        "Prepared chain inputs for contract_type='%s' (%d files, extra prompt: %s).",
        contract_type,
        len(file_list),
        "yes" if extra_prompt_path else "no",
    )

    return {
        "contract_type": contract_type,
        "known_vulnerabilities": format_known_vulnerabilities(vulnerabilities),
        "files_context": files_context,
        "extra_inputs": extra_inputs,
    }


def resolve_config_path(target_root: Path, config_override: str | None) -> Path:
    """Locate the canonical .scout file."""
    search_root = Path(config_override).expanduser() if config_override else target_root
    search_root = search_root.resolve()
    logger.debug(
        "Resolving config path. target_root=%s override=%s",
        target_root,
        config_override,
    )

    if search_root.is_file() and search_root.name != CONFIG_FILENAME:
        raise ValueError(
            f"Config file must be named '{CONFIG_FILENAME}', got {search_root.name!r}"
        )

    candidate = (
        search_root
        if search_root.name == CONFIG_FILENAME
        else search_root / CONFIG_FILENAME
    )

    if candidate.name != CONFIG_FILENAME:
        raise ValueError(
            f"Config path must resolve to '{CONFIG_FILENAME}', got {candidate.name!r}"
        )

    if not candidate.exists():
        raise FileNotFoundError(
            f"No '{CONFIG_FILENAME}' file found under {search_root}."
        )

    logger.info("Using config file at %s", candidate)
    return candidate


def run_analysis(args) -> int:
    target_root = Path(args.target).resolve()
    logger.info(
        "Starting analysis run. target=%s dry_run=%s", target_root, args.dry_run
    )
    config_path = resolve_config_path(target_root, args.config)
    config = load_config(config_path)
    prompt_text = read_prompt_file(DEFAULT_PROMPT_PATH)

    extra_prompt_path = Path(args.extra_prompt) if args.extra_prompt else None
    chain_inputs = assemble_chain_inputs(
        config["contract_type"],
        config["files"],
        target_root,
        extra_prompt_path,
    )
    prompt = build_prompt(prompt_text)

    if not should_execute_llm(args.dry_run):
        logger.info("Rendering composed prompt without executing the LLM.")
        print(
            "[DRY-RUN] Displaying composed prompt. Provide OPENAI_API_KEY to execute.\n"
        )
        messages = prompt.format_messages(**chain_inputs)
        for message in messages:
            role = message.type.upper()
            print(f"[{role}]\n{message.content}\n")
        return 0

    try:
        chain = create_chain(prompt, args.model)
        result = chain.invoke(chain_inputs)
    except Exception as exc:
        logger.exception("Failed to execute LangChain pipeline.")
        print(f"Failed to execute LangChain pipeline: {exc}", file=sys.stderr)
        return 1

    output_text = result.get("text") if isinstance(result, dict) else result
    logger.info("LLM execution completed successfully.")
    print(output_text)
    return 0


__all__ = ["run_analysis"]

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


from .data_loader import (
    build_files_context,
    load_config,
    load_extra_inputs,
    read_prompt_file,
)
from .dependency_analyzer import include_dependencies
from .paths import DEFAULT_PROMPT_PATH
from .providers import infer_provider
from .vulnerability_catalog import get_vulnerabilities

CONFIG_FILENAME = ".scout"
logger = logging.getLogger(__name__)


def get_api_key() -> str | None:
    api_key = os.getenv("API_KEY")
    if api_key:
        return api_key.strip() or None
    return None


def should_execute_llm(explicit_dry_run: bool, api_key: str | None) -> bool:
    if explicit_dry_run:
        logger.info("Dry-run flag active; LLM execution disabled.")
        return False
    if not api_key:
        logger.warning("API_KEY not set; defaulting to dry-run output.")
        return False
    return True


def build_prompt(prompt_text: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(prompt_text),
            HumanMessagePromptTemplate.from_template(
                """Analyze the following files and report exploitable vulnerabilities only:\n{files_context}"""
            ),
        ]
    )


def format_known_vulnerabilities(vulnerabilities: Iterable[str]) -> str:
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

    model_name = args.model or config.get("model")
    if not model_name:
        logger.error(
            "No model specified. Provide --model or add a 'model' field to %s.",
            config_path,
        )
        return 1

    model_source = "CLI flag" if args.model else ".scout config"
    logger.info("Using model '%s' from %s.", model_name, model_source)
    try:
        provider, provider_config = infer_provider(model_name)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1
    logger.info("Inferred provider '%s' for model '%s'.", provider.name, model_name)

    extra_prompt_path = Path(args.extra_prompt) if args.extra_prompt else None
    file_list = config["files"]
    if args.include_deps:
        if args.dependency_depth < 1:
            logger.error("--dependency-depth must be >= 1 when using --include-deps.")
            return 1
        file_list = include_dependencies(file_list, target_root, args.dependency_depth)
    elif args.dependency_depth != 1:
        logger.warning(
            "--dependency-depth is ignored unless --include-deps is provided."
        )

    chain_inputs = assemble_chain_inputs(
        config["contract_type"],
        file_list,
        target_root,
        extra_prompt_path,
    )
    prompt = build_prompt(prompt_text)

    api_key = get_api_key()
    if not should_execute_llm(args.dry_run, api_key):
        logger.info("Rendering composed prompt without executing the LLM.")
        print(
            "[DRY-RUN] Displaying composed prompt. Provide API_KEY in your "
            "environment (or .env) to execute.\n"
        )
        messages = prompt.format_messages(**chain_inputs)
        for message in messages:
            role = message.type.upper()
            print(f"[{role}]\n{message.content}\n")
        return 0

    try:
        logger.info(
            "Creating LangChain pipeline with provider '%s' and model '%s'.",
            provider.name,
            model_name,
        )
        llm = provider.builder(model_name, api_key, provider_config)
        chain = prompt | llm | StrOutputParser()
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
